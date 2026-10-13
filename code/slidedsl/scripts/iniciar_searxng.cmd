@echo off
rem Inicia o SearXNG local (exige Docker Desktop aberto) e confere se responde.
cd /d "%~dp0.."
docker --version >nul 2>&1 || (
  echo Docker nao encontrado. Instale o Docker Desktop: https://www.docker.com/products/docker-desktop/
  exit /b 1
)
rem Cada instalacao guarda seu segredo em arquivo local, fora do Git.
powershell -NoProfile -Command "$path='searxng\.env'; if (-not (Test-Path -LiteralPath $path)) { $bytes=New-Object byte[] 32; $rng=[System.Security.Cryptography.RandomNumberGenerator]::Create(); $rng.GetBytes($bytes); $rng.Dispose(); $secret=[BitConverter]::ToString($bytes).Replace('-','').ToLowerInvariant(); [System.IO.File]::WriteAllText($path,('SEARXNG_SECRET='+$secret+[Environment]::NewLine),[System.Text.UTF8Encoding]::new($false)) }" || exit /b 1
docker compose -f searxng\docker-compose.yml up -d || exit /b 1
echo Aguardando o SearXNG...
for /l %%i in (1,1,30) do (
  powershell -NoProfile -Command "try { (Invoke-WebRequest -UseBasicParsing http://127.0.0.1:8888/healthz -TimeoutSec 2).StatusCode } catch { exit 1 }" >nul 2>&1 && goto ok
  powershell -NoProfile -Command "Start-Sleep -Seconds 2"
)
echo SearXNG nao respondeu. Veja: docker logs slidedsl-searxng
exit /b 1
:ok
powershell -NoProfile -Command "$ErrorActionPreference='Stop'; $r = Invoke-RestMethod 'http://127.0.0.1:8888/search?q=microsservicos&format=json' -TimeoutSec 30; Write-Host ('SearXNG pronto: ' + $r.results.Count + ' resultados de teste.')" || exit /b 1
echo No painel, mantenha a pesquisa ativada.
