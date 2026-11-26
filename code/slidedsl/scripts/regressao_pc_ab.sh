# A/B do fluxo do PC antes e depois de uma mudança: mesmos 12 pedidos do Teste 3, semente 11, modo gramática,
# Qwen3 4B no llama-server. "antes" roda a cópia em D:/wt_antes (git worktree no commit anterior).
# Uso (Git Bash): bash scripts/regressao_pc_ab.sh <pasta de saída>
set -e
R="/c/Users/brito/OneDrive/Área de Trabalho/ia/code/slidedsl"
OUT="${1:-$R/outputs/regressao_pc_ab}"
mkdir -p "$OUT"
taskkill //F //IM llama-server.exe >/dev/null 2>&1 || true; sleep 2
/d/android/llama/llama-server.exe -m D:/android/models/Qwen3-4B-Instruct-2507-Q4_K_M.gguf -ngl 99 -c 8192 --port 8080 --jinja > "$OUT/llama.log" 2>&1 &
for i in $(seq 120); do curl -s http://127.0.0.1:8080/health | grep -q '"ok"' && break; sleep 1; done
for lado in antes depois; do
  # Caminho no formato do Windows: o Python não entende /c/Users/... (visto em 26/11).
  if [ "$lado" = antes ]; then SRC=D:/wt_antes/code/slidedsl; else SRC="$(cygpath -m "$R")"; fi
  "$R/.venv/Scripts/python" -c "
import importlib.util, sys
spec = importlib.util.spec_from_file_location('t3', r'$SRC/scripts/teste3_restricao.py')
t3 = importlib.util.module_from_spec(spec); spec.loader.exec_module(t3)
t3.MODES = ['gramatica']
t3.main(['--seeds', '11', '--out', r'$OUT/$lado'])
" > "$OUT/$lado.log" 2>&1
  echo "$lado: $(tail -1 "$OUT/$lado.log")"
done
taskkill //F //IM llama-server.exe >/dev/null 2>&1 || true
