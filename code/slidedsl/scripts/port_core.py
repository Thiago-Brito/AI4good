"""Tradução mecânica auditável das funções puras para TypeScript.

Uso de desenvolvimento, nunca executado pelo pacote. O runtime TS não interpreta
Python: funções, condições, laços e expressões são emitidos como código TS.
As adaptações de I/O e os contratos públicos ficam em módulos escritos à mão.
"""

import ast
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "packages/slidedsl-core/src/port.ts"


class Port:
    def __init__(self):
        self.depth = 0
        self.in_class = False

    def e(self, n):
        if n is None:
            return "null"
        if isinstance(n, ast.Constant):
            return json.dumps(n.value, ensure_ascii=False)
        if isinstance(n, ast.Name):
            return {
                "self": "this",
                "True": "true",
                "False": "false",
                "None": "null",
                "default": "defaultValue",
                "re": "p.re",
                "math": "p.math",
            }.get(n.id, n.id)
        if isinstance(n, (ast.List, ast.Tuple, ast.Set)):
            seq = "[" + ", ".join(self.e(x) for x in n.elts) + "]"
            return "new Set(" + seq + ")" if isinstance(n, ast.Set) else seq
        if isinstance(n, ast.Dict):
            return (
                "({"
                + ", ".join(
                    ("..." + self.e(v)) if k is None else "[" + self.e(k) + "]: " + self.e(v)
                    for k, v in zip(n.keys, n.values)
                )
                + "})"
            )
        if isinstance(n, ast.Attribute):
            return self.e(n.value) + "." + n.attr
        if isinstance(n, ast.Starred):
            return "...p.iter(" + self.e(n.value) + ")"
        if isinstance(n, ast.Subscript):
            if isinstance(n.slice, ast.Slice):
                return f"p.slice({self.e(n.value)}, {self.e(n.slice.lower)}, {self.e(n.slice.upper)}, {self.e(n.slice.step)})"
            return f"p.at({self.e(n.value)}, {self.e(n.slice)})"
        if isinstance(n, ast.BinOp):
            a, b = self.e(n.left), self.e(n.right)
            return f"p.bin({json.dumps(type(n.op).__name__)}, {a}, {b})"
        if isinstance(n, ast.UnaryOp):
            op = {ast.Not: "!p.truth", ast.USub: "-", ast.UAdd: "+"}[type(n.op)]
            return f"{op}({self.e(n.operand)})"
        if isinstance(n, ast.BoolOp):
            return (
                "p."
                + ("and" if isinstance(n.op, ast.And) else "or")
                + "(["
                + ", ".join("() => " + self.e(v) for v in n.values)
                + "])"
            )
        if isinstance(n, ast.Compare):
            values = [n.left] + n.comparators
            return (
                "("
                + " && ".join(
                    f"p.cmp({json.dumps(type(op).__name__)}, {self.e(values[i])}, {self.e(values[i + 1])})"
                    for i, op in enumerate(n.ops)
                )
                + ")"
            )
        if isinstance(n, ast.IfExp):
            return f"(p.truth({self.e(n.test)}) ? {self.e(n.body)} : {self.e(n.orelse)})"
        if isinstance(n, ast.NamedExpr):
            return f"({self.target(n.target)} = {self.e(n.value)})"
        if isinstance(n, ast.JoinedStr):
            parts = []
            for v in n.values:
                if isinstance(v, ast.Constant):
                    parts.append(self.e(v))
                else:
                    spec = self.e(v.format_spec) if v.format_spec else '""'
                    parts.append(f"p.format({self.e(v.value)}, {spec}, {v.conversion})")
            return "(" + " + ".join(parts) + ")"
        if isinstance(n, ast.Lambda):
            params = [a.arg for a in n.args.args] + (
                ["..." + n.args.vararg.arg] if n.args.vararg else []
            )
            return "(" + ", ".join(params) + ") => " + self.e(n.body)
        if isinstance(n, (ast.ListComp, ast.SetComp, ast.GeneratorExp, ast.DictComp)):
            variables = {
                x.id for g in n.generators for x in ast.walk(g.target) if isinstance(x, ast.Name)
            }
            variables |= {x.target.id for x in ast.walk(n) if isinstance(x, ast.NamedExpr)}
            out = "(() => { let " + ", ".join(sorted(variables)) + "; const result = []; "
            for g in n.generators:
                out += "for (" + self.target(g.target) + " of p.iter(" + self.e(g.iter) + ")) { "
                for cond in g.ifs:
                    out += "if (!p.truth(" + self.e(cond) + ")) continue; "
            item = (
                "[" + self.e(n.key) + ", " + self.e(n.value) + "]"
                if isinstance(n, ast.DictComp)
                else self.e(n.elt)
            )
            out += "result.push(" + item + "); " + "}" * len(n.generators)
            out += (
                " return "
                + (
                    "Object.fromEntries(result)"
                    if isinstance(n, ast.DictComp)
                    else "new Set(result)"
                    if isinstance(n, ast.SetComp)
                    else "result"
                )
                + "; })()"
            )
            return out
        if isinstance(n, ast.Call):
            args = [self.e(a) for a in n.args]
            if n.keywords:
                args.append(
                    "p.kw({"
                    + ", ".join(
                        (k.arg + ": " + self.e(k.value)) if k.arg else "..." + self.e(k.value)
                        for k in n.keywords
                    )
                    + "})"
                )
            argtext = ", ".join(args)
            if (
                isinstance(n.func, ast.Attribute)
                and isinstance(n.func.value, ast.Name)
                and n.func.value.id in {"math", "re", "unicodedata"}
            ):
                return "p." + n.func.value.id + "." + n.func.attr + "(" + argtext + ")"
            if isinstance(n.func, ast.Attribute):
                # All methods preserve Python keyword/sequence/string semantics.
                return (
                    "p.method("
                    + self.e(n.func.value)
                    + ", "
                    + json.dumps(n.func.attr)
                    + (", " + argtext if argtext else "")
                    + ")"
                )
            name = self.e(n.func)
            builtins = {
                "len",
                "max",
                "min",
                "sum",
                "round",
                "abs",
                "int",
                "float",
                "str",
                "bool",
                "set",
                "list",
                "dict",
                "tuple",
                "enumerate",
                "zip",
                "range",
                "any",
                "all",
                "sorted",
                "next",
                "getattr",
                "setattr",
                "isinstance",
                "replace",
                "pstdev",
                "combinations",
                "urlsplit",
            }
            if name in builtins:
                name = "p." + name
            if name in {"Builder", "Estilo"}:
                name = "new " + name
            if name in {"ValueError", "DSLException"}:
                name = "new " + ("Error" if name == "ValueError" else name)
            return name + "(" + argtext + ")"
        raise ValueError(ast.dump(n))

    def target(self, n):
        if isinstance(n, (ast.Tuple, ast.List)):
            return "[" + ", ".join(self.target(x) for x in n.elts) + "]"
        if isinstance(n, ast.Subscript):
            return self.e(n.value) + "[" + self.e(n.slice) + "]"
        return self.e(n)

    def block(self, nodes):
        return "\n".join(self.s(n) for n in nodes)

    def s(self, n):
        if isinstance(n, (ast.Import, ast.ImportFrom, ast.Pass)):
            return ""
        if isinstance(n, ast.Expr):
            return (
                ""
                if isinstance(n.value, ast.Constant) and isinstance(n.value.value, str)
                else self.e(n.value) + ";"
            )
        if isinstance(n, (ast.Assign, ast.AnnAssign)):
            if isinstance(n, ast.AnnAssign) and n.value is None:
                return ""
            targets = n.targets if isinstance(n, ast.Assign) else [n.target]
            return "\n".join(
                ("(" + self.target(t) + " = " + self.e(n.value) + ");") for t in targets
            )
        if isinstance(n, ast.AugAssign):
            return self.target(n.target) + " = " + self.e(ast.BinOp(n.target, n.op, n.value)) + ";"
        if isinstance(n, ast.Return):
            return "return " + self.e(n.value) + ";"
        if isinstance(n, ast.If):
            return (
                "if (p.truth("
                + self.e(n.test)
                + ")) {\n"
                + self.block(n.body)
                + "\n}"
                + (" else {\n" + self.block(n.orelse) + "\n}" if n.orelse else "")
            )
        if isinstance(n, ast.For):
            return (
                "for ("
                + self.target(n.target)
                + " of p.iter("
                + self.e(n.iter)
                + ")) {\n"
                + self.block(n.body)
                + "\n}"
            )
        if isinstance(n, ast.While):
            return "while (p.truth(" + self.e(n.test) + ")) {\n" + self.block(n.body) + "\n}"
        if isinstance(n, (ast.Break, ast.Continue)):
            return type(n).__name__.lower() + ";"
        if isinstance(n, ast.FunctionDef):
            return self.function(n)
        if isinstance(n, ast.Try):
            return (
                "try {\n"
                + self.block(n.body)
                + "\n} catch ("
                + (n.handlers[0].name or "exception")
                + ") {\n"
                + self.block(n.handlers[0].body)
                + "\n}"
            )
        if isinstance(n, ast.Raise):
            return "throw " + self.e(n.exc) + ";"
        raise ValueError(ast.dump(n))

    def function(self, n, method=False):
        names = [a.arg for a in n.args.args]
        if method:
            names = names[1:]
        defaults = ["undefined"] * (len(names) - len(n.args.defaults)) + [
            self.e(d) for d in n.args.defaults
        ]
        names += [a.arg for a in n.args.kwonlyargs]
        defaults += [self.e(d) if d else "undefined" for d in n.args.kw_defaults]
        vararg, kwarg = n.args.vararg, n.args.kwarg
        locals_ = set()

        def visit(nodes):
            for node in nodes:
                if isinstance(node, ast.FunctionDef):
                    continue
                if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
                    locals_.add(node.id)
                visit(ast.iter_child_nodes(node))

        visit(n.body)
        locals_ -= set(names) | {"self"}
        isgetter = any(isinstance(d, ast.Name) and d.id == "property" for d in n.decorator_list)
        prefix = ("get " if isgetter else "") + n.name if method else "function " + n.name
        result = prefix + ("()" if isgetter else "(...__args)") + " {\n"
        if not isgetter:
            allnames = names + ([vararg.arg] if vararg else []) + ([kwarg.arg] if kwarg else [])
            result += (
                "var ["
                + ", ".join("defaultValue" if a == "default" else a for a in allnames)
                + "] = p.bind(__args, "
                + json.dumps(names)
                + ", ["
                + ", ".join(defaults)
                + "], "
                + str(bool(vararg)).lower()
                + ", "
                + str(bool(kwarg)).lower()
                + ");\n"
            )
        if locals_:
            result += "var " + ", ".join(sorted(locals_)) + ";\n"
        result += self.block(n.body) + "\n}"
        return result


def main():
    port = Port()
    result = [
        "// @ts-nocheck",
        "// Gerado por scripts/port_core.py a partir das funções puras do compilador.",
        "import * as p from './pythonCompat.js';",
        "import { text_width, text_height, optical_size } from './textMetrics.js';",
        "import { analyze, Diagnostic, DSLException, Command, Position, PresentationNode, SlideNode, Element } from './semantic.js';",
        "import rules from './data/design_rules.json' with { type: 'json' };",
        "import themes from './data/themes.json' with { type: 'json' };",
        "function load_rules() { return rules; }",
    ]
    exports = []
    modules = [
        "geometry",
        "editorial",
        "design_system",
        "design_rules",
        "layout_score",
        "layout_metrics",
        "alto",
        "alto_layout",
    ]
    skip = {"load_rules", "alto_to_dsl", "photo", "variants_for", "capitalize_visible"}
    for module in modules:
        tree = ast.parse((ROOT / "src/slidedsl" / (module + ".py")).read_text(encoding="utf-8-sig"))
        result.append("// Fonte: src/slidedsl/" + module + ".py")
        if module == "alto_layout":
            result.append("var W = WIDTH, H = HEIGHT, M = MARGIN;")
        for node in tree.body:
            if isinstance(node, ast.FunctionDef):
                if (
                    node.name in skip
                    or module == "alto"
                    and node.name
                    not in {"_num", "_digits", "number_tokens", "_norm", "validate_alto"}
                ):
                    continue
                if node.name == "_num":
                    result.append("function _num(v) { return String(v); }")
                    continue
                if node.name == "check_design":
                    node.body[1].value = ast.parse("themes[deck.theme]").body[0].value
                result.append(port.function(node))
                exports.append(node.name)
            elif isinstance(node, ast.ClassDef) and node.name in {"Builder", "Estilo"}:
                fields = [n for n in node.body if isinstance(n, ast.AnnAssign)]
                names = [n.target.id for n in fields]
                defaults = []
                for n in fields:
                    value = n.value
                    if (
                        isinstance(value, ast.Call)
                        and isinstance(value.func, ast.Name)
                        and value.func.id == "field"
                    ):
                        kind = value.keywords[0].value.id
                        defaults.append("[]" if kind == "list" else "{}")
                    else:
                        defaults.append(port.e(value) if value else "undefined")
                code = (
                    "class "
                    + node.name
                    + " {\nconstructor(...args) {\nconst values = p.bind(args, "
                    + json.dumps(names)
                    + ", ["
                    + ", ".join(defaults)
                    + "]);\n"
                )
                code += (
                    "Object.assign(this, Object.fromEntries("
                    + json.dumps(names)
                    + ".map((n,i) => [n,values[i]])));\n}\n"
                )
                code += (
                    "\n".join(
                        port.function(n, True) for n in node.body if isinstance(n, ast.FunctionDef)
                    )
                    + "\n}"
                )
                result.append(code)
                exports.append(node.name)
            elif isinstance(node, (ast.Assign, ast.AnnAssign)):
                if module == "alto" and not any(
                    isinstance(x, ast.Name) and x.id in {"LIMITS", "TEXT_LIMITS", "GENERIC"}
                    for x in ast.walk(node)
                ):
                    continue
                if (
                    module == "geometry"
                    and getattr(node, "targets", [None])[0]
                    and getattr(node.targets[0], "id", "") == "Rect"
                ):
                    continue
                targets = node.targets if isinstance(node, ast.Assign) else [node.target]
                names = [x.id for t in targets for x in ast.walk(t) if isinstance(x, ast.Name)]
                result.append("var " + ", ".join(names) + ";\n" + port.s(node))
                exports += names
    result += [
        "import { photo, variants_for } from './images.js';",
        "export { " + ", ".join(dict.fromkeys(exports)) + " };",
    ]
    code = "\n\n".join(result) + "\n"
    code = code.replace("import * as p from", "import * as __py from")
    code = re.sub(r"\bp\.", "__py.", code)
    OUT.write_text(code, encoding="utf-8")


if __name__ == "__main__":
    main()
