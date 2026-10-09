$ErrorActionPreference = 'Stop'
$Script:SlideDslRoot = Split-Path -Parent $PSScriptRoot
$Script:SlideDslPython = Join-Path $Script:SlideDslRoot '.venv/Scripts/python.exe'

function Invoke-SlideDslNative {
    param([string]$Exe, [string[]]$Arguments)
    & $Exe @Arguments
    if ($LASTEXITCODE -ne 0) { throw "Comando falhou ($LASTEXITCODE): $Exe" }
}

function Get-SlideDslNode {
    $portable = Join-Path $Script:SlideDslRoot 'outputs/runtime/node.exe'
    if ($env:SLIDEDSL_NODE) { return $env:SLIDEDSL_NODE }
    if (Test-Path -LiteralPath $portable) { return $portable }
    $node = (Get-Command node.exe -ErrorAction Stop).Source
    $version = & $node --version
    if ($version -notmatch '^v24\.') { throw 'Node 24 é obrigatório. Execute setup_windows.ps1.' }
    return $node
}

function Invoke-SlideDslNpm {
    param([string[]]$Arguments)
    $node = Get-SlideDslNode
    $npmCommand = (Get-Command npm.cmd -ErrorAction Stop).Source
    $npmCli = Join-Path (Split-Path -Parent $npmCommand) 'node_modules/npm/bin/npm-cli.js'
    if (-not (Test-Path -LiteralPath $npmCli)) { throw 'npm-cli.js não encontrado junto ao npm.cmd. Instale Node/npm.' }
    # Invocar npm via Node 24 evita que npm.cmd prefira o Node 22 instalado ao seu lado.
    Invoke-SlideDslNative -Exe $node -Arguments (@($npmCli) + $Arguments)
}
