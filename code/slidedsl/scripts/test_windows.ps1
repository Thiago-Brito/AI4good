. (Join-Path $PSScriptRoot '_common.ps1')
Push-Location -LiteralPath $Script:SlideDslRoot
try {
    $env:PYTHONUTF8='1'
    $env:PATH=(Split-Path -Parent (Get-SlideDslNode))+';'+$env:PATH
    # Cada execução usa temporários próprios no projeto, inclusive em ambientes isolados.
    $runId = [guid]::NewGuid().ToString('N')
    Invoke-SlideDslNative -Exe $Script:SlideDslPython -Arguments @('-m','ruff','check','src','tests','scripts','api','benchmark')
    Invoke-SlideDslNative -Exe $Script:SlideDslPython -Arguments @('-m','ruff','format','--check','src','tests','scripts','api','benchmark')
    Invoke-SlideDslNpm -Arguments @('run','lint','--prefix','editor')
    Invoke-SlideDslNpm -Arguments @('run','format:check','--prefix','editor')
    Invoke-SlideDslNpm -Arguments @('run','build','--prefix','editor')
    Invoke-SlideDslNative -Exe $Script:SlideDslPython -Arguments @('-m','pytest','-q','--junitxml=outputs/tests/pytest.xml',"--basetemp=outputs/tests/tmp-$runId",'-o',"cache_dir=outputs/tests/cache-$runId")
    Invoke-SlideDslNpm -Arguments @('test','--prefix','renderer')
    Invoke-SlideDslNpm -Arguments @('run','lint','--prefix','renderer')
    Invoke-SlideDslNpm -Arguments @('test','--prefix','editor')
} finally { Pop-Location }
