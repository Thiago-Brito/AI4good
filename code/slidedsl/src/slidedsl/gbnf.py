"""Converte a GLC (subconjunto Lark usado pela SlideDSL) em GBNF para geração restrita.

Com GBNF, o servidor de inferência (llama.cpp) só permite tokens que mantêm o texto
dentro da gramática: o SLM não consegue produzir um programa sintaticamente inválido.
A conversão parte do EBNF original (preserva `+ * ?`), sem a recursão à esquerda que
o Lark cria internamente para LALR — llama.cpp não aceita recursão à esquerda.

Também há um reconhecedor GBNF mínimo (`GBNFMatcher`) para testar a conversão sem
servidor: todo programa aceito pelo Lark deve ser aceito pela GBNF gerada.
"""

from dataclasses import dataclass
from functools import lru_cache
import json
from pathlib import Path
import re

# Terminais importados de lark.common (%import), já em GBNF. Terminais declarados
# na própria gramática são convertidos a partir da regex/literais originais.
TERMINAL_OVERRIDES = {
    "STRING": r'"\"" ( [^"\\\x00-\x1F] | "\\" ["\\/bfnrt] | "\\u" [0-9a-fA-F]{4} ){0,600} "\""',
    "INT": "[0-9]{1,6}",
    "SIGNED_INT": '"-"? [0-9]{1,6}',
}
IGNORED = {"WS", "CPP_COMMENT", "COMMENT"}


@dataclass
class Rule:
    name: str
    inline: bool
    body: str  # expressão Lark (alternativas com aliases removidos)


def _strip_comments(text: str) -> str:
    # O subconjunto usado pelo projeto só tem comentários de linha inteira.
    return "\n".join(line for line in text.splitlines() if not line.strip().startswith("//"))


def parse_lark(text: str) -> tuple[dict[str, Rule], dict[str, str]]:
    """Retorna (regras, terminais) do subconjunto Lark usado nas gramáticas do projeto."""
    text = _strip_comments(text)
    statements, current = [], ""
    for line in text.splitlines():
        if not line.strip():
            continue
        if re.match(r"^\s*[|]", line) or (line.startswith((" ", "\t")) and current):
            current += " " + line.strip()
        else:
            if current:
                statements.append(current)
            current = line.strip()
    if current:
        statements.append(current)
    rules, terminals = {}, {}
    for st in statements:
        if st.startswith("%"):
            continue
        m = re.match(r"^([?!]?)([a-zA-Z_][a-zA-Z0-9_]*)(\.\d+)?\s*:\s*(.*)$", st)
        if not m:
            raise ValueError(f"Declaração Lark não suportada: {st[:60]}")
        prefix, name, _, body = m.groups()
        body = re.sub(r"->\s*[a-z_][a-z0-9_]*", "", body)  # aliases não mudam a linguagem
        if name.isupper():
            terminals[name] = body.strip()
        else:
            rules[name] = Rule(name, prefix == "?", body.strip())
    return rules, terminals


def _gbnf_name(name: str) -> str:
    return ("t-" if name.isupper() else "") + name.lower().replace("_", "-")


def _escape(literal: str) -> str:
    return json.dumps(literal, ensure_ascii=False)


def _regex_to_gbnf(pattern: str) -> str:
    """Converte regexes simples (classes, grupos, ?, *, +, |) em GBNF."""
    out, k = [], 0
    while k < len(pattern):
        c = pattern[k]
        if c == "[":
            end = pattern.index("]", k + 1)
            out.append(pattern[k : end + 1])
            k = end + 1
        elif c == "(":
            k += 3 if pattern[k : k + 3] == "(?:" else 1
            out.append("(")
        elif c == "{":
            end = pattern.index("}", k)
            out.append(pattern[k : end + 1])
            k = end + 1
        elif c in ")|?*+":
            out.append(f" {c} " if c == "|" else c)
            k += 1
        elif c == "\\":
            nxt = pattern[k + 1]
            out.append({"d": "[0-9]", "s": "[ \\t\\n]", "w": "[a-zA-Z0-9_]"}.get(nxt, _escape(nxt)))
            k += 2
        elif c == ".":
            out.append("[^\\n]")
            k += 1
        else:
            out.append(_escape(c))
            k += 1
    joined = " ".join(out)
    for op in ("?", "*", "+", ")", "{"):
        joined = joined.replace(" " + op, op)
    return joined


def _tokenize(body: str) -> list[str]:
    tokens = re.findall(
        r'"(?:[^"\\]|\\.)*"i?|/(?:[^/\\]|\\.)+/[a-z]*|[A-Za-z_][A-Za-z0-9_]*|[()|?*+]', body
    )
    return tokens


def _expr_to_gbnf(body: str, known: set[str]) -> str:
    """Cada terminal vira `ws terminal` (equivalente a %ignore WS); toda regra começa,
    portanto, aceitando espaços/linhas, inclusive dentro de repetições."""
    tokens = _tokenize(body)
    out = []
    for k, tok in enumerate(tokens):
        nxt = tokens[k + 1] if k + 1 < len(tokens) else ""
        if tok in "()|?*+":
            out.append(tok)
            continue
        if tok.startswith('"'):
            atom = _escape(json.loads(tok.rstrip("i")))
        elif tok.startswith("/"):
            atom = "(" + _regex_to_gbnf(tok[1 : tok.rindex("/")]) + ")"
        else:
            if tok not in known:
                raise ValueError(f"Símbolo não definido na gramática: {tok}")
            atom = _gbnf_name(tok)
            if not tok.isupper():  # regras já começam com ws
                out.append(atom)
                continue
        out.append(f"(ws {atom})" if nxt in ("?", "*", "+") else f"ws {atom}")
    joined = " ".join(out)
    for op in ("?", "*", "+", ")"):
        joined = joined.replace(" " + op, op)
    return joined.replace("( ", "(")


def lark_to_gbnf(text: str, start: str = "start") -> str:
    rules, terminals = parse_lark(text)
    if start not in rules:
        raise ValueError(f"Regra inicial inexistente: {start}")
    known = set(rules) | set(terminals) | set(TERMINAL_OVERRIDES)
    lines = [f"root ::= {_gbnf_name(start)} ws", "ws ::= [ \\t\\n]{0,20}"]
    # Só emite regras alcançáveis a partir de `start`.
    reachable, pending = set(), [start]
    while pending:
        name = pending.pop()
        if name in reachable:
            continue
        reachable.add(name)
        body = rules[name].body if name in rules else terminals.get(name, "")
        for tok in _tokenize(body):
            if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", tok) and tok in known:
                pending.append(tok)
    for name in sorted(reachable, key=lambda n: (n.isupper(), n != start, n)):
        if name in IGNORED:
            continue
        if name in TERMINAL_OVERRIDES and (name == "STRING" or name not in terminals):
            lines.append(f"{_gbnf_name(name)} ::= {TERMINAL_OVERRIDES[name]}")
        elif name in terminals:
            body = terminals[name]
            alternatives = [a.strip() for a in body.split("|")]
            if all(a.startswith('"') for a in alternatives):
                lines.append(
                    f"{_gbnf_name(name)} ::= "
                    + " | ".join(_escape(json.loads(a)) for a in alternatives)
                )
            elif body.startswith("/") and body.endswith("/"):
                lines.append(f"{_gbnf_name(name)} ::= {_regex_to_gbnf(body[1:-1])}")
            else:
                raise ValueError(f"Terminal sem conversão GBNF: {name}")
        else:
            lines.append(f"{_gbnf_name(name)} ::= {_expr_to_gbnf(rules[name].body, known)}")
    return "\n".join(lines) + "\n"


@lru_cache
def alto_gbnf(start: str = "start") -> str:
    from .alto import grammar_text

    return lark_to_gbnf(grammar_text(), start)


def low_level_gbnf() -> str:
    text = Path(__file__).with_name("grammar").joinpath("slidedsl.lark").read_text("utf-8")
    return lark_to_gbnf(text)


# ---------------------------------------------------------------------------
# Reconhecedor GBNF mínimo (testes): literais, classes, grupos, | ? * + {m,n}.


class GBNFMatcher:
    def __init__(self, grammar: str):
        self.rules = {}
        for line in grammar.splitlines():
            if "::=" in line:
                name, body = line.split("::=", 1)
                self.rules[name.strip()] = self._parse(body.strip())

    # Árvore: ("alt", [seq...]) / ("seq", [item...]) / ("lit", s) / ("cls", neg, ranges)
    #         ("ref", name) / ("rep", node, min, max)
    def _parse(self, body: str):
        self._s, self._k = body, 0
        node = self._alt()
        return node

    def _ws(self):
        while self._k < len(self._s) and self._s[self._k] in " \t":
            self._k += 1

    def _alt(self):
        seqs = [self._seq()]
        self._ws()
        while self._k < len(self._s) and self._s[self._k] == "|":
            self._k += 1
            seqs.append(self._seq())
            self._ws()
        return ("alt", seqs)

    def _seq(self):
        items = []
        while True:
            self._ws()
            if self._k >= len(self._s) or self._s[self._k] in "|)":
                return ("seq", items)
            items.append(self._postfix(self._atom()))

    def _atom(self):
        s, k = self._s, self._k
        if s[k] == '"':
            end = k + 1
            while s[end] != '"':
                end += 2 if s[end] == "\\" else 1
            self._k = end + 1
            return ("lit", json.loads(s[k : end + 1]))
        if s[k] == "[":
            end = k + 1
            while s[end] != "]":
                end += 2 if s[end] == "\\" else 1
            self._k = end + 1
            return self._cls(s[k + 1 : end])
        if s[k] == "(":
            self._k += 1
            node = self._alt()
            self._k += 1  # ')'
            return node
        m = re.compile(r"[a-zA-Z0-9-]+").match(s, k)
        self._k = m.end()
        return ("ref", m.group(0))

    def _cls(self, body):
        neg = body.startswith("^")
        body = body[1:] if neg else body
        chars, k = [], 0
        while k < len(body):
            if body[k] == "\\":
                esc = body[k + 1]
                if esc == "x":
                    chars.append(chr(int(body[k + 2 : k + 4], 16)))
                    k += 4
                    continue
                chars.append({"n": "\n", "t": "\t", "r": "\r"}.get(esc, esc))
                k += 2
            else:
                chars.append(body[k])
                k += 1
        ranges, k = [], 0
        while k < len(chars):
            if k + 2 < len(chars) and chars[k + 1] == "-":
                ranges.append((chars[k], chars[k + 2]))
                k += 3
            else:
                ranges.append((chars[k], chars[k]))
                k += 1
        return ("cls", neg, ranges)

    def _postfix(self, node):
        s = self._s
        if self._k < len(s) and s[self._k] in "?*+":
            op = s[self._k]
            self._k += 1
            return ("rep", node, 0 if op in "?*" else 1, 1 if op == "?" else None)
        if self._k < len(s) and s[self._k] == "{":
            end = s.index("}", self._k)
            low, _, high = s[self._k + 1 : end].partition(",")
            self._k = end + 1
            high = int(high) if high else (int(low) if not _ else None)
            return ("rep", node, int(low), high)
        return node

    def _match(self, node, text, i):
        kind = node[0]
        if kind == "lit":
            if text.startswith(node[1], i):
                yield i + len(node[1])
        elif kind == "cls":
            if i < len(text):
                inside = any(a <= text[i] <= b for a, b in node[2])
                if inside != node[1]:
                    yield i + 1
        elif kind == "ref":
            key = (node[1], i)
            if key not in self._memo:
                self._memo[key] = list(dict.fromkeys(self._match(self.rules[node[1]], text, i)))
            yield from self._memo[key]
        elif kind == "alt":
            for seq in node[1]:
                yield from self._match(seq, text, i)
        elif kind == "seq":
            yield from self._seq_match(node[1], 0, text, i)
        elif kind == "rep":
            yield from self._rep(node, text, i, 0)

    def _seq_match(self, items, k, text, i):
        if k == len(items):
            yield i
            return
        for j in self._match(items[k], text, i):
            yield from self._seq_match(items, k + 1, text, j)

    def _rep(self, node, text, i, count):
        _, inner, low, high = node
        if count >= low:
            yield i
        if high is not None and count >= high:
            return
        for j in self._match(inner, text, i):
            if j != i:
                yield from self._rep(node, text, j, count + 1)

    def accepts(self, text: str, start: str = "root") -> bool:
        self._memo = {}
        import sys

        limit = sys.getrecursionlimit()
        sys.setrecursionlimit(max(limit, 20000))
        try:
            return any(j == len(text) for j in self._match(("ref", start), text, 0))
        finally:
            sys.setrecursionlimit(limit)
