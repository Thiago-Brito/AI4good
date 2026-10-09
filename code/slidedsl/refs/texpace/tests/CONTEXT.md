# tests
> ← add description

<!-- routing:start -->
## Routing

| File | Interface | API | Description |
|------|-----------|-----|-------------|
| [`conftest.py`](conftest.py) | [`conftest.pyi`](conftest.pyi) | `build`, `make_scene`, `degrees` | Scene fixtures: a definite desk/chair/lamp/ball scene in canonical form, built through the loader. |
| [`test_declarations.py`](test_declarations.py) | [`test_declarations.pyi`](test_declarations.pyi) | `document_without` | The header is mandatory: no frame, no tolerance, no non-canonical frames. Plus the user-extensible type ontology. |
| [`test_direction.py`](test_direction.py) | [`test_direction.pyi`](test_direction.pyi) | `verdicts` | DIR under the three anchors, and the arity gate: an unreadable projective term is an ERROR, never a FAIL. |
| [`test_metrics.py`](test_metrics.py) | [`test_metrics.pyi`](test_metrics.pyi) | `only` | DIST, faces, alignment — and the ordinal rule: rank may never enter a metric predicate (C2). |
| [`test_profile_2d.py`](test_profile_2d.py) | [`test_profile_2d.pyi`](test_profile_2d.pyi) | `widget`, `build` | The 2D profile: the plane is XY viewed from +Z, so "above" means +Y and topology ignores the degenerate Z (C1). |
| [`test_quantifiers.py`](test_quantifiers.py) | [`test_quantifiers.pyi`](test_quantifiers.pyi) | `only` | Coverage and negation: without them a checker gets gamed (a baseline "solved" scenes by deleting objects). |
| [`test_svg_parse.py`](test_svg_parse.py) | [`test_svg_parse.pyi`](test_svg_parse.pyi) | — | SVG round-trip: the emitter's output parses back to the same positions, and plain metre-unit SVG parses too. |
| [`test_temporal.py`](test_temporal.py) | [`test_temporal.pyi`](test_temporal.pyi) | `scene_with` | Time: keyframed poses, HOLD as a sampled invariant, Allen over events — and the ordinal-timebase type error (C3). |
| [`test_topology.py`](test_topology.py) | [`test_topology.pyi`](test_topology.pyi) | `box` | RCC-8 must produce all eight codes on definite regions, and 'is inside' must genuinely differ from 'is within'. |
<!-- routing:end -->
