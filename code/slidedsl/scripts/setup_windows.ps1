param([switch]$SkipBrowserDownload)
. (Join-Path $PSScriptRoot '_common.ps1')
Push-Location -LiteralPath $Script:SlideDslRoot
try {
    if (-not (Test-Path -LiteralPath $Script:SlideDslPython)) {
        $python = (Get-Command python.exe -ErrorAction Stop).Source
        $version = & $python --version
        if ($version -notmatch '^Python 3\.12\.') { throw 'Python 3.12 deve estar disponível como python.exe.' }
        Invoke-SlideDslNative -Exe $python -Arguments @('-m','venv','.venv')
    }
    Invoke-SlideDslNative -Exe $Script:SlideDslPython -Arguments @('-m','pip','install','-r','requirements-lock.txt')
    Invoke-SlideDslNative -Exe $Script:SlideDslPython -Arguments @('-m','pip','install','--no-deps','-e','.')
    Invoke-SlideDslNative -Exe $Script:SlideDslPython -Arguments @('scripts/provision_node.py')
    Invoke-SlideDslNpm -Arguments @('ci','--prefix','renderer','--no-audit','--no-fund')
    Invoke-SlideDslNpm -Arguments @('ci','--prefix','editor','--no-audit','--no-fund')
    if (-not $SkipBrowserDownload -and -not (Test-Path -LiteralPath 'C:/Program Files/Google/Chrome/Application/chrome.exe') -and -not $env:SLIDEDSL_BROWSER) {
        Invoke-SlideDslNative -Exe (Get-SlideDslNode) -Arguments @('editor/node_modules/@playwright/test/cli.js','install','chromium')
    }
    Write-Host 'Ambiente pronto. Execute scripts/test_windows.ps1 e scripts/demo_windows.ps1.'
} finally { Pop-Location }
