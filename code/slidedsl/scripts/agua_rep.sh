# Uso: agua_rep.sh <rotulo>  — 0.6B LoRA, agua.txt, 5 slides, sementes 11 22 33
# Encerra servidor antigo (o motor do celular do PC mantém um llama-server vivo sem --slot-save-path).
taskkill //F //IM llama-server.exe >/dev/null 2>&1; sleep 2
R="/c/Users/brito/OneDrive/Área de Trabalho/ia/code/slidedsl"; T="$R/outputs/repeticao_agua"; mkdir -p "$T"
/d/android/llama/llama-server.exe -m D:/android/models/Qwen3-0.6B-SlideDSL-LoRA-Q4_K_M.gguf -ngl 99 -c 8192 -np 1 --jinja --port 8080 --cache-ram 0 --slot-save-path D:/android/llama/slots > "$T/llama.log" 2>&1 &
srv=$!
for i in $(seq 120); do curl -s http://127.0.0.1:8080/health | grep -q '"ok"' && break; sleep 1; done
for s in 11 22 33; do
  (cd /d/slidedsl-mobile/app && node bench/motor_pc.mjs --pedido "Explique o ciclo da água para alunos do ensino fundamental" --slides 5 --documento "$R/outputs/teste4/documentos/agua.txt" --semente $s --out "$T/$1_s$s" > "$T/$1_s$s.log" 2>&1)
  echo "$1 s$s: $(tail -1 "$T/$1_s$s.log")"
done
kill $srv; sleep 2; taskkill //F //IM llama-server.exe >/dev/null 2>&1; true
