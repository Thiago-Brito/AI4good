# T3 da noite de 26/11: todos os motores no mesmo documento. Os do celular ligam o próprio llama-server; depois,
# o 4B para o fluxo do PC; por último, o GPT-5.4-mini (pago, uma execução).
# Uso (Git Bash): bash scripts/bancada_documento.sh <pasta>
R="/c/Users/brito/OneDrive/Área de Trabalho/ia/code/slidedsl"
OUT="$1"; mkdir -p "$OUT"; W="$(cygpath -m "$OUT")"
PY="$R/.venv/Scripts/python"
taskkill //F //IM llama-server.exe >/dev/null 2>&1; sleep 2
"$PY" "$R/scripts/bancada_documento.py" --out "$W" celular:qwen3-0.6b-lora celular:qwen3-0.6b celular:qwen3-1.7b celular:qwen3-4b-instruct celular:qwen3-4b-instruct-lora
taskkill //F //IM llama-server.exe >/dev/null 2>&1; sleep 2
/d/android/llama/llama-server.exe -m D:/android/models/Qwen3-4B-Instruct-2507-Q4_K_M.gguf -ngl 99 -c 8192 --port 8080 --jinja > "$OUT/llama.log" 2>&1 &
for i in $(seq 120); do curl -s http://127.0.0.1:8080/health | grep -q '"ok"' && break; sleep 1; done
"$PY" "$R/scripts/bancada_documento.py" --out "$W" pc:llamacpp
taskkill //F //IM llama-server.exe >/dev/null 2>&1
"$PY" "$R/scripts/bancada_documento.py" --out "$W" pc:openai
