from pathlib import Path

import pytest

from slidedsl.parser import parse
from slidedsl.semantic import analyze


@pytest.fixture
def root():
    return Path(__file__).resolve().parents[1]


@pytest.fixture
def compile_scene(root):
    def build(commands, theme="claro"):
        return analyze(
            parse(f'apresentacao "Teste" {{ tema {theme} slide 1 {{ {commands} }} }}'), root
        )

    return build
