@echo off
cd /d "%~dp0.."
docker compose -f searxng\docker-compose.yml down
