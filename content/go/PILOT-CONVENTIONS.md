# Pilot content conventions — Go concurrency-discrimination vertical (Phase 0)

Binding for every lesson under `content/go/`. The field vocabulary is the canonical schema at
[`../examples/go04-concurrency-discrimination.yaml`](../examples/go04-concurrency-discrimination.yaml)
— copy its field names, never invent competitors. This file adds only what Phase 0 needs to make
every lesson **executable** by `pilot/pilot.py` (the canonical example is a design-time sketch;
pilot lessons must actually run). Verify with `make verify ID=<lesson-id>` — zero errors or the
lesson does not ship.

## File & identity

- One lesson per file: `content/go/<id>.yaml`; filename stem MUST equal `id`.
- `id` = `<tag>-<slug>` (e.g. `go04a-channel-ownership`, tag `go04a`). Tags `go04a`–`go04g`
  are the M4 half (goroutines/channels/select/context), `go05a`–`go05g` the M5 half (sync
  primitives & memory model).
- `schema_version: 1`, `content_rev: 1` (int; bump on any edit), `track: go`,
  `toolchain: { go: "1.26" }` (the installed toolchain this content is verified against, R10).
- `prerequisites` may only name lesson ids that exist in `content/go/` (the pilot DAG is
  self-contained; `verify` rejects dangling ids).
- `altitude`: `on_ramp` for the two entry lessons, `ramp` otherwise. `priority: attack`.
- Objectives: 2–3 per lesson, ids `<tag>-oN`, `bloom` ∈ analyze/evaluate/create only.
- Coverage-closure is enforced: every objective id appears in ≥1 `teach`/`worked_examples`
  `covers` AND ≥1 `assessments[].covers`; no `covers` id may be undeclared.
- `limitations` is required — name what a green run does NOT prove.
- 3–4 assessments per lesson. Prefer mixing strategies; every lesson needs ≥1 item that is
  NOT `deterministic_choice`.

## Executable-code rules (differences from the design-time sketch)

All embedded Go is **complete files**, stdlib only (the runner sets `GOPROXY=off` — any
external import fails the build; `go.uber.org/goleak` is rejected for this reason, use
`runtime.NumGoroutine()` drain assertions with a retry loop instead).

1. **`hidden_tests`** (`code_from_scratch` / `code_completion` / `debug_this`):
   - `grading.test_code` (pilot-additive field): one complete `_test.go` file,
     `package crucible`, containing every test named in the `tests:` metadata list.
   - `grading.starter`, `grading.reference_solution`, and (debug_this) `grading.buggy` are
     complete files in `package crucible` with their own imports. The learner edits a copy of
     starter/buggy; tests are compiled next to it in the same package.
   - `tests:` metadata keeps `{name, visible, golden}`; ≥1 visible and ≥1 hidden. Hidden
     goldens must not appear in prompt/starter (leak-guard).
   - Tests must be deterministic: never sleep-as-synchronization; use channels/WaitGroups;
     any polling loop needs a generous deadline (~2 s) so a loaded box can't flake it.
   - `verify` executes `reference_solution` against ALL tests under `-race` (must be green)
     and, for `debug_this`, executes `buggy` (must fail ≥1 test — a fake bug is rejected).
   - `timeout_ms` (default 30000) is passed to `go test -timeout`.
2. **`predict_output`**:
   - `grading.program` is a complete `package main` file. Its output MUST be deterministic —
     no scheduling-order-dependent prints (collect + sort, or sequence goroutines with
     channels). `verify` runs it twice and rejects differing outputs (R4 smoke check).
   - `expected_output` must be the program's real output — `verify` re-derives it by running
     the program and rejects drift (anti-fabrication: derived, never hand-typed).
   - `match`: `exact` | `trimmed` (default) | `contains` | `regex`. For programs that die
     (deadlock/panic), set `stream: combined` (pilot-additive; default `stdout`) and
     `match: contains` with the key phrase (e.g. `all goroutines are asleep - deadlock!`).
3. **`predict_race_verdict`**:
   - `grading.program` is a complete `package main` file; `iterations: 50` (R4: N≫2);
     `confidence: probabilistic`.
   - `expected_verdict: race | clean` (pilot-additive; replaces the sketch's single-polarity
     `expected_output` so clean programs are expressible).
   - A `race` construction must trip *reliably*: start contending goroutines behind a barrier
     (shared start channel) and loop the racy access ~100× per goroutine so overlap is
     near-certain. `verify` runs N iterations and rejects a race that never trips (and warns
     below ~50% trip rate) and a `clean` program that ever trips.
4. **`llm_judge`** (`explain_tradeoff` etc.):
   - Graded in Phase 0 by honest self-scoring against `reference_answer` (confidence LOW) —
     author rubrics exactly as the canonical example: weights sum to 1.0, `pass_threshold`,
     `anti_reward_hacking: {min_words, penalize_if_contains}`.
   - Rubric criteria follow the house bar: name the rejected alternative, state a concrete
     failure mode, include a number. `reference_answer` must itself clear `min_words`
     (rubric-fails-its-own-gold is a verify error).

## Voice & pedagogy

- Calibrated to a strong systems engineer who is a Go *beginner*: never teach "what a race
  is" — teach which primitive is idiomatic *here* and what the tooling actually prints.
  Conclave (his SFU project: signaling fan-out, upload meter, peer lifecycles) is the
  preferred running example.
- Teach bodies: short, WHY-first, one `> [!KEY] ...` line for the load-bearing rule.
- MCQ: exactly one `correct: true`, ≥3 options (prefer 4), every option carries a non-empty
  `why` (the distractors' whys are where the discrimination teaching lives — make them
  plausible, no giveaways); `reference_answer` equals the correct option's text verbatim.
- Numbers over adjectives everywhere a claim is made.
