# Ambiente Android do SlideDSL (APK). Uso: . .\scripts\android_env.ps1
# Tudo fica fora do C: (pouco espaço) e fora do OneDrive. Mude SLIDEDSL_ANDROID_ROOT se quiser.
$root = if ($env:SLIDEDSL_ANDROID_ROOT) { $env:SLIDEDSL_ANDROID_ROOT } else { 'D:\android' }
$env:JAVA_HOME = Join-Path $root 'jdk17'
$env:ANDROID_HOME = Join-Path $root 'sdk'
$env:ANDROID_SDK_ROOT = $env:ANDROID_HOME
$env:GRADLE_USER_HOME = Join-Path $root 'gradle'
$env:npm_config_cache = Join-Path $root 'npm-cache'
# Metro, Hermes, npm e Java também usam a pasta temporária do sistema.
$mobileTemp = Join-Path $root 'tmp'
New-Item -ItemType Directory -Force $mobileTemp | Out-Null
$env:TEMP = $mobileTemp
$env:TMP = $mobileTemp
$env:TMPDIR = $mobileTemp
$env:ANDROID_USER_HOME = Join-Path $root 'user'
$javaUserCache = Join-Path $root 'java-home'
$kotlinRunCache = Join-Path $root 'kotlin-daemon'
New-Item -ItemType Directory -Force $env:ANDROID_USER_HOME,$javaUserCache,$kotlinRunCache | Out-Null
# Kotlin usa LOCALAPPDATA no Windows se runFilesPath não for definido explicitamente.
$mobileJavaOptions = '-Duser.home="' + $javaUserCache + '" -Dkotlin.daemon.options="runFilesPath=' + $kotlinRunCache + '"'
if ($env:JAVA_TOOL_OPTIONS -notlike '*kotlin.daemon.options*') {
  $env:JAVA_TOOL_OPTIONS = (($env:JAVA_TOOL_OPTIONS + ' ' + $mobileJavaOptions).Trim())
}
$env:SLIDEDSL_MOBILE_BUILD = if ($env:SLIDEDSL_MOBILE_BUILD) { $env:SLIDEDSL_MOBILE_BUILD } else { 'D:\slidedsl-mobile\app' }
$env:PATH = "$($env:JAVA_HOME)\bin;$($env:ANDROID_HOME)\platform-tools;$($env:ANDROID_HOME)\cmdline-tools\latest\bin;$env:PATH"
Write-Host "JAVA_HOME=$($env:JAVA_HOME)  ANDROID_HOME=$($env:ANDROID_HOME)  build=$($env:SLIDEDSL_MOBILE_BUILD)"
