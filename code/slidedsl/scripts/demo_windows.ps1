. (Join-Path $PSScriptRoot '_common.ps1')
Push-Location -LiteralPath $Script:SlideDslRoot
try {
    $env:PYTHONUTF8='1'
    Invoke-SlideDslNative -Exe $Script:SlideDslPython -Arguments @('-m','slidedsl.cli','validate','examples/cinco_slides.sld','--json','outputs/validation.json')
    Invoke-SlideDslNative -Exe $Script:SlideDslPython -Arguments @('-m','slidedsl.cli','ast','examples/cinco_slides.sld','--out','outputs/ast.json')
    Invoke-SlideDslNative -Exe $Script:SlideDslPython -Arguments @('-m','slidedsl.cli','ir','examples/cinco_slides.sld','--out','outputs/deck.json')
    Invoke-SlideDslNative -Exe $Script:SlideDslPython -Arguments @('-m','slidedsl.cli','compile','examples/cinco_slides.sld','--out','outputs/apresentacao.pptx')
    Invoke-SlideDslNative -Exe $Script:SlideDslPython -Arguments @('scripts/inspect_delivery.py')
    Write-Host 'Demo concluída em outputs/apresentacao.pptx. Editor: .venv/Scripts/slidedsl.exe serve'
} finally { Pop-Location }
