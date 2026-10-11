"""Conservative three-way scene merge by stable ID, with observable conflicts."""

from copy import deepcopy

from .ir import Presentation
from .semantic import validate_ir
from .visual_validation import check_visual


def merged_source(deck, previous_source):
    """Retain actual front/back instructions; restore the edited final z order."""
    from .ast_nodes import Command
    from .parser import parse
    from .printer import print_ast
    from .serializer import ir_to_ast
    from .diagnostics import DSLException

    ast = ir_to_ast(deck)
    try:
        previous = parse(previous_source) if previous_source else None
    except DSLException:
        previous = None
    if previous:

        def flatten(commands):
            for command in commands:
                if command.op == "layout":
                    yield from flatten(command.children)
                else:
                    yield command

        for scene, node in zip(deck.slides, ast.slides, strict=True):
            prior = next((s for s in previous.slides if s.number == scene.number), None)
            ids = {e.id for e in scene.elements} | {g.id for g in scene.groups}
            operations = (
                [
                    deepcopy(c)
                    for c in flatten(prior.commands)
                    if c.op in {"back", "front"} and c.id in ids
                ]
                if prior
                else []
            )
            if operations:
                node.commands.extend(operations)
                node.commands.extend(
                    Command(op="layer", id=e.id, value=e.z)
                    for e in sorted(scene.elements, key=lambda e: e.z)
                )
    return print_ast(ast)


def merge_manual(base, current, candidate):
    for data in (base, current, candidate):
        Presentation.model_validate(data)
    if not (len(base["slides"]) == len(current["slides"]) == len(candidate["slides"])):
        return deepcopy(current), [
            {"conflict": "Quantidade de slides mudou; sincronização manual necessária."}
        ]
    merged, changes = deepcopy(candidate), []
    for key in ("title", "theme"):
        if current[key] != base[key]:
            merged[key] = current[key]
            changes.append({"field": key, "decision": "manual preserved"})
    for old, edited, new in zip(base["slides"], current["slides"], merged["slides"], strict=True):
        before = {e["id"]: e for e in old["elements"]}
        manual = {e["id"]: e for e in edited["elements"]}
        generated = {e["id"]: e for e in new["elements"]}
        removed = before.keys() - manual.keys()
        for id in removed:
            generated.pop(id, None)
            changes.append(
                {"slide": old["number"], "element": id, "decision": "manual removal preserved"}
            )
        for id, element in manual.items():
            if id not in before:
                if id in generated and generated[id] != element:
                    return deepcopy(current), [
                        {"element": id, "conflict": "ID de adição manual colide com reparo."}
                    ]
                generated[id] = deepcopy(element)
                changes.append({"element": id, "decision": "manual addition preserved"})
                continue
            fields = [k for k in element if element.get(k) != before[id].get(k)]
            if fields and id not in generated:
                return deepcopy(current), [
                    {"element": id, "conflict": "Reparo removeu elemento editado."}
                ]
            for key in fields:
                target = generated[id]
                conflict = target.get(key) != before[id].get(key) and target.get(
                    key
                ) != element.get(key)
                changes.append(
                    {
                        "element": id,
                        "field": key,
                        "decision": "manual preserved",
                        "conflict": conflict,
                    }
                )
                target[key] = deepcopy(element[key])
        new["elements"] = list(generated.values())
        # Manual groups and relations are protected too, including deleted members.
        for key in ("groups", "relations"):
            if old[key] != edited[key]:
                new[key] = deepcopy(edited[key])
                changes.append(
                    {"slide": old["number"], "field": key, "decision": "manual preserved"}
                )
        new["groups"] = [g for g in new["groups"] if all(id in generated for id in g["members"])]
        new["relations"] = [
            r
            for r in new["relations"]
            if r["target"] not in removed and r["reference"] not in removed
        ]
        # Stable sort retains edited z order; gaps/duplicate z become canonical ranks.
        new["elements"].sort(key=lambda e: e["z"])
        for z, element in enumerate(new["elements"]):
            element["z"] = z
    deck = Presentation.model_validate(merged)
    if validate_ir(deck) or any(d["severity"] == "ERRO" for d in check_visual(deck)):
        return deepcopy(current), changes + [
            {"conflict": "Cena combinada inválida; edição atual preservada e reparo descartado."}
        ]
    return merged, changes
