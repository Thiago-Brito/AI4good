# texpace checker
> Deterministic verifier: it owns geometric truth so a model's eyes never assert geometry. Scores claims on definite scenes, O(n²).

The **lift lives here**, not in the grammar (project CONTEXT.md line 13). The checker consumes the AST — a
JSON scene — and scores its **claims**. Setup and actions build the scene; only claims are scored (LEXICON
§0). Every predicate compares against an explicit tolerance; equality is never exact.

## Import surface

`from checker import load_scene, check_scene` — the [`__init__.py`](__init__.py) facade is the only entry.
CLI: `python -m checker <scene.json>` → one line per claim, exit 0 iff every scored claim passes. Try it:
`python -m checker ../examples/office.json`.

## Reading order

| # | File | Owns |
|---|---|---|
| 1 | [scene.py](scene.py) | the IR the checker consumes: entities, poses, keyframes, viewpoints, claims |
| 2 | [loader.py](loader.py) | JSON → `Scene`; rejects a missing header or a non-canonical frame at the door (C1) |
| 3 | [evaluate.py](evaluate.py) | dispatch one claim → its predicate; quantifiers (`none`/`every`/`count`) and the `HOLD` temporal wrapper |
| 4 | [rcc8.py](rcc8.py) · [direction.py](direction.py) · [metrics.py](metrics.py) · [allen.py](allen.py) | the four predicate families: topology · projective direction · distance/orientation · time |
| 5 | [geometry.py](geometry.py) · [vecmath.py](vecmath.py) · [units.py](units.py) · [types.py](types.py) | regions & AABBs · quaternion math (no Euler, C4) · unit-tagged quantities & the ordinal rule (C2) · the intrinsic-front ontology |
| 6 | [report.py](report.py) | the verdict record: PASS / FAIL / **ERROR** / SKIPPED |

## The three verdicts that are not PASS

- **FAIL** — the claim is well-formed and false. A geometric disagreement.
- **ERROR** — the claim is **not evaluable as written**: an ordinal quantity in a metric predicate (C2), a
  projective term with no readable frame (the arity gate, SPEC §1.2), a duration on an ordinal timebase
  (C3). Never silently a FAIL — an unwritable claim is a different fact from a false one.
- **SKIPPED** — a DOF the scene declared `free`. Reported, never scored (LEXICON §1).

## What it checks, and what fell out

The concept-by-concept filter run — which `core` concepts have a working predicate, and the four that were
**demoted** for lacking one — is [`../dsl/CHECKABILITY.md`](../dsl/CHECKABILITY.md). Read it before claiming
"every core concept is checkable": four are not, and it says which.

## Known approximations (honest, not hidden)

- **Regions are AABBs.** A rotated box is bounded by the AABB of its rotated half-extent — exact when
  axis-aligned, conservative otherwise (`geometry.box_region`). Oriented-box overlap is future work.
- **`faces`/`DIST` schematize the figure to its centroid** (foundations §3). A tall object's centroid
  carries a height offset the angle tolerance must absorb — hence `office.json` declares 6° there.
- **Group interpolation of orientation is nearest-keyframe, not slerp.** Positions lerp; orientation snaps
  at the midpoint. Fine for order/topology claims; a slerp is needed before scoring smooth rotation.

## Tests

`python -m pytest tests` from the project root — 39 cases, all green. Fixtures build scenes through the
real loader (`tests/conftest.py`), so the tests exercise the parse path, not a bypass.

<!-- routing:start -->
## Routing

| File | Interface | API | Description |
|------|-----------|-----|-------------|
| [`__init__.py`](__init__.py) | — | — | **facade** — texpace checker facade: the only import surface. Load a scene, score its claims, read the report. |
| [`__main__.py`](__main__.py) | — | — | Module entrypoint so the checker runs as `python -m checker <scene.json>`. |
| [`allen.py`](allen.py) | [`allen.pyi`](allen.pyi) | `relation`, `holds` | Allen's 13 interval relations, with an explicit epsilon. Used twice: over time (tau) and per axis (Rectangle Algebra). |
| [`cli.py`](cli.py) | — | `main` | CLI: `python -m checker <scene.json>` -> the report, exit 0 iff every scored claim passes. |
| [`direction.py`](direction.py) | — | `AnchorError`, `axis_for`, `holds` | DIR: projective direction under the three anchors (world / locale / group), decided by Rectangle Algebra on the anchor axis. |
| [`evaluate.py`](evaluate.py) | — | `check_scene` | Claim evaluation: dispatch one claim to its predicate, with the quantifiers and the temporal wrapper around it. |
| [`geometry.py`](geometry.py) | — | `Aabb`, `box_region`, `sphere_region`, `point_region`, `interval_along` | Regions: the only geometric primitive the checker owns. Shape + pose -> an axis-aligned box, plus its support interval along any axis. |
| [`loader.py`](loader.py) | — | `load_scene`, `scene_from` | JSON scene -> Scene IR. Declarations are mandatory: no frame, no units, no tolerance means no parse (SPEC §0). |
| [`metrics.py`](metrics.py) | — | `PredicateError`, `distance`, `distance_holds`, `compare`, `faces` | Numeric predicates: DIST (point-to-region), and the orientation family (faces / aligned / parallel / perpendicular). |
| [`rcc8.py`](rcc8.py) | [`rcc8.pyi`](rcc8.pyi) | `relation`, `holds` | RCC-8 topology, evaluated numerically on definite scenes (regions, not constraint networks) -> O(1) per pair. |
| [`report.py`](report.py) | [`report.pyi`](report.pyi) | `Verdict`, `CheckReport`, `add`, `scored`, `failures` | The verdict record and the report. The checker's whole output surface: one line per claim, plus the scene's free DOFs. |
| [`scene.py`](scene.py) | — | `SceneError`, `Keyframe`, `Entity`, `Viewpoint`, `Tolerance` | The scene IR the checker actually consumes: entities with pose (possibly keyframed), viewpoints, declarations, claims. |
| [`types.py`](types.py) | [`types.pyi`](types.pyi) | `TypeDef`, `TypeError_`, `Ontology`, `base_ontology`, `add` | The type ontology and the intrinsic-front flag: the one bit that gates locale-anchored direction (LEXICON §6, dsl/TYPES.md). |
| [`units.py`](units.py) | [`units.pyi`](units.pyi) | `UnitTypeError`, `UnitContext`, `kind_of`, `Quantity`, `parse` | Unit-tagged quantities: five unit kinds, canonicalization to metres/seconds, and the ordinal type error (C2, C3). |
| [`vecmath.py`](vecmath.py) | [`vecmath.pyi`](vecmath.pyi) | `add`, `sub`, `scaled`, `dot`, `cross` | Vector and unit-quaternion math in the canonical frame (right-handed, +Z up, +Y forward, +X right). |
<!-- routing:end -->
