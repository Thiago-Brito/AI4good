"""Entrada adicional; mesma implementação da CLI instalada."""

import sys
from slidedsl.cli import main

if __name__ == "__main__":
    raise SystemExit(main(["benchmark", *sys.argv[1:]]))
