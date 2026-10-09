# SPEC: texpace DSL
<!-- Machine-parseable module contract (spec-driven development) + the full language reference below. -->
spec-version: 0
status: locked
verify: make verify-fast

<!-- status: locked  → read-gate armed: editing this module's files requires reading this SPEC first.
     verify: make verify-fast → the ## Examples map to cases in `tests/` (pytest); a broken example
     turns verify:fast red and the commit gate blocks it. Language reference is normative, below. -->

## Inputs
- A **texpace document** in either surface — controlled-English *prose* or *JSON* — over one AST (§Surfaces).
- A mandatory document **header**: `texpace <ver>`, `profile`, `frame`, `units`, `timebase`, `tolerance` (§0). Missing header → does not parse.
- Three line kinds only: `setup` · `action` · `claim` (§"Three kinds of line"). Prose lexicon is **closed** ([LEXICON.md](LEXICON.md)).

## Outputs
- A parsed **AST** (surface-independent) the checker consumes; prose↔JSON are bijective.
- Per `claim`, a deterministic **verdict** from the four predicates `DIR · DIST · TOP · PATH` (§1.3), graded against the declared `tolerance`.
- Parse-time **errors** for arity-gate / article-type / lexicon violations (never silent guesses).

## Invariants
- **Checkability filter:** no concept enters the kernel without a deterministic checker predicate (§1).
- **Closed lexicon:** any phrasing outside [LEXICON.md](LEXICON.md) is a parse error, never an interpretation.
- **Two surfaces, one AST:** a scene emitted to prose and JSON parses back to the *same* canonical form and scores identically (§5 acceptance test).
- **Arity gate at parse time:** `locale` requires an intrinsic-front ground; `group` requires a bound viewpoint — violations are unrepresentable, not mis-scored (§1.2).
- **Only `claim` lines are scored;** `setup`/`action` never reach the checker as primitives (§"Three kinds of line").
- **No Euler storage** (orientation = unit quaternion, C4); ordinal quantities never enter metric predicates (C2); durations illegal on ordinal timebases (C3).
- **Adapter bijection:** a format↔canonical disagreement indicts the adapter, never the checker (§5).

## Examples
- Kernel-only → fully-extended worked scenes: [EXAMPLES.md](EXAMPLES.md) (six, prose surface).
- Predicate conformance is exercised by the suite behind `make verify-fast`: `tests/test_direction.py` (`DIR`), `tests/test_metrics.py` (`DIST`), `tests/test_quantifiers.py` (`none/every/count`), `tests/test_declarations.py` (header/identity/arity).
- Acceptance test (adapter round-trip): a scene → two formats → identical canonical form (§5).

## Notes
Goal: [[spec-driven-development]] · [[spacemantics]]. This SPEC is the module contract; the sections
below are the normative **language reference** it points to. Reading order for the whole `dsl/` module is
in [CONTEXT.md](CONTEXT.md). Companion contracts: [CONFORMANCE.md](CONFORMANCE.md) (adapters), [INVENTORY.md](INVENTORY.md) (per-concept verdicts).

---

# Language Reference (normative) — texpace v1
> Layered spatial+temporal DSL: kernel · modules · profiles · adapters. Every core construct is mechanically checkable.

**Governing principle (from M0.5):** the capability lift comes from the **checker**, not the grammar
surface. So the grammar exists to make claims *addressable and verifiable* — nothing enters the kernel
without a checker predicate. See [INVENTORY.md](INVENTORY.md) for the per-concept verdicts and
[CONFLICTS.md](CONFLICTS.md) for the conventions this spec normalizes.

---

## Surfaces — two, one AST

texpace has **two bijective surfaces** over a single AST. The checker consumes **neither** — it consumes
the AST.

| Surface | For | Defined in |
|---|---|---|
| **prose** — controlled English | humans authoring; models emitting; diffs | [LEXICON.md](LEXICON.md), [GRAMMAR-PROSE.ebnf](GRAMMAR-PROSE.ebnf) |
| **json** — structured interchange | tooling, adapters, programmatic generation | [GRAMMAR-JSON.md](GRAMMAR-JSON.md) |

The prose lexicon is **closed**: a phrasing outside it is a parse error, never a guess. This keeps the
front-end a parser rather than an interpreter.

**Why two.** The evidence says surface syntax is not the lever — swapping drawing languages moves model
accuracy by under 1% — so the surface should be optimized for the consumers who *do* care (humans, diffs,
parsers), and the choice should be *measured* rather than assumed. Prose-vs-JSON is therefore an ablation
axis in the benchmark: it directly tests this project's own claim that the checker, not the notation,
carries the lift.

Worked examples, kernel-only through fully-extended: [EXAMPLES.md](EXAMPLES.md).

**Note on this document.** The predicate names below (`DIR`, `DIST`, `TOP`, `PATH`) and the RCC-8 codes
are the **IR** — the checker's vocabulary. They are *not* what a user writes. Users write prose
(`is inside`, `rests on`, `is left of ... seen from ...`); the lexicon maps it here.

## Three kinds of line

A document has exactly three kinds of line, and the split is what lets texpace express **editing**
(inherently imperative) without giving up **verification** (inherently declarative). See LEXICON §0.

| Kind | Reads like | Ordered? | Role | Scored? |
|---|---|---|---|---|
| **setup** | `use meters and seconds as units.` | — | frame, units, tolerance, profile, viewpoints | no |
| **action** | `add a chair in front of the desk.` | **yes — a program** | how the scene is built or edited | no |
| **claim** | `no two objects overlap.` | no — a set | what must be true of the **final** state | **yes — the only thing scored** |

Actions are the *program*; claims are the *spec*. Verbs desugar into `create` + `constrain` (LEXICON §3),
so nothing an action does reaches the checker as a new primitive — the checker sees only the final scene
and the claim set. This is why generation and verification share one language: a generation task is a claim
set with the scene unbuilt; a verification task is the same claim set over a scene that already exists.

**Articles are a type system on identity.** `a`/`an` **introduces** (legal only with `add`/`create`); `the`
**refers** (required by `move`/`delete`/`rotate` and every claim). `move a ball` is a **parse error**, never
a silent create — silent creation forks the scene invisibly and surfaces the error far away. `the ball` is
legal only if exactly one ball exists. This is checked at parse time, not scored. Full rules: LEXICON §2.

## 0. Document header (mandatory)

Nothing is implicit. A document that omits a header does not parse.

```
texpace 1.0
profile   3d                                          # 2d | 2.5d | 3d | 4d
frame     { handedness: right, up: +Z, forward: +Y, origin: site_datum }
units     { length: m, angle: rad }
timebase  seconds                                     # seconds | frames@fps | steps | months
tolerance { length: 5mm, angle: 0.5deg, iou: 0.9 }
```

`tolerance` is **not optional**: without it, "aligned" is not a verifiable claim. Every predicate is
evaluated against the declared epsilon.

## 1. Kernel

All of it deterministically checkable. This is the whole of what `core` means.

### 1.1 Entities, identity, semantic type

```
entity desk  : furniture { extent: 1.6m 0.8m 0.75m }   # furniture has an intrinsic front
entity ball  : prop      { radius: 0.1m }              # prop has NO intrinsic front
```

The **semantic type carries the intrinsic-orientation flag**, and that flag *is* the locale-anchor gate
(§1.2). Geometry primitives: `point · vector · segment · polyline · curve · polygon · bbox · volume ·
mesh-ref`. Transform = position + **orientation (unit quaternion)** + scale. Euler degrees are never
stored (C4).

### 1.2 Anchors and the arity gate

Three anchors, from Levinson's frames of reference:

| Anchor | Origin | Arity | Valid when |
|---|---|---|---|
| `world` | declared datum / global axes | binary `(figure, ground)` | always |
| `locale` | on the ground object, from its own facets | binary | **iff the ground has an intrinsic front** |
| `group` | on a viewer, projected onto the ground | **ternary `(figure, ground, viewpoint)`** | **iff a viewpoint is bound** |

```
viewpoint door : camera { position: 4m 0m 1.6m, look_at: desk }

assert DIR(chair, desk, front, locale)                     # ok: desk is furniture
assert DIR(chair, desk, left,  group{viewpoint: door})     # ok: viewpoint bound
assert DIR(chair, ball, front, locale)                     # PARSE ERROR: ball has no front
assert DIR(chair, desk, left,  group)                      # PARSE ERROR: arity gate
```

**The arity gate is enforced at parse time, not scored at check time.** Underspecified viewpoint is the
single most common real-world spatial ambiguity; texpace makes it unrepresentable rather than wrong.
`group` additionally carries `transform: reflected | rotated | translated` (default `reflected`, the
English convention) so cross-convention statements remain scorable.

### 1.3 The four predicates

| Predicate | Meaning | Checked by |
|---|---|---|
| `DIR(fig, gnd, axis, anchor)` | projective direction | Rectangle Algebra (one Allen relation per axis); AVS-graded acceptability near axis boundaries |
| `DIST(fig, gnd) <op> q` | metric / proximity | numeric distance vs tolerance |
| `TOP(a, b, rcc)` | topology: containment, contact, overlap | RCC-8 `{DC, EC, PO, TPP, TPP-i, NTPP, NTPP-i, EQ}` |
| `PATH(fig, gnd, shape, τ)` | motion / trajectory | per-frame relations + trajectory error |

Everything in the spatial lexicon is a parametrization of these four (foundations §3): `in/inside` =
`TOP(..., NTPP)`; `on/touching` = `TOP(..., EC)`; `near/next-to` = `DIST < θ`; `aligned/parallel/facing`
= `DIR` angles over object axes; `into` = `PATH ⇒ Finally TOP(inside)`.

**Checks run on definite scenes by numeric grounding** — O(n²), no NP-hardness touched. (Optional
spec-consistency checking via path-consistency is confined to the tractable fragments: RCC-8 Ĥ₈/C₈/Q₈,
Allen ORD-Horn.)

### 1.4 Assertions vs constraints

Same predicates, two modes — the distinction the v0 core lacked:

```
assert    TOP(lamp, desk, EC)          # a FACT to verify   (checker scores it)
constrain DIST(chair, desk) < 0.6m     # a GOAL to satisfy  (solver/model must achieve it)
```

### 1.5 Negation, quantification, selectors

Without these a checker **gets gamed** (M0.5 Q5: a baseline silently deleted objects while passing every
geometric check). Coverage and negative constraints are therefore kernel, not optional.

```
select chairs = entities where type == furniture and name ~ "chair*"

assert none  ( TOP(a, b, PO) for a, b in entities )        # no two objects overlap
assert every ( DIR(c, desk, front, locale) for c in chairs )
assert count ( chairs ) == 4                               # coverage: nothing vanished
```

### 1.6 Underspecification

```
free chair.position.z        # explicitly unconstrained — the checker will not score it
```
A generation task states what must hold; everything else is free *by declaration*, never by silence.

### 1.7 Time

```
assert AT(1.2s)      DIR(ball, box, left, world)
assert OVER([0s,1.2s]) TOP(ball, box, DC)          # never touches the box
assert PATH(ball, box, behind) BEFORE stop(ball)   # Allen: before|meets|overlaps|during|...
HOLD( TOP(lid, jar, EC), 3s )                      # invariant over an interval
```

Temporal relations are **Allen's 13**. On an **ordinal** timebase (`steps`), durations do not exist:
`HOLD(pred, Δ)` is a **type error**, and only order relations are legal (C3). Likewise an **ordinal**
length (CV depth, z-rank) may never appear in a metric predicate (C2).

## 2. Modules (optional; a profile declares which are live)

| Module | Provides | Checkable? |
|---|---|---|
| `camera` | cameras, viewpoints, FOV, line-of-sight, projection (perspective / orthographic / isometric-dimetric), clipping planes | yes — LOS + frustum are geometric tests |
| `depth` | z-order, occlusion, depth maps. **Depth is DERIVED from position + camera, never authored** (C6); `layer`/`priority` only as an explicit tie-break | yes — derived order compared to reference |
| `hierarchy` | grouping, scene/canvas trees, transform inheritance | yes — composed transforms |
| `parametric` | variables, expressions, **spatial arrays** with per-instance overrides | yes — expanded then checked |
| `timeline` | keyframes, checkpoints, transitions, easing/interpolation, events | yes — sampled per frame + Allen |
| `appearance` | materials, colour, texture | **advisory** — not scored |
| `physics` | gravity, rigid bodies, collision, **rigging/skinning** | **advisory / outcome-checked only** (§3) |

### 2.1 Spatial arrays (the v0 gap — casinhas)

```
param  W = 3.45m
module casa { entity wall_n : wall {...}  entity laje : slab {...} }

array houses of casa count 7 along +X spacing W
  override [6] { kind: corner_unit }

assert every( TOP(h.laje, terrain, EC) for h in houses )
assert count( houses ) == 7
```
Instances get stable identities (`houses[3]`) that selectors can address. Distinct from the **temporal**
`REPEAT(action, N)` — conflating the two was the v0 gap (C5).

## 3. Physics: advisory, outcome-checked

No open format declaratively encodes physics, and simulation is not deterministic across engines. So
physics is **expressible and executable, but never scored directly**. Only *observables* are checked:

```
physics { engine: bullet, gravity: -9.81 }     # advisory: executed, NOT scored

assert OUTCOME at rest   TOP(ball, shelf, EC)                    # observable post-condition
assert OUTCOME event contact(ball, box) BEFORE contact(ball, shelf)   # Allen over events
```
Rest positions, contact events and their Allen ordering are observable and checkable within tolerance;
the simulation's internals are not. Rigging/skinning is the same: the **posed result** is checkable, the
rig is advisory.

## 4. Profiles

| Profile | Live modules | Canonical formats |
|---|---|---|
| `2d` | camera(ortho) · depth · hierarchy · parametric · appearance* | SVG, PPTX |
| `2.5d` | + isometric projection, explicit depth/occlusion | Tiled TMX, SVG(iso) |
| `3d` | + full camera, volumes | glTF, IFC |
| `4d` | + timeline (and physics*) | Lottie, glTF-animation |

\* advisory.

## 5. Adapters

An adapter is a **bijection between a format and canonical form**. It must declare its conformance level
and its native conventions (up-axis, handedness, units, time base) — see [CONFORMANCE.md](CONFORMANCE.md).

**The acceptance test:** a scene emitted to two formats must parse back to the same canonical form and
therefore score **identically**. A disagreement indicts the adapter, never the checker.
