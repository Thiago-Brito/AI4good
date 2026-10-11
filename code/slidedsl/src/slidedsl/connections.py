"""Native OOXML anchoring for explicitly declared source -> arrow -> target chains."""

from io import BytesIO
import xml.etree.ElementTree as ET
import zipfile

NS = {
    "p": "http://schemas.openxmlformats.org/presentationml/2006/main",
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
}
for prefix, uri in NS.items():
    ET.register_namespace(prefix, uri)


def anchored_connections(slide):
    elements = {e.id: e for e in slide.elements}
    result = {}
    for arrow in slide.elements:
        if arrow.type != "arrow":
            continue
        sources = [
            r.reference for r in slide.relations if r.kind == "below" and r.target == arrow.id
        ]
        targets = [
            r.target for r in slide.relations if r.kind == "below" and r.reference == arrow.id
        ]
        if len(sources) != 1 or len(targets) != 1:
            continue
        a, b = elements.get(sources[0]), elements.get(targets[0])
        if a is None or b is None or a.type != "rectangle" or b.type != "rectangle" or a.id == b.id:
            continue
        # Only vertical ordered links are supported; no invented routing.
        if abs(a.x + a.width / 2 - b.x - b.width / 2) > 1 or b.y < a.y + a.height:
            continue
        result[arrow.id] = (a, b)
    return result


def anchor_pptx(file, deck):
    edits = {}
    with zipfile.ZipFile(file) as archive:
        for slide in deck.slides:
            links = anchored_connections(slide)
            if not links:
                continue
            name = f"ppt/slides/slide{slide.number}.xml"
            root = ET.fromstring(archive.read(name))
            objects = {}
            for obj in root.find("p:cSld/p:spTree", NS):
                ident = obj.find(".//p:cNvPr", NS)
                if ident is not None:
                    objects[ident.get("name")] = (obj, ident.get("id"))
            for arrow, (a, b) in links.items():
                obj, ident = objects[arrow]
                nv = obj.find("p:nvSpPr", NS)
                if nv is None:
                    raise ValueError("Connector source is not a native shape")
                obj.tag = f"{{{NS['p']}}}cxnSp"
                nv.tag = f"{{{NS['p']}}}nvCxnSpPr"
                props = nv.find("p:cNvSpPr", NS)
                props.tag = f"{{{NS['p']}}}cNvCxnSpPr"
                props.attrib.clear()
                ET.SubElement(props, f"{{{NS['a']}}}stCxn", id=objects[a.id][1], idx="2")
                ET.SubElement(props, f"{{{NS['a']}}}endCxn", id=objects[b.id][1], idx="0")
                shape = obj.find("p:spPr", NS)
                shape.find("a:prstGeom", NS).set("prst", "line")
                for fill in list(shape):
                    if fill.tag in {f"{{{NS['a']}}}solidFill", f"{{{NS['a']}}}noFill"}:
                        shape.remove(fill)
                shape.insert(2, ET.Element(f"{{{NS['a']}}}noFill"))
                line = shape.find("a:ln", NS)
                if line is None:
                    line = ET.SubElement(shape, f"{{{NS['a']}}}ln")
                line.clear()
                line.set("w", "25400")
                color = ET.SubElement(line, f"{{{NS['a']}}}solidFill")
                e = next(e for e in slide.elements if e.id == arrow)
                ET.SubElement(color, f"{{{NS['a']}}}srgbClr", val=e.color[1:])
                ET.SubElement(line, f"{{{NS['a']}}}tailEnd", type="triangle")
                xfrm = shape.find("a:xfrm", NS)
                xfrm.find("a:off", NS).attrib.update(
                    x=str(round((a.x + a.width / 2) * 9525)), y=str(round((a.y + a.height) * 9525))
                )
                xfrm.find("a:ext", NS).attrib.update(
                    cx="0", cy=str(round((b.y - a.y - a.height) * 9525))
                )
                tx = obj.find("p:txBody", NS)
                if tx is not None:
                    obj.remove(tx)
            edits[name] = ET.tostring(root, encoding="utf-8", xml_declaration=True)
        if not edits:
            return 0
        output = BytesIO()
        with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as target:
            for info in archive.infolist():
                target.writestr(info, edits.get(info.filename, archive.read(info.filename)))
    file.write_bytes(output.getvalue())
    return len(edits)
