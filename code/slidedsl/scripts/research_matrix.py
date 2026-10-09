"""Materializar a matriz de evidências consultadas; não executa APIs externas."""

import csv
from pathlib import Path

DATE = "2026-10-08"
PPT = "https://gitbrent.github.io/PptxGenJS/docs/"
COM = "https://learn.microsoft.com/en-us/office/vba/api/powerpoint."
CAN = "https://www.canva.dev/docs/apps/"
GGL = "https://developers.google.com/workspace/slides/api/"
operations = [
    "criar apresentação",
    "adicionar slide",
    "remover slide",
    "adicionar texto",
    "remover texto",
    "adicionar forma",
    "remover forma",
    "inserir imagem",
    "mover",
    "redimensionar",
    "trocar cor",
    "alinhar",
    "agrupar",
    "camadas",
    "exportar PPTX",
    "editar documento existente",
    "execução offline",
]
columns = [
    "PptxGenJS",
    "PowerPoint COM",
    "Canva CLI/REST",
    "Canva Apps SDK",
    "Canva MCP",
    "Google Slides API",
]


def cell(status, op, url, tested=False):
    return f"{status} | {op} | {url} | {DATE} | {'VERIFICADO' if tested else 'DOCUMENTADO; NAO_TESTADO'}"


def build():
    rows = []
    for op in operations:
        ppt_op = {
            "criar apresentação": "new PptxGenJS",
            "adicionar slide": "addSlide",
            "adicionar texto": "addText",
            "adicionar forma": "addShape",
            "inserir imagem": "addImage",
            "mover": "x/y ao gerar",
            "redimensionar": "w/h ao gerar",
            "trocar cor": "color/fill ao gerar",
            "alinhar": "x/y calculados pela IR",
            "camadas": "sequência add*",
            "exportar PPTX": "writeFile",
            "execução offline": "Node local",
        }
        p = cell(
            "SIM" if op in ppt_op else "NÃO",
            ppt_op.get(op, "não há importação/edição pública; refazer IR"),
            PPT
            + (
                {
                    "adicionar texto": "api-text/",
                    "inserir imagem": "api-images/",
                    "adicionar forma": "api-shapes/",
                }.get(op, "usage/")
            ),
            tested=op in ppt_op,
        )
        com_op = {
            "criar apresentação": "Presentations.Add",
            "adicionar slide": "Slides.Add",
            "remover slide": "Slide.Delete",
            "adicionar texto": "Shapes.AddTextbox",
            "remover texto": "TextRange.Delete/Shape.Delete",
            "adicionar forma": "Shapes.AddShape",
            "remover forma": "Shape.Delete",
            "inserir imagem": "Shapes.AddPicture",
            "mover": "Shape.Left/Top",
            "redimensionar": "Shape.Width/Height",
            "trocar cor": "Shape.Fill/Font.Color",
            "alinhar": "ShapeRange.Align",
            "agrupar": "ShapeRange.Group",
            "camadas": "Shape.ZOrder",
            "exportar PPTX": "Presentation.SaveAs",
            "editar documento existente": "Presentations.Open",
            "execução offline": "PowerPoint desktop instalado",
        }[op]
        c = cell(
            "SIM",
            com_op,
            COM
            + (
                {
                    "alinhar": "shaperange.align",
                    "agrupar": "shaperange.group",
                    "camadas": "shape.zorder",
                    "remover slide": "slide.delete",
                    "exportar PPTX": "presentation.saveas",
                }.get(op)
                or (
                    "shapes"
                    if op.startswith("adicionar") or op == "inserir imagem"
                    else "presentation"
                    if op
                    in [
                        "criar apresentação",
                        "exportar PPTX",
                        "editar documento existente",
                        "execução offline",
                    ]
                    else "shape"
                )
            ),
        )
        rest = cell(
            "NÃO CONFIRMADO",
            "operação por elemento não demonstrada",
            CAN + "canva-cli/making-rest-api-requests/",
        )
        if op == "criar apresentação":
            rest = cell(
                "SIM",
                "canva api designs create / POST designs",
                CAN + "rest-apis/reference/designs/create-design/",
            )
        elif op == "exportar PPTX":
            rest = cell(
                "SIM",
                "POST exports; format.type=pptx",
                CAN + "rest-apis/reference/exports/create-design-export-job/",
            )
        elif op == "execução offline":
            rest = cell("NÃO", "REST requer serviço", CAN + "canva-cli/making-rest-api-requests/")
        sdk = cell(
            "PARCIAL",
            "openDesign: tipos e contextos suportados; dentro de app",
            CAN + "design-editing/",
        )
        if op == "execução offline":
            sdk = cell("NÃO", "contexto Canva conectado", CAN + "design-editing/")
        elif op == "agrupar":
            sdk = cell("SIM", "session.helpers.group/ungroup", CAN + "design-editing/")
        mcp = cell(
            "NÃO CONFIRMADO",
            "catálogo não demonstra edição elementar irrestrita",
            CAN + "mcp/tools/",
        )
        if op == "criar apresentação":
            mcp = cell("SIM", "create-design / generate-design", CAN + "mcp/tools/")
        elif op == "exportar PPTX":
            mcp = cell("PARCIAL", "export-design; consultar get-export-formats", CAN + "mcp/tools/")
        elif op == "execução offline":
            mcp = cell("NÃO", "serviço remoto autenticado", CAN + "mcp/")
        g_op = {
            "criar apresentação": "presentations.create",
            "adicionar slide": "createSlide",
            "remover slide": "deleteObject",
            "adicionar texto": "createShape TEXT_BOX + insertText",
            "remover texto": "deleteText/deleteObject",
            "adicionar forma": "createShape",
            "remover forma": "deleteObject",
            "inserir imagem": "createImage (URL acessível)",
            "mover": "updatePageElementTransform",
            "redimensionar": "updatePageElementTransform",
            "trocar cor": "updateShapeProperties/updateTextStyle",
            "alinhar": "transform calculada",
            "agrupar": "groupObjects",
            "camadas": "updatePageElementsZOrder",
            "exportar PPTX": "Drive files.export",
            "editar documento existente": "presentations.batchUpdate",
            "execução offline": "API exige rede",
        }[op]
        g = cell(
            "NÃO"
            if op == "execução offline"
            else "PARCIAL"
            if op in ["alinhar", "exportar PPTX"]
            else "SIM",
            g_op,
            "https://developers.google.com/workspace/drive/api/guides/ref-export-formats"
            if op == "exportar PPTX"
            else GGL
            + (
                "reference/rest/v1/presentations/create"
                if op == "criar apresentação"
                else "reference/rest/v1/presentations/request"
            ),
        )
        rows.append([op, p, c, rest, sdk, mcp, g])
    with Path("docs/MATRIZ_CAPACIDADES.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["operação", *columns])
        w.writerows(rows)


if __name__ == "__main__":
    build()
