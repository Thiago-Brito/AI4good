import {NativeModule, requireNativeModule} from 'expo-modules-core';
import * as DocumentPicker from 'expo-document-picker';
import {File} from 'expo-file-system';
import {DOCUMENT_MIMES, extractBytes, makeDocument, validateDocument, type DocumentFile, type DocumentPart, type DocumentText} from '../pipeline/documents';
import {checkCancelled} from '../pipeline/types';
declare class DocumentsModule extends NativeModule<{onDocument: () => void}> {
  importDocument(uri: string, name: string, mime: string): Promise<DocumentFile>;
  takePendingDocument(): Promise<DocumentFile | null>;
  deleteDocument(uri: string): Promise<void>;
  extractPdf(uri: string): Promise<{pages: number; parts: DocumentPart[]}>;
}
const native = requireNativeModule<DocumentsModule>('SlideDocuments');
export function onIncomingDocument(listener: () => void) {return native.addListener('onDocument', listener);}
export const pendingDocument = () => native.takePendingDocument();
export const deleteDocument = (file: DocumentFile) => native.deleteDocument(file.uri);
export async function pickDocument(): Promise<DocumentFile | null> {
  // A cópia nativa limita também provedores que omitem/mentem sobre o tamanho.
  const result = await DocumentPicker.getDocumentAsync({type: DOCUMENT_MIMES, multiple: false, copyToCacheDirectory: false});
  if (result.canceled) return null;
  const file = result.assets[0];
  if (file.size !== undefined) validateDocument({uri: file.uri, name: file.name, bytes: file.size, mime: file.mimeType ?? ''});
  return native.importDocument(file.uri, file.name, file.mimeType ?? '');
}
export async function readDocument(file: DocumentFile, signal?: AbortSignal): Promise<DocumentText> {
  checkCancelled(signal);
  const kind = validateDocument(file);
  if (kind === 'pdf') {
    let extracted: {pages: number; parts: DocumentPart[]};
    try {extracted = await native.extractPdf(file.uri);}
    catch (e) {
      checkCancelled(signal);
      const message = e instanceof Error ? e.message : String(e);
      if (/PDF sem texto selecionável|200 mil caracteres|10 MB|protegido contra extração/.test(message)) throw Error(message);
      throw Error('Não foi possível ler o PDF. Ele pode estar corrompido ou protegido por senha.');
    }
    checkCancelled(signal);
    return makeDocument(file, extracted.parts, 'PDFBox', extracted.pages);
  }
  const bytes = await new File(file.uri).bytes();
  checkCancelled(signal);
  const document = await extractBytes(file, bytes);
  checkCancelled(signal);
  return document;
}
