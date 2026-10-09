param([Parameter(Mandatory=$true)][string]$Pptx, [Parameter(Mandatory=$true)][string]$OutDir)
$ErrorActionPreference = 'Stop'
$app = $null
$deck = $null
try {
    $app = New-Object -ComObject PowerPoint.Application
    $deck = $app.Presentations.Open($Pptx, $true, $false, $false)
    New-Item -ItemType Directory -Path $OutDir -Force | Out-Null
    $deck.Export($OutDir, 'PNG', 1280, 720)
} finally {
    if ($null -ne $deck) { $deck.Close(); [void][Runtime.InteropServices.Marshal]::ReleaseComObject($deck) }
    if ($null -ne $app) { $app.Quit(); [void][Runtime.InteropServices.Marshal]::ReleaseComObject($app) }
}
