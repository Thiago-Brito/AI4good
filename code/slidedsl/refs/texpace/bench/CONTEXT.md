# bench
> The WITH/WITHOUT pilot: does the checker-in-the-loop lift a model's spatial placement? Same tasks, same scorer, three arms.
> spec: none
> goal: [spacemantics](../../../brain/goals/spacemantics.md)

**What this measures.** The project's thesis is that the *checker*, not the notation, carries the lift
(surface syntax moves accuracy <1%, [CHECKABILITY.md](../dsl/CHECKABILITY.md)). So the pilot holds the
output format constant (the model emits a JSON pose per object) and toggles the **checker feedback loop**:

| Arm | What the model gets | Isolates |
|---|---|---|
| **SVG** | one shot of *raw SVG* (2D suites only), parsed back for scoring | baseline in the raw target format, no DSL at all |
| **WITHOUT** | one shot, no feedback | baseline spatial capability (JSON poses) |
| **blind** | *k* attempts, retried with "try again" and no detail | the value of *extra tries alone* (the control) |
| **WITH** | *k* attempts, each retry carries the checker's per-claim verdicts | the value of **verifiable feedback** |

The SVG arm's parsed poses are **anchor-aligned before scoring** (rigid translation onto the drawn fixed
anchors, `scoring.align_to_anchors`): the claims are relation-level, so grading the model on its choice of
SVG origin would measure bookkeeping, not spatial capability. Retries are single-turn: every retry prompt
re-carries the full task plus the model's previous answer (`arms._next_prompt`).

`WITH − blind` is the honest lift: the improvement that is the checker's feedback, not just more attempts.
`blind − WITHOUT` is what retries alone buy. The checker is the **scorer for all three arms** — that is the
whole point: it owns geometric truth, so it grades the baseline and drives the loop with the same predicates.

## Run

```bash
python -m bench.run --model claude-cli:haiku --tasks tasks_2d.json --k 3   # subscription, no API key
python -m bench.run --model opencode:nvidia/z-ai/glm-5.2 --tasks tasks_2d.json --k 3
GEMINI_API_KEY=... python -m bench.run --k 3            # HTTP transport, 3D task set
python -m bench.run --limit 2 --k 3                     # smoke test
```

Providers: `claude-cli` (local `claude -p`, any alias/model id it accepts: haiku, sonnet, opus, …),
`opencode` (local `opencode run`, model id is opencode's `provider/model` path), `gemini` (HTTP, needs
`GEMINI_API_KEY`). CLI transports run from a neutral cwd so no workspace instructions leak into the
completion; they ignore `temperature`. Both retry on a transient failure (`CLI_RETRIES`, backoff).

**opencode always runs under the `plan` agent** (`cli_transport.OPENCODE_AGENT`), never the default
`build` agent — `build` has blanket `*` tool permissions and *will* invoke Write/Bash mid-completion
instead of just replying with text (observed: it wrote stray `.svg` files into the repo root). Do not
drop this pin without re-verifying no tool use survives a completion.

Writes `results-<model>.json` (one per model); prints a per-task row + a summary (claims-passed % and
tasks-solved %).

## Files

| File | Owns |
|---|---|
| [tasks.json](tasks.json) · [tasks_hard.json](tasks_hard.json) | 3D pilot task sets — NL prompt + fixed anchors + **ground-truth claims** (the spec) |
| [tasks_2d.json](tasks_2d.json) | the 2D suite (UI/floor-plan layouts, mostly dense L2/L3) — the only suite the raw-SVG arm runs on |
| [model_client.py](model_client.py) | provider-agnostic completion; provider is data, one branch per transport |
| [cli_transport.py](cli_transport.py) | the two local-CLI transports (`claude -p`, `opencode run`), neutral cwd, ANSI-stripped |
| [prompts.py](prompts.py) | the message builders (task / SVG task / blind-retry / checker-feedback) + the pose extractor |
| [scoring.py](scoring.py) | build a scene from the model's poses, score it with the checker (shared by all arms) + anchor alignment |
| [arms.py](arms.py) | the four arms as a single loop parametrized by feedback on/off + extractor |
| [run.py](run.py) | orchestrate arms × tasks, print the table, write `results-<model>.json` |

## Honesty notes

- **Tolerances are generous** (5 cm / 10° in 3D, 3 cm in the 2D suite) so the signal is *getting the
  relation right*, not sub-mm precision. Tightening them is a separate difficulty axis.
- The 2D suite is weighted toward dense L2/L3 scenes on purpose: the earlier easy pilot showed a strong
  model has no headroom on simple scenes at generous tolerance — the lift can only show where the
  baseline breaks.
- This is a **pilot**, not the M2 benchmark: hand-built tasks (8 per suite), no glTF round-trip yet. It
  exists to see the WITH/WITHOUT signal early, on real model calls, scored by the real checker.

<!-- routing:start -->
## Routing

| File | Interface | API | Description |
|------|-----------|-----|-------------|
| [`__init__.py`](__init__.py) | — | — | **facade** — bench facade: the pilot WITH/WITHOUT harness. Load tasks, run arms against a model, score via the checker. |
| [`arms.py`](arms.py) | — | `ArmResult`, `run_without`, `run_without_svg`, `run_blind`, `run_with` | The three experimental arms: WITHOUT (one-shot), blind-retry (control), WITH (checker feedback loop). |
| [`cli_transport.py`](cli_transport.py) | — | `CliError`, `run_claude_cli`, `run_opencode` | Transports that shell out to local agent CLIs (claude -p, opencode run). Keeps model_client HTTP-only. |
| [`model_client.py`](model_client.py) | [`model_client.pyi`](model_client.pyi) | `Model`, `ModelError`, `complete`, `label` | Provider-agnostic text-completion client. Provider is data (a string), never baked into a file/verb name. |
| [`prompts.py`](prompts.py) | — | `build_task_prompt`, `build_svg_task_prompt`, `build_blind_retry`, `build_feedback`, `extract_poses` | The three message builders (task prompt, blind-retry nudge, checker feedback) and the pose extractor. |
| [`report.py`](report.py) | — | `main` | Aggregate results-<model>.json files into one cross-model table, with the honest lift (WITH - blind). |
| [`run.py`](run.py) | — | `main` | Pilot runner: run WITHOUT / blind / WITH across the task set, print the results table, write results.json. |
| [`scoring.py`](scoring.py) | — | `ScoreResult`, `build_document`, `align_to_anchors`, `score_poses`, `fraction` | Score a model's placement: build a texpace document from the task + the model's poses, then run the checker. |
<!-- routing:end -->
