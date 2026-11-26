# Roda os 12 pedidos do Teste 3 (semente 11, modo gramática, Qwen3 4B) com o código atual, numa pasta.
# Uso (Git Bash): bash scripts/rodar_t3_lado.sh <pasta de saída> [sementes]
set -e
R="/c/Users/brito/OneDrive/Área de Trabalho/ia/code/slidedsl"
OUT="$1"; SEEDS="${2:-11}"
mkdir -p "$OUT"
taskkill //F //IM llama-server.exe >/dev/null 2>&1 || true; sleep 2
/d/android/llama/llama-server.exe -m D:/android/models/Qwen3-4B-Instruct-2507-Q4_K_M.gguf -ngl 99 -c 8192 --port 8080 --jinja > "$OUT/llama.log" 2>&1 &
for i in $(seq 120); do curl -s http://127.0.0.1:8080/health | grep -q '"ok"' && break; sleep 1; done
W="$(cygpath -m "$R")"
"$R/.venv/Scripts/python" -c "
import importlib.util
spec = importlib.util.spec_from_file_location('t3', r'$W/scripts/teste3_restricao.py')
t3 = importlib.util.module_from_spec(spec); spec.loader.exec_module(t3)
t3.MODES = ['gramatica']
t3.main(['--seeds', '$SEEDS', '--out', r'$(cygpath -m "$OUT")'])
" > "$OUT/run.log" 2>&1
tail -1 "$OUT/run.log"
taskkill //F //IM llama-server.exe >/dev/null 2>&1 || true
