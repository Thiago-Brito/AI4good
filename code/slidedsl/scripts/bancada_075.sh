R="/c/Users/brito/OneDrive/Área de Trabalho/ia/code/slidedsl"
# Bancada do Teste 9 (docs/RESULTADOS_T9.md): 3 modelos do celular × 24 apresentações, código do app 0.7.5.
# Uso (Git Bash, com a cópia de build em D:/slidedsl-mobile/app compilada por npm test): bash scripts/bancada_075.sh
for spec in lora06:Qwen3-0.6B-SlideDSL-LoRA-Q4_K_M.gguf:8.88:3.41 q06:Qwen3-0.6B.Q4_K_M.gguf:8.88:3.41 q17:Qwen3-1.7B-Q4_K_M.gguf:3.88:1.49; do
  IFS=: read name file ptps gtps <<< "$spec"
  OUT="$R/outputs/teste9_v075_$name"; mkdir -p "$OUT"
  /d/android/llama/llama-server.exe -m "D:/android/models/$file" -ngl 99 -c 8192 -np 1 --jinja --port 8080 --cache-ram 0 --slot-save-path D:/android/llama/slots > "$OUT/llama.log" 2>&1 &
  srv=$!
  for i in $(seq 120); do curl -s http://127.0.0.1:8080/health | grep -q '"ok"' && break; sleep 1; done
  (cd /d/slidedsl-mobile/app && node bench/app_bench.mjs --docs "$R/outputs/teste4/documentos" --requests "$R/benchmark/format_requests.json" --out "$OUT" --seeds 11,22 --modes gramatica_limites+frases --phone-prompt-tps $ptps --phone-gen-tps $gtps > "$OUT/bench.log" 2>&1)
  echo "$name: $(tail -2 "$OUT/bench.log" | tr '\n' ' ')"
  kill $srv; sleep 3; taskkill //F //IM llama-server.exe >/dev/null 2>&1; sleep 2
done
