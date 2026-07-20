# CLAUDE.md — Crucible (build guide for a fresh session)

> **STATUS: Phase 0 content pilot BUILT (2026-07-20); daily-use trial IN PROGRESS.** 14 lessons
> (`content/go/go04a…go05g`, conventions in `content/go/PILOT-CONVENTIONS.md`) run on the throwaway
> CLI harness `pilot/pilot.py` (`make list` / `make lesson ID=<id>` / `make verify` / `make status`;
> conda env `crucible`, wired into the Makefile). **Do NOT build Phase 1+ (engine, gate, mastery,
> judge) until the 2-week daily-use bar in §4 is met** — `make status` tracks it. Backlog + authoring
> cost: `docs/curriculum/go-backlog.md`. Web-dashboard theme tokens (for Phase 6, chosen by Bibek):
> `docs/theme/dracula-terminal.css`.
>
> This file is **Crucible-specific**. Bibek's profile, skills, coding style, git habits, and the
> no-artifact-publish rule already load from `~/Codes/CLAUDE.md` and `~/.claude/CLAUDE.md` — don't
> repeat them; honor them. This file adds only what a builder of *this project* needs.

---

## 1. What Crucible is (30 seconds)

A **local, single-user "teach then test" workbook** for Bibek. It teaches a primitive, forces
effortful reconstruction, and **auto-grades** the answer with a hybrid engine — deterministic checks
where a machine can decide, a reference-grounded **LLM-judge** only for design reasoning — assessing at
Bloom **Analyze/Evaluate/Create** ("name the rejected alternative + the failure mode + a number, or the
answer fails"). Domains: **Go** (his real gap, tied to `conclave`), **Python/FastAPI internals**, **deep
system design / cloud / DevOps**, and **defend-and-extend case-studies from his own repos**.

The whole plan was produced by two multi-agent research passes (a synthesis, then an adversarial
critique that corrected it). The corrected plan is the contract below. Nothing runs yet — this repo is
**docs only**.

## 2. Read these first, in order

1. **`PLAN.md`** — the architecture contract: locked stack, binding resolutions **R1–R10**, and the
   non-negotiable invariants. *This is the source of truth; when in doubt, it wins.*
2. **`docs/02-features.md`** — the prototype feature spec (P0/P1/P2), each with its rejected alternative.
3. **`docs/09-roadmap.md`** — the phased build order (content pilot first).
4. Then, as you build a given piece: `docs/03-architecture.md`, `docs/04-grading.md`,
   `docs/05-content-model.md`, `docs/06-progress-model.md`, `docs/01-pedagogy.md`.
5. **`content/examples/go04-concurrency-discrimination.yaml`** — the canonical lesson schema, as a full
   worked example. Copy its field names; don't invent a competing schema.
6. Raw research (why any decision was made) lives in `RESEARCH/`, incl. `_synthesis.md` (first draft)
   and `_critique.md` (the review that produced R1–R10).

## 3. Locked stack (chosen by Bibek — do not relitigate)

| Axis | Decision |
|---|---|
| Engine language | **Python** (FastAPI) |
| Interface | **Local web app** (FastAPI + light web UI); **CLI runner** for the earliest slices |
| Grading | **Hybrid per question-type** — deterministic + a **hosted** Claude LLM-judge |
| First vertical slice | **Go** concurrency-discrimination module |
| Persistence | **SQLite**, append-only attempt log + materialized mastery fold |
| Env/tooling | **uv + pyproject.toml**; gate on **ruff + mypy --strict + pytest** |
| Deliverables | **Local files only** — nothing published to claude.ai |

## 4. Where the build starts — Phase 0 (do THIS first)

Per **R2**, the #1 risk is building the fun platform instead of studying. So Phase 0 is **content, not
engine**:

- **Goal:** prove Crucible earns *daily use* before any grading machinery exists.
- **Do:** hand-author **10–15 real Go lessons** in the concurrency-discrimination vertical (tied to
  `conclave`), each following the `go04` YAML schema. Grade code answers with **plain `go test`** — a
  tiny throwaway harness (drop learner code + the lesson's tests into a temp Go module, run `go test
  -race`, show pass/fail + the minimal failing input). **No** sandbox, **no** schema-gate, **no**
  mastery model, **no** LLM-judge yet.
- **Use it daily for 2+ weeks.** If it teaches and he keeps opening it, *then* build Phase 1 (the
  executable green-gate) and the rest of the roadmap. If it doesn't get used, fix the content/loop
  before building anything.
- **Exit criterion:** ~12 lessons authored, gradeable with plain `go test`, and demonstrably used daily.

Only after that do you build Phase 1+ (spine + `make gate` → deterministic grader → hidden-tests →
hosted judge → scheduler → web UI → authoring pipeline → domain expansion). Full order in
`docs/09-roadmap.md`.

## 5. Guardrails you must not violate (compressed R1–R10 + invariants — full text in `PLAN.md`)

- **R1 — the LLM-judge is HOSTED, not offline.** `claude -p` / the Anthropic API are metered network
  calls. Never call the judge "offline/local/self-hosted." Budget USD cost; fail **open** on network
  loss (self-grade vs the shown reference at LOW confidence, never hard-fail). *(The critique caught
  this exact error in the first draft — don't reintroduce it.)*
- **R2 — content before cathedral.** See §4.
- **R3 — v1 code grading is plain local `go test`/`pytest` + timeout + `ulimit`.** His code on his box
  ≈ zero RCE risk. The hardened container is deferred until AI-authored/shared content exists.
- **R4 — `go test -race` is probabilistic** (false negatives; Go randomizes map iteration). Run
  `predict_race_verdict` over many iterations and report it as probabilistic; a 2-run stdout-diff is
  unsound.
- **R5 — budget latency + cost.** Warm runner + cached builds; cap judge samples at 3 with early-stop;
  grade code async; track grading-latency p50/p90/p99.
- **R6 — orchestrate over external labs** (6.824 / Maelstrom / CodeCrafters own code conformance);
  Crucible uniquely adds the design-defense judge, spacing, mastery/θ, and the rejected-alternative
  rubric. Hand-roll a grader only where none exists.
- **R7 — right-size anti-gaming:** for v1 keep only **reference-grounding** + **deterministic-wins**;
  defer the gold-set harness.
- **R8** — question taxonomy includes paper-comprehension, capacity/back-of-envelope, refactor-to-
  idiomatic, benchmark-reproduction.
- **R9 — mastery precision:** the gate is a **discrete unlock latch**; θ drives *review scheduling*; a
  decayed θ never re-locks a passed module; `recompute_from_log()` replays scheduler arithmetic from
  **stored grades**, it does **not** re-grade.
- **R10 — content ages:** changed-only gate execution, per-track toolchain pins.

**Invariants (always true):** gradeability *by construction* (a broken/ungradeable lesson cannot be
committed) · **deterministic-wins** (judge may only lower/flag, never raise a test verdict) · **numbers
over adjectives** + a per-module Limitations note · value order **Correctness > Reliability > UX >
Maintainability > Performance** · graceful degradation (fail-open/quarantine) · **local only**.

## 6. Vocabulary contract (do not silently rename across sessions)

Grading `strategy` values (`deterministic_choice`, `deterministic_output`, `hidden_tests`,
`llm_judge`) · the normalized grade **envelope** `{score, max, verdict, per_criterion, evidence,
confidence, grader_id, logs}` · `recompute_from_log()` · lesson `schema_version` / `content_rev` · the
`θ` / half-life / `due_at` mastery triple. To change one, edit `PLAN.md §4` first with the reason, then
propagate.

## 7. Build conventions (his taste — apply when you write code)

- **uv + `pyproject.toml`.** Package-by-feature under `src/crucible/` (e.g. `content/`, `grading/`,
  `mastery/`, `session/`, `web/`) — **not** package-by-layer. Thin dispatcher over self-contained
  mechanism modules, dependency-injected at `main`, no globals.
- **Green gate = `ruff` + `mypy --strict` + `pytest`.** Add a `Makefile` (`make gate`, `make test`).
  Table-driven, deterministic tests (injected clock, mocked HTTP); never say "done" without running it.
- **From-scratch where the primitive is the learning target**; reach for a library only when the
  library *is* the target. Structured errors → one handler → `{code, message, details}`.
- **Named constants with a justifying comment; WHY-not-what doc comments.** No bare magic numbers, no
  TODOs-as-implementation.
- **Commits:** terse, single-sentence, imperative, **no co-author trailer**. Commit/push **only when
  asked**. This is a new repo — `git init` when you start Phase 0; tighten `.gitignore` (no build
  artifacts, no `.env`).
- **When a web UI exists:** spin up isolated test instances (throwaway env/homedir), never touch a live
  dev port, avoid broad `pkill`; drive it with Playwright MCP to verify (loading/empty states,
  dark/light, console/network) before calling it done. The analytics dashboard is a **local file** —
  never published.

## 8. Directory map

```
crucible/
├── CLAUDE.md   (this file)   README.md   PLAN.md   (contract)   Makefile   (pilot targets)
├── docs/       00-vision · 01-pedagogy · 02-features · 03-architecture · 04-grading
│               05-content-model · 06-progress-model · 07-landscape · 09-roadmap
│   ├── curriculum/  go · go-backlog · python · system-design · project-design
│   └── theme/dracula-terminal.css   (web-dashboard tokens, Phase 6 — chosen by Bibek)
├── content/examples/go04-concurrency-discrimination.yaml   (canonical lesson schema)
├── content/go/  PILOT-CONVENTIONS.md + 14 pilot lessons (go04a…go05g), all verify-green
├── pilot/       THROWAWAY Phase 0 harness: pilot.py (CLI+graders+verify), attempts.jsonl,
│                answers/ (learner work), scratch/ (gitignored temp Go modules)
└── RESEARCH/    12 raw research docs (+ _synthesis.md, _critique.md)
    # src/ + pyproject.toml still do not exist — that is Phase 1, gated on §4's daily-use bar.
```

## 9. Definition of done (for any build task here)

The relevant gate is green (`make gate` once it exists; plain `go test` for Phase 0 lessons), the change
is verified by running it (show output), every quantitative claim is a real measured number, and the
piece's Limitations are stated. If a step was skipped or a test failed, say so plainly.
