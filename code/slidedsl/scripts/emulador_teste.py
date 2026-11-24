"""Dirige o app SlideDSL no emulador Android por adb + uiautomator e recolhe os dados do teste.

Passos: abre o app, escolhe o modelo, confere a chave "Escrever slides em SlideDSL Alto" (liga ou desliga
conforme --modo), digita o pedido (ASCII: `adb shell input text` não aceita acentos), gera, espera o
resultado, toca em "Exportar dados do teste" e puxa, com `adb root` (imagem google_apis), o JSON exportado e
o PPTX gravados na pasta de documentos do app.

Pré-requisitos: emulador ligado (`adb devices`), APK instalado e o modelo em files/models/<id>.gguf.
Uso: .venv\\Scripts\\python scripts\\emulador_teste.py --modo gramatica --out outputs/teste5_emulador/gramatica
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
import time
import xml.etree.ElementTree as ET
from pathlib import Path

ADB = r"D:\android\sdk\platform-tools\adb.exe"
PKG = "br.slidedsl.app"
FILES = f"/data/data/{PKG}/files"


def adb(*args: str, check=True, text=True) -> str:
    run = subprocess.run([ADB, *args], capture_output=True, text=text, timeout=180)
    if check and run.returncode:
        raise RuntimeError(f"adb {' '.join(args)}: {run.stderr.strip()[:200]}")
    return run.stdout


def dump() -> ET.Element:
    adb("shell", "uiautomator", "dump", "/sdcard/ui.xml", check=False)
    return ET.fromstring(adb("shell", "cat", "/sdcard/ui.xml"))


def center(node: ET.Element) -> tuple[int, int]:
    a, b, c, d = map(int, re.findall(r"\d+", node.get("bounds", "[0,0][0,0]")))
    return (a + c) // 2, (b + d) // 2


def find(root: ET.Element, pattern: str, attr="text") -> ET.Element | None:
    rx = re.compile(pattern)
    for n in root.iter("node"):
        if rx.search(n.get(attr, "") or ""):
            return n
    return None


def tap_text(pattern: str, attr="text", scrolls=4) -> bool:
    for _ in range(scrolls + 1):
        node = find(dump(), pattern, attr)
        if node is not None:
            adb("shell", "input", "tap", *map(str, center(node)))
            time.sleep(1.5)
            return True
        adb("shell", "input", "swipe", "540", "1600", "540", "700", "300")
        time.sleep(1)
    return False


def say(msg: str) -> None:
    print(time.strftime("%H:%M:%S"), msg, flush=True)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--modo", choices=["gramatica", "json"], default="gramatica")
    ap.add_argument("--modelo", default=r"Qwen3 0\.6B")
    ap.add_argument("--pedido", default="Ciclo da agua para alunos do ensino fundamental")
    ap.add_argument("--out", required=True)
    ap.add_argument("--timeout-min", type=int, default=90)
    ap.add_argument("--so-esperar", action="store_true", help="geração já iniciada: só espera e recolhe")
    args = ap.parse_args(argv)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    adb("root", check=False)
    time.sleep(3)
    before = set(adb("shell", "ls", FILES, check=False).split())
    if not args.so_esperar:
        prepare(args)
    collect(args, out, before)


def prepare(args) -> None:
    adb("shell", "am", "force-stop", PKG, check=False)
    adb("shell", "monkey", "-p", PKG, "-c", "android.intent.category.LAUNCHER", "1")
    time.sleep(8)
    say("app aberto")
    if not tap_text(r"^Modelo$"):
        sys.exit("botão Modelo não encontrado")
    if not tap_text(args.modelo):
        sys.exit(f"modelo {args.modelo} não encontrado")
    switch = None
    for _ in range(5):
        root = dump()
        switch = find(root, r"Escrever slides em SlideDSL Alto", "content-desc")
        if switch is not None:
            break
        adb("shell", "input", "swipe", "540", "1600", "540", "700", "300")
        time.sleep(1)
    if switch is None:
        sys.exit("chave de escrita em SlideDSL Alto não encontrada (APK antigo?)")
    on = switch.get("checked") == "true"
    if on != (args.modo == "gramatica"):
        adb("shell", "input", "tap", *map(str, center(switch)))
        time.sleep(1)
    say(f"chave gramática: {'ligada' if args.modo == 'gramatica' else 'desligada'} (estava {'ligada' if on else 'desligada'})")
    adb("shell", "input", "swipe", "540", "700", "540", "1700", "300")
    tap_text(r"^Pedido$")
    field = find(dump(), r"EditText", "class")
    if field is None:
        sys.exit("campo do pedido não encontrado")
    adb("shell", "input", "tap", *map(str, center(field)))
    adb("shell", "input", "text", args.pedido.replace(" ", "%s"))
    adb("shell", "input", "keyevent", "4")  # BACK fecha o teclado (ESC não fecha no React Native)
    time.sleep(2)
    if not tap_text(r"^Gerar apresentação$", attr="content-desc"):
        sys.exit("botão Gerar apresentação não encontrado")
    say("gerando")


def collect(args, out: Path, before: set) -> None:
    t0, last = time.time(), ""
    while time.time() - t0 < args.timeout_min * 60:
        time.sleep(45)
        root = dump()
        if find(root, r"Exportar dados do teste") is not None and find(root, r"Compartilhar \.pptx") is not None:
            say("resultado pronto")
            break
        texts = " | ".join(n.get("text") for n in root.iter("node") if n.get("text"))[:160]
        if texts != last:
            say(texts)
            last = texts
        if find(root, r"Exportar dados do teste") is not None and find(root, r"^Gerar apresentação$") is not None:
            say("geração terminou sem resultado (erro na tela)")
            break
    else:
        sys.exit("tempo esgotado")
    adb("shell", "screencap", "-p", "/sdcard/resultado.png")
    adb("pull", "/sdcard/resultado.png", str(out / "tela_resultado.png"))
    tap_text(r"Exportar dados do teste")
    time.sleep(3)
    adb("shell", "input", "keyevent", "4")  # fecha a folha de compartilhamento
    after = adb("shell", "ls", FILES).split()
    new = [f for f in after if f not in before and (f.endswith(".json") or f.endswith(".pptx"))]
    for f in new:
        adb("pull", f"{FILES}/{f}", str(out / f))
    say(f"arquivos: {new}")


if __name__ == "__main__":
    main()
