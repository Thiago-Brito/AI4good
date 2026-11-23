# Auxiliar de teste no emulador (adb + uiautomator). Uso:
#   . scripts\emu_ui.ps1 ; Get-UiNodes ; Tap-Text 'Modelo' ; Get-UiTexts
. (Join-Path $PSScriptRoot 'android_env.ps1') | Out-Null

function Get-UiXml {
  adb shell uiautomator dump /sdcard/ui.xml 2>$null | Out-Null
  adb pull /sdcard/ui.xml D:\android\ui.xml 2>$null | Out-Null
  return [xml](Get-Content D:\android\ui.xml -Raw -Encoding UTF8)
}

function Get-UiTexts {
  (Get-UiXml).SelectNodes('//node[@text!=""]') | ForEach-Object { $_.text }
}

function Get-UiNodes {
  (Get-UiXml).SelectNodes('//node[@clickable="true"]') | ForEach-Object { "$($_.text)|$($_.'content-desc')|$($_.bounds)" }
}

function Tap-Text([string]$label, [int]$scrolls = 3) {
  for ($i = 0; $i -le $scrolls; $i++) {
    $x = Get-UiXml
    $n = $x.SelectNodes('//node') | Where-Object { $_.text -eq $label -or $_.'content-desc' -eq $label } | Select-Object -First 1
    if ($n -and $n.bounds -match '\[(\d+),(\d+)\]\[(\d+),(\d+)\]') {
      $cx = ([int]$matches[1] + [int]$matches[3]) / 2; $cy = ([int]$matches[2] + [int]$matches[4]) / 2
      adb shell input tap $cx $cy; Start-Sleep -Milliseconds 800; return $true
    }
    adb shell input swipe 540 1800 540 700 300; Start-Sleep -Milliseconds 600
  }
  return $false
}

function Shot([string]$name) {
  adb shell screencap -p /sdcard/s.png; adb pull /sdcard/s.png "D:\android\$name.png" | Out-Null
}
