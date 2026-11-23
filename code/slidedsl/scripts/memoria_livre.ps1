# Uso: powershell -File scripts\memoria_livre.ps1 [-MinGB 3]
# Sai com código 1 se a RAM livre estiver abaixo do mínimo: não iniciar tarefa pesada nesse caso.
param([double]$MinGB = 3)
$os = Get-CimInstance Win32_OperatingSystem
$free = [math]::Round($os.FreePhysicalMemory / 1MB, 1)
$total = [math]::Round($os.TotalVisibleMemorySize / 1MB, 1)
Write-Host "RAM livre: $free GB de $total GB (mínimo $MinGB GB)"
if ($free -lt $MinGB) { exit 1 }
