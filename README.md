# Crucible

*A workbook that teaches a primitive, then tests you in the fire.* A local, single-user "teach then
test" system for one advanced engineer — it teaches a concept, forces effortful reconstruction, and
grades the answer with a hybrid of deterministic checks and a reference-grounded LLM-judge, assessing
at the level that actually matters: **"name the rejected alternative + the failure mode + a number, or
the answer fails."**

> **Status: Phase 0 content pilot BUILT (2026-07-20) — daily-use trial in progress.** The Go
> concurrency-discrimination vertical (14 lessons under `content/go/`) runs on a throwaway CLI
> harness (`pilot/`): `make list` · `make lesson ID=<id>` · `make status` · `make verify`. No
> engine exists yet, deliberately (R2): Phase 1+ is earned only by 2+ weeks of daily use. Working
> name **Crucible** — rename freely (theme: a crucible tests metal under heat; you're teaching
> *and* testing understanding all the way down).

## Why this exists

Off-the-shelf tools don't fit: exercism / A-Tour-of-Go grade too softly, Anki/LeetCode gate on rote
content, educative/roadmap.sh stop at interview depth with passive grading, boot.dev wraps it in
gamification you don't need. Crucible is a teach-then-**test** workbook that assesses design judgment
(not recall), auto-grades without external ground truth, reports **numbers not adjectives**, and —
because a broken or ungradeable lesson literally cannot be committed — is trustworthy by construction.

It teaches four domains: **Go** (the real gap, tied to `conclave`), **Python/FastAPI internals** (deep
from day one), **deep system design / cloud / DevOps** (beyond interview level), and **defend-and-extend
case-studies mined from your own repos** (WALterDB, GOOGLY, conclave…).

## How to read this

1. **[`PLAN.md`](PLAN.md)** — the architecture contract: the locked stack decisions and the ten binding
   resolutions (R1–R10) that correct the first-draft design. *Start here.*
2. **[`docs/00-vision.md`](docs/00-vision.md)** — problem, goals, non-goals, success criteria.
3. **[`docs/02-features.md`](docs/02-features.md)** — the prototype **feature spec** (P0/P1/P2). *The
   thing you asked for.*
4. **[`docs/09-roadmap.md`](docs/09-roadmap.md)** — the phased build order (content pilot first).
5. Everything else fills in the how.

## Document map

| Area | Docs |
|---|---|
| Contract & vision | [`PLAN.md`](PLAN.md) · [`docs/00-vision.md`](docs/00-vision.md) |
| Prototype spec | [`docs/02-features.md`](docs/02-features.md) · [`docs/09-roadmap.md`](docs/09-roadmap.md) |
| How it works | [`docs/01-pedagogy.md`](docs/01-pedagogy.md) · [`docs/03-architecture.md`](docs/03-architecture.md) · [`docs/04-grading.md`](docs/04-grading.md) · [`docs/05-content-model.md`](docs/05-content-model.md) · [`docs/06-progress-model.md`](docs/06-progress-model.md) |
| Positioning | [`docs/07-landscape.md`](docs/07-landscape.md) |
| Curriculum | [`docs/curriculum/go.md`](docs/curriculum/go.md) · [`docs/curriculum/python.md`](docs/curriculum/python.md) · [`docs/curriculum/system-design.md`](docs/curriculum/system-design.md) · [`docs/curriculum/project-design.md`](docs/curriculum/project-design.md) |
| Canonical schema | [`content/examples/go04-concurrency-discrimination.yaml`](content/examples/go04-concurrency-discrimination.yaml) |
| Raw research | [`RESEARCH/`](RESEARCH/) — one faithful doc per track, plus [`_synthesis.md`](RESEARCH/_synthesis.md) (first draft) and [`_critique.md`](RESEARCH/_critique.md) (the adversarial review that produced R1–R10) |

## The stack (chosen)

Python + **FastAPI** engine · local **web UI** (CLI runner for the earliest slices) · **SQLite**
(append-only attempt log + materialized mastery fold) · **hybrid grading** (deterministic + a *hosted*
Claude LLM-judge) · **first slice = Go**. Everything local except the design-judge, which is a hosted,
metered Anthropic API call (see `PLAN.md` R1).

## The honest part

The research was run twice: a synthesis, then an adversarial critique that caught a real incoherence
(the judge was described as "offline" when it's a hosted API call) and argued for building the *content*
before the *engine*. Both are preserved in `RESEARCH/`, and the corrections are folded into `PLAN.md` as
R1–R10. The plan you're reading is the corrected one, not the rosy one.

## Next step

**Use the pilot daily for 2+ weeks** (`make lesson ID=go04a-channel-ownership`, then follow the
prereq chain in `make list`; `make status` tracks the streak against the 14-day bar). The
per-lesson authoring-cost estimate and the ordered ~35-lesson backlog live in
[`docs/curriculum/go-backlog.md`](docs/curriculum/go-backlog.md). Only after the daily-use bar
holds does Phase 1 (spine + green-gate) get built — and if the bar fails, the honest outcome is
to fix the content or stop, not to build the engine anyway.
