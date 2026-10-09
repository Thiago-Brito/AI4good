import {
  Handle,
  Position,
  type NodeProps,
  type Node,
  type Edge,
  type Connection,
} from "@xyflow/react";
import type { Deck } from "./types";

type DomainNode = Node<{
  label: string;
  kind: "presentation" | "slide" | "element" | "group";
  slide?: number;
  id?: string;
}>;
export function DomainCard({ data, selected }: NodeProps<DomainNode>) {
  return (
    <div className={"domain-card " + data.kind + (selected ? " selected" : "")}>
      {data.kind === "slide" && (
        <Handle type="target" position={Position.Left} id="contains_slide" />
      )}
      {(data.kind === "element" || data.kind === "group") && (
        <>
          <Handle
            type="target"
            position={Position.Left}
            id="contains_element"
          />
          <Handle type="target" position={Position.Top} id="spatial" />
        </>
      )}
      <small>
        {data.kind === "presentation"
          ? "Apresentação"
          : data.kind === "slide"
            ? "Slide"
            : data.kind === "group"
              ? "Grupo"
              : "Elemento"}
      </small>
      <strong>{data.label}</strong>
      {data.kind === "presentation" && (
        <Handle type="source" position={Position.Right} id="contains_slide" />
      )}
      {data.kind === "slide" && (
        <Handle type="source" position={Position.Right} id="contains_element" />
      )}
      {(data.kind === "element" || data.kind === "group") && (
        <Handle type="source" position={Position.Bottom} id="spatial" />
      )}
    </div>
  );
}
export function graphFor(deck: Deck): { nodes: DomainNode[]; edges: Edge[] } {
  const nodes: DomainNode[] = [
    {
      id: "presentation",
      type: "domain",
      position: { x: 0, y: 80 },
      data: { label: deck.title, kind: "presentation" },
    },
  ];
  const edges: Edge[] = [];
  let offset = 0;
  for (const s of deck.slides) {
    const id = "slide-" + s.number;
    nodes.push({
      id,
      type: "domain",
      position: { x: 290, y: offset },
      data: { label: "Slide " + s.number, kind: "slide", slide: s.number },
    });
    edges.push({
      id: "p-" + id,
      source: "presentation",
      target: id,
      sourceHandle: "contains_slide",
      targetHandle: "contains_slide",
      label: "contém_slide",
    });
    s.elements.forEach((e, i) => {
      const eid = `s${s.number}:${e.id}`;
      nodes.push({
        id: eid,
        type: "domain",
        position: {
          x: 600 + (i % 2) * 260,
          y: offset + Math.floor(i / 2) * 110,
        },
        data: {
          label: e.id + " • " + e.type,
          kind: "element",
          slide: s.number,
          id: e.id,
        },
      });
      edges.push({
        id: "h-" + eid,
        source: id,
        target: eid,
        sourceHandle: "contains_element",
        targetHandle: "contains_element",
        label: "contém_elemento",
      });
    });
    s.groups.forEach((g, i) => {
      const gid = `s${s.number}:${g.id}`;
      nodes.push({
        id: gid,
        type: "domain",
        position: { x: 1160, y: offset + i * 110 },
        data: {
          label: g.label ?? g.id,
          kind: "group",
          slide: s.number,
          id: g.id,
        },
      });
      edges.push({
        id: "hg-" + gid,
        source: id,
        target: gid,
        sourceHandle: "contains_element",
        targetHandle: "contains_element",
        label: "grupo",
      });
      g.members.forEach((member) =>
        edges.push({
          id: gid + "-" + member,
          source: `s${s.number}:${member}`,
          target: gid,
          sourceHandle: "spatial",
          targetHandle: "spatial",
          label: "membro",
          style: { stroke: "#94a3b8", strokeDasharray: "4 4" },
        }),
      );
    });
    s.relations.forEach((r, i) => {
      const exists = (id: string) =>
        s.elements.some((e) => e.id === id) ||
        s.groups.some((g) => g.id === id);
      if (exists(r.target) && exists(r.reference)) {
        edges.push({
          id: `r-${s.number}-${i}`,
          source: `s${s.number}:${r.reference}`,
          target: `s${s.number}:${r.target}`,
          sourceHandle: "spatial",
          targetHandle: "spatial",
          label: r.kind,
          style: { stroke: "#d97706", strokeWidth: 2 },
        });
      }
    });
    offset += Math.max(
      240,
      Math.ceil(s.elements.length / 2) * 110 + 80,
      s.groups.length * 110 + 80,
    );
  }
  return { nodes, edges };
}
export function validConnection(c: Connection | Edge) {
  if (
    !c.source ||
    !c.target ||
    c.source === c.target ||
    c.sourceHandle !== c.targetHandle
  )
    return false;
  if (c.sourceHandle === "contains_slide")
    return c.source === "presentation" && c.target.startsWith("slide-");
  if (c.sourceHandle === "contains_element")
    return (
      c.source.startsWith("slide-") &&
      c.target.startsWith("s") &&
      c.target.split(":")[0] === c.source.replace("slide-", "s")
    );
  if (c.sourceHandle === "spatial")
    return (
      c.source.includes(":") &&
      c.target.includes(":") &&
      c.source.split(":")[0] === c.target.split(":")[0]
    );
  return false;
}
