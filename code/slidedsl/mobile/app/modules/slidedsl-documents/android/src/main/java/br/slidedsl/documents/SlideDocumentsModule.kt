package br.slidedsl.documents

import android.content.Intent
import android.net.Uri
import android.provider.OpenableColumns
import com.tom_roush.pdfbox.android.PDFBoxResourceLoader
import com.tom_roush.pdfbox.pdmodel.PDDocument
import com.tom_roush.pdfbox.text.PDFTextStripper
import expo.modules.kotlin.modules.Module
import expo.modules.kotlin.modules.ModuleDefinition
import java.io.File
import java.io.Writer
import java.util.UUID

class SlideDocumentsModule : Module() {
  private val maxBytes = 10L * 1024 * 1024
  private val maxChars = 200000
  private var pending: Intent? = null
  private var consumedInitial = false

  override fun definition() = ModuleDefinition {
    Name("SlideDocuments")
    Events("onDocument")
    OnNewIntent { intent ->
      if (isDocumentIntent(intent)) {
        synchronized(this@SlideDocumentsModule) { pending = intent }
        sendEvent("onDocument", emptyMap<String, Any>())
      }
    }
    AsyncFunction("takePendingDocument") {
      val intent = synchronized(this@SlideDocumentsModule) {
        val current = pending
        pending = null
        if (current != null) { consumedInitial = true; current }
        else if (!consumedInitial) {
          val initial = appContext.currentActivity?.intent
          if (initial != null) consumedInitial = true
          initial
        }
        else null
      }
      if (intent != null && isDocumentIntent(intent)) {
        @Suppress("DEPRECATION")
        val uri = if (intent.action == Intent.ACTION_SEND) intent.getParcelableExtra<Uri>(Intent.EXTRA_STREAM)
          ?: intent.clipData?.takeIf { it.itemCount > 0 }?.getItemAt(0)?.uri else intent.data
        if (uri == null) throw IllegalArgumentException("Compartilhe um arquivo PDF, DOCX, TXT ou MD, em vez de um link ou texto.")
        copyDocument(uri.toString(), "", intent.type ?: "")
      } else null
    }
    AsyncFunction("importDocument") { uri: String, name: String, mime: String -> copyDocument(uri, name, mime) }
    AsyncFunction("deleteDocument") { uri: String -> localFile(uri).delete(); Unit }
    AsyncFunction("extractPdf") { uri: String ->
      val context = appContext.reactContext ?: throw IllegalStateException("Contexto Android indisponível.")
      val file = localFile(uri)
      require(file.length() <= maxBytes) { "O documento deve ter no máximo 10 MB." }
      PDFBoxResourceLoader.init(context.applicationContext)
      PDDocument.load(file).use { document ->
        require(!document.isEncrypted || document.currentAccessPermission.canExtractContent()) { "PDF protegido contra extração de texto." }
        val pages = mutableListOf<Map<String, Any>>()
        var chars = 0
        for (page in 1..document.numberOfPages) {
          val buffer = StringBuilder()
          val writer = object : Writer() {
            override fun write(cbuf: CharArray, off: Int, len: Int) {
              chars += len
              require(chars <= maxChars) { "O documento excede 200 mil caracteres extraídos." }
              buffer.append(cbuf, off, len)
            }
            override fun flush() {}
            override fun close() {}
          }
          PDFTextStripper().apply { startPage = page; endPage = page; sortByPosition = true }.writeText(document, writer)
          pages.add(mapOf("page" to page, "text" to buffer.toString()))
        }
        require(pages.any { (it["text"] as String).isNotBlank() }) { "PDF sem texto selecionável" }
        mapOf("pages" to document.numberOfPages, "parts" to pages)
      }
    }
  }
  private fun isDocumentIntent(intent: Intent) = intent.action == Intent.ACTION_SEND || intent.action == Intent.ACTION_VIEW
  private fun root(): File {
    val context = appContext.reactContext ?: throw IllegalStateException("Contexto Android indisponível.")
    return File(context.cacheDir, "slidedsl-documents").apply { mkdirs() }
  }
  private fun localFile(uri: String): File {
    val parsed = Uri.parse(uri)
    require(parsed.scheme == "file") { "URI de documento local inválida." }
    val file = File(parsed.path ?: "").canonicalFile
    require(file.parentFile == root().canonicalFile) { "Documento fora do cache privado." }
    return file
  }
  private fun copyDocument(value: String, suggestedName: String, suggestedMime: String): Map<String, Any> {
    val context = appContext.reactContext ?: throw IllegalStateException("Contexto Android indisponível.")
    val uri = Uri.parse(value)
    require(uri.scheme == "content" || uri.scheme == "file") { "Escolha um arquivo local ou de um provedor de documentos." }
    var name = suggestedName
    var size = -1L
    if (uri.scheme == "content") context.contentResolver.query(uri, arrayOf(OpenableColumns.DISPLAY_NAME, OpenableColumns.SIZE), null, null, null)?.use { cursor ->
      if (cursor.moveToFirst()) {
        val ni = cursor.getColumnIndex(OpenableColumns.DISPLAY_NAME)
        val si = cursor.getColumnIndex(OpenableColumns.SIZE)
        if (ni >= 0 && !cursor.isNull(ni)) name = cursor.getString(ni)
        if (si >= 0 && !cursor.isNull(si)) size = cursor.getLong(si)
      }
    }
    if (name.isBlank()) name = uri.lastPathSegment ?: "documento"
    name = name.replace('\\', '/').substringAfterLast('/').take(180)
    val mime = context.contentResolver.getType(uri) ?: suggestedMime
    val suffix = name.substringAfterLast('.', "").lowercase()
    require(suffix in listOf("pdf", "docx", "txt", "md") || mime in listOf("application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", "text/plain", "text/markdown", "text/x-markdown")) { "Formato não suportado. Escolha PDF, DOCX, TXT ou MD." }
    require(size <= maxBytes) { "O documento deve ter no máximo 10 MB." }
    val out = File(root(), UUID.randomUUID().toString())
    try {
      val input = context.contentResolver.openInputStream(uri) ?: throw IllegalArgumentException("Não foi possível ler o documento.")
      input.use { source -> out.outputStream().use { target ->
        val buffer = ByteArray(16384); var total = 0L
        while (true) {
          val count = source.read(buffer)
          if (count < 0) break
          total += count
          require(total <= maxBytes) { "O documento deve ter no máximo 10 MB." }
          target.write(buffer, 0, count)
        }
      } }
      return mapOf("uri" to Uri.fromFile(out).toString(), "name" to name, "bytes" to out.length(), "mime" to mime)
    } catch (e: Exception) { out.delete(); throw e }
  }
}
