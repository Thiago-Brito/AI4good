# Gera o APK em D:, preservando caches, evidências e builds nativos existentes.
# Uso: powershell -File scripts\mobile_build.ps1 [-Clean] [-Debug] [-SkipPrebuild]
# SkipPrebuild: retomar Gradle após falha quando a configuração Expo não mudou.
param([switch]$Clean, [switch]$Debug, [switch]$SkipPrebuild)
$ErrorActionPreference = 'Stop'
if ($Clean -and $SkipPrebuild) { throw 'Clean e SkipPrebuild são incompatíveis.' }
# Só builds anteriores (Gradle/Kotlin) bloqueiam; Java de outras ferramentas (ex.: extensão Java do VS Code) não.
$builds = Get-CimInstance Win32_Process -Filter "Name='java.exe'" -ErrorAction SilentlyContinue |
  Where-Object { $_.CommandLine -match 'GradleDaemon|GradleWrapperMain|org\.jetbrains\.kotlin\.daemon' -and
    $_.CommandLine -notmatch '\\\.vscode\\extensions\\' }  # daemon do Gradle da extensão Java do VS Code não é nosso
if ($builds) {
  throw 'Há build Gradle/Kotlin ativo. Aguarde o build anterior encerrar antes de executar mobile_build.ps1.'
}
. (Join-Path $PSScriptRoot 'android_env.ps1')
$repo = Split-Path -Parent $PSScriptRoot
$src = Join-Path $repo 'mobile\app'
$dst = [IO.Path]::GetFullPath($env:SLIDEDSL_MOBILE_BUILD)
# /MIR pode excluir arquivos: validar os destinos absolutos antes de qualquer espelho.
$buildRoot = [IO.Path]::GetFullPath('D:\slidedsl-mobile')
if (-not $dst.StartsWith($buildRoot + '\', [StringComparison]::OrdinalIgnoreCase)) {
  throw 'SLIDEDSL_MOBILE_BUILD deve ficar dentro de D:\slidedsl-mobile.'
}
$coreDst = [IO.Path]::GetFullPath((Join-Path (Split-Path -Parent $dst) 'slidedsl-core'))
if (-not $coreDst.StartsWith($buildRoot + '\', [StringComparison]::OrdinalIgnoreCase) -or $coreDst -eq $dst) {
  throw 'Destino do núcleo inválido.'
}
New-Item -ItemType Directory -Force $dst | Out-Null
$appExcluded = @('node_modules', 'android', 'ios', '.expo', 'outputs', 'modules\slidedsl-documents\android\build', 'modules\slidedsl-documents\android\.gradle') | ForEach-Object { Join-Path $src $_; Join-Path $dst $_ }
# Excluir somente pastas geradas da raiz: modules/*/android contém fontes locais.
robocopy $src $dst /MIR /XD $appExcluded /XF *.apk *.gguf /NFL /NDL /NJH /NJS /NP | Out-Null
if ($LASTEXITCODE -ge 8) { throw "robocopy falhou ($LASTEXITCODE)" }
if (-not (Test-Path (Join-Path $dst 'modules\slidedsl-documents\android\build.gradle'))) {
  throw 'Cópia incompleta: módulo nativo de documentos ausente.'
}
$core = Join-Path $repo 'packages\slidedsl-core'
robocopy $core $coreDst /MIR /XD node_modules dist outputs /NFL /NDL /NJH /NJS /NP | Out-Null
if ($LASTEXITCODE -ge 8) { throw "robocopy do núcleo falhou ($LASTEXITCODE)" }
Push-Location $coreDst
try {
  npm ci --no-audit --no-fund
  if ($LASTEXITCODE) { throw 'npm ci do núcleo falhou' }
  npm run build
  if ($LASTEXITCODE) { throw 'Build TypeScript do núcleo falhou' }
} finally { Pop-Location }
Push-Location $dst
try {
  npm install --no-audit --no-fund
  if ($LASTEXITCODE) { throw 'npm install falhou' }
  npm run typecheck
  if ($LASTEXITCODE) { throw 'Typecheck falhou' }
  npm test
  if ($LASTEXITCODE) { throw 'Testes do app falharam' }
  if ($SkipPrebuild) {
    if (-not (Test-Path 'android\gradlew.bat')) { throw 'SkipPrebuild exige um projeto Android já gerado.' }
    Write-Host 'Prebuild existente preservado; retomando Gradle.'
  } else {
    $prebuild = @('expo', 'prebuild', '--platform', 'android', '--no-install')
    if ($Clean -or -not (Test-Path 'android')) { $prebuild += '--clean' }
    npx @prebuild
    if ($LASTEXITCODE) { throw 'expo prebuild falhou' }
  }
  # Intermediários antigos do Expo podem ser hardlinks do SDK; preserve a cópia
  # antes de permitir que o Gradle limpe somente o arquivo intermediário.
  $nativeRoot = [IO.Path]::GetFullPath((Join-Path $dst 'node_modules\expo-modules-core\android\build\intermediates\cxx'))
  $preserved = [IO.Path]::GetFullPath((Join-Path (Split-Path -Parent $dst) 'outputs\native-preserved'))
  if (-not $nativeRoot.StartsWith($dst + '\', [StringComparison]::OrdinalIgnoreCase) -or
      -not $preserved.StartsWith($buildRoot + '\', [StringComparison]::OrdinalIgnoreCase)) { throw 'Destino de cache nativo inválido.' }
  if (Test-Path -LiteralPath $nativeRoot) {
    foreach ($lib in Get-ChildItem -LiteralPath $nativeRoot -Filter 'libc++_shared.so' -Recurse -File) {
      if ($lib.LinkType -ne 'HardLink') { continue }
      $target = [IO.Path]::GetFullPath($lib.FullName)
      if (-not $target.StartsWith($nativeRoot + '\', [StringComparison]::OrdinalIgnoreCase)) { throw 'Intermediário fora do cache esperado.' }
      New-Item -ItemType Directory -Force $preserved | Out-Null
      $backup = Join-Path $preserved ('expo-' + $lib.Directory.Name + '-' + [guid]::NewGuid().ToString('N') + '.so')
      Move-Item -LiteralPath $target -Destination $backup
      Copy-Item -LiteralPath $backup -Destination $target
      Write-Host "Hardlink do Expo preservado: $backup"
    }
  }
  Push-Location android
  try {
    $task = if ($Debug) { 'assembleDebug' } else { 'assembleRelease' }
    .\gradlew.bat $task --no-daemon
    if ($LASTEXITCODE) { throw "gradle $task falhou" }
  } finally { Pop-Location }
  $kind = if ($Debug) { 'debug' } else { 'release' }
  $apk = Get-ChildItem "android\app\build\outputs\apk\$kind\*.apk" | Select-Object -First 1
  if (-not $apk) { throw 'Gradle não produziu APK.' }
  $out = Join-Path (Split-Path -Parent $dst) "SlideDSL-$kind.apk"
  Copy-Item $apk.FullName $out -Force
  Write-Host "APK: $out ($([math]::Round((Get-Item $out).Length/1MB,1)) MB)"
} finally { Pop-Location }
