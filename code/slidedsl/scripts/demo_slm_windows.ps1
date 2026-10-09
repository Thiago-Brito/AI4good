param(
    [string]$PromptFile = 'benchmark/prompts/demo_slm_local.txt',
    [string]$Request = '',
    [string]$Model = 'qwen3:4b-instruct',
    [ValidateSet('json','direct')][string]$Mode = 'json',
    [string]$Out = '',
    [switch]$NoEditor,
    [switch]$Strict
)
. (Join-Path $PSScriptRoot '_common.ps1')
Push-Location -LiteralPath $Script:SlideDslRoot
try {
    $env:PYTHONUTF8 = '1'
    $env:PATH = (Split-Path -Parent (Get-SlideDslNode)) + ';' + $env:PATH
    if (-not $Out) { $Out = 'outputs/demo_local/run-' + [guid]::NewGuid().ToString('N') }
    $ollamaDemoExe = Join-Path $env:LOCALAPPDATA 'Programs/Ollama/ollama.exe'
    if (-not (Test-Path -LiteralPath $ollamaDemoExe)) { $ollamaDemoExe = (Get-Command ollama.exe -ErrorAction Stop).Source }
    try { Invoke-RestMethod 'http://127.0.0.1:11434/api/version' -TimeoutSec 3 | Out-Null }
    catch {
        Start-Process -FilePath $ollamaDemoExe -ArgumentList @('serve') -WindowStyle Hidden
        $ollamaReady = $false
        for ($retry = 0; $retry -lt 15; $retry++) {
            Start-Sleep -Milliseconds 1000
            try {
                Invoke-RestMethod 'http://127.0.0.1:11434/api/version' -TimeoutSec 2 | Out-Null
                $ollamaReady = $true
                break
            } catch {}
        }
        if (-not $ollamaReady) { throw 'Ollama local indisponivel apos iniciar serve.' }
    }
    $tags = Invoke-RestMethod 'http://127.0.0.1:11434/api/tags' -TimeoutSec 5
    if ($Model -notin $tags.models.name) { Invoke-SlideDslNative -Exe $ollamaDemoExe -Arguments @('pull',$Model) }
    if ($Request) {
        $requestDir = Join-Path $Script:SlideDslRoot 'outputs/demo_local/requests'
        New-Item -ItemType Directory -Path $requestDir -Force | Out-Null
        $PromptFile = Join-Path $requestDir ([guid]::NewGuid().ToString('N')+'.txt')
        [IO.File]::WriteAllText($PromptFile,$Request,(New-Object Text.UTF8Encoding($false)))
    }
    $demoArguments = @('-m','slidedsl.cli','demo-local','--model',$Model,'--mode',$Mode,'--prompt-file',$PromptFile,'--out',$Out)
    if ($Strict) { $demoArguments += '--strict' }
    Invoke-SlideDslNative -Exe $Script:SlideDslPython -Arguments $demoArguments
    Write-Host "SLM real: $Out/presentation.sld, ast.json, ir.json, diagnostics.json, presentation.pptx"
    if (-not $NoEditor) {
        Invoke-SlideDslNpm -Arguments @('run','build','--prefix','editor')
        $editorDemoReady = $false
        try { Invoke-RestMethod 'http://127.0.0.1:8000/api/local-demo' -TimeoutSec 3 | Out-Null; $editorDemoReady = $true } catch {}
        if (-not $editorDemoReady) {
            Start-Process -FilePath $Script:SlideDslPython -ArgumentList @('-m','uvicorn','slidedsl.server:app','--host','127.0.0.1','--port','8000') -WorkingDirectory $Script:SlideDslRoot -WindowStyle Hidden
            for ($retry = 0; $retry -lt 15; $retry++) {
                Start-Sleep -Milliseconds 1000
                try { Invoke-RestMethod 'http://127.0.0.1:8000/api/local-demo' -TimeoutSec 2 | Out-Null; $editorDemoReady = $true; break } catch {}
            }
        }
        if (-not $editorDemoReady) { throw 'PPTX gerado; editor nao iniciou na porta 8000. Verifique processo que ocupa a porta.' }
        Start-Process 'http://127.0.0.1:8000/?demo=1'
    }
} finally { Pop-Location }
