# Avaliação cega v3 (docs/AVALIACAO_CEGA_V3_PROTOCOLO.md): 0.6B LoRA e 1.7B nos 4 assuntos novos, semente 11, em duas
# versões do app: a congelada (tag artigo-v2, 0.7.7) e a nova (branch exp/celular-documento, com detalhe literal).
# Usa a cópia de build D:/slidedsl-mobile/app: troca src/bench pelo código de cada versão, compila (npm test) e
# volta para o código do working tree no fim. Uso (Git Bash): bash scripts/bancada_v3.sh
set -u
R="/c/Users/brito/OneDrive/Área de Trabalho/ia/code/slidedsl"
APP=/d/slidedsl-mobile/app
V3="$R/outputs/avaliacao_cega_v3"
mata() { taskkill //F //IM llama-server.exe >/dev/null 2>&1; sleep 2; }
instala() {  # $1 = pasta com src/ e bench/ do app
  rm -rf "$APP/src" "$APP/bench" "$APP/test" "$APP/outputs/tests"
  cp -r "$1/src" "$1/bench" "$1/test" "$APP/" && (cd "$APP" && npm test > "$V3/npm_test_$2.log" 2>&1; tail -8 "$V3/npm_test_$2.log" | grep -E "^# (pass|fail)")
}
roda() {  # $1 = versão, $2 = flags extras
  for spec in lora06:Qwen3-0.6B-SlideDSL-LoRA-Q4_K_M.gguf:8.88:3.41 q17:Qwen3-1.7B-Q4_K_M.gguf:3.88:1.49; do
    IFS=: read name file ptps gtps <<< "$spec"
    OUT="$V3/celular_${1}_$name"; mkdir -p "$OUT"; mata
    /d/android/llama/llama-server.exe -m "D:/android/models/$file" -ngl 99 -c 8192 -np 1 --jinja --port 8080 --cache-ram 0 --slot-save-path D:/android/llama/slots > "$OUT/llama.log" 2>&1 &
    for i in $(seq 120); do curl -s http://127.0.0.1:8080/health | grep -q '"ok"' && break; sleep 1; done
    (cd "$APP" && node bench/app_bench.mjs --docs "$V3/documentos" --requests "$V3/pedidos.json" --out "$OUT" --seeds 11 --modes gramatica_limites+frases --phone-prompt-tps $ptps --phone-gen-tps $gtps $2 > "$OUT/bench.log" 2>&1)
    echo "$1 $name: $(tail -2 "$OUT/bench.log" | tr '\n' ' ')"
  done
  mata
}
TMP="$V3/app_artigo_v2"; rm -rf "$TMP"; mkdir -p "$TMP"
(cd "$R" && git archive artigo-v2 mobile/app/src mobile/app/bench mobile/app/test | tar -x -C "$TMP")
NOVO="$R/mobile/app"
instala "$NOVO" novo && roda novo "--detalhe-literal"
instala "$TMP/mobile/app" 077 && roda 077 ""
instala "$NOVO" novo_volta
