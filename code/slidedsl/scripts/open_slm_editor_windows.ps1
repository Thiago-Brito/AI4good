param(
    [ValidateRange(1024,65535)][int]$Port = 8000,
    [switch]$NoBrowser
)
. (Join-Path $PSScriptRoot '_common.ps1')
Push-Location -LiteralPath $Script:SlideDslRoot
try {
    $env:PYTHONUTF8 = '1'
    $env:PATH = (Split-Path -Parent (Get-SlideDslNode)) + ';' + $env:PATH
    if (-not (Test-Path -LiteralPath $Script:SlideDslPython)) {
        throw 'Instale o ambiente com scripts/setup_windows.ps1 antes de abrir o editor.'
    }
    try { Invoke-RestMethod 'http://127.0.0.1:11434/api/version' -TimeoutSec 3 | Out-Null }
    catch {
        $slmEditorOllama = Join-Path $env:LOCALAPPDATA 'Programs/Ollama/ollama.exe'
        if (-not (Test-Path -LiteralPath $slmEditorOllama)) {
            $slmEditorOllama = (Get-Command ollama.exe -ErrorAction Stop).Source
        }
        Start-Process -FilePath $slmEditorOllama -ArgumentList @('serve') -WindowStyle Hidden
        $slmEditorOllamaReady = $false
        for ($retry = 0; $retry -lt 15; $retry++) {
            Start-Sleep -Milliseconds 1000
            try {
                Invoke-RestMethod 'http://127.0.0.1:11434/api/version' -TimeoutSec 2 | Out-Null
                $slmEditorOllamaReady = $true
                break
            } catch {}
        }
        if (-not $slmEditorOllamaReady) { throw 'Ollama nao iniciou. Verifique a instalacao local.' }
    }
    Invoke-SlideDslNpm -Arguments @('run','build','--prefix','editor')
    $slmEditorUrl = "http://127.0.0.1:$Port"
    $slmEditorReady = $false
    try {
        $slmEditorModels = Invoke-RestMethod "$slmEditorUrl/api/models" -TimeoutSec 3
        $slmEditorReady = $null -ne $slmEditorModels.available
    } catch {}
    if (-not $slmEditorReady) {
        $slmEditorLogs = Join-Path $Script:SlideDslRoot 'outputs/editor_server'
        New-Item -ItemType Directory -Path $slmEditorLogs -Force | Out-Null
        $slmEditorRunId = [guid]::NewGuid().ToString('N')
        $slmEditorProcess = Start-Process -FilePath $Script:SlideDslPython -ArgumentList @('-m','uvicorn','slidedsl.server:app','--host','127.0.0.1','--port',"$Port") -WorkingDirectory $Script:SlideDslRoot -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $slmEditorLogs "$slmEditorRunId.stdout.log") -RedirectStandardError (Join-Path $slmEditorLogs "$slmEditorRunId.stderr.log")
        for ($retry = 0; $retry -lt 15; $retry++) {
            Start-Sleep -Milliseconds 1000
            try {
                $slmEditorModels = Invoke-RestMethod "$slmEditorUrl/api/models" -TimeoutSec 2
                if ($null -ne $slmEditorModels.available) { $slmEditorReady = $true; break }
            } catch {}
        }
        if (-not $slmEditorReady) { throw "Editor nao iniciou na porta $Port. Consulte outputs/editor_server/ ou use -Port com uma porta livre." }
        Write-Host "Servidor local PID $($slmEditorProcess.Id); logs em outputs/editor_server/."
    }
    Write-Host "Editor com geracao local: $slmEditorUrl"
    if (-not $NoBrowser) { Start-Process $slmEditorUrl }
} finally { Pop-Location }
