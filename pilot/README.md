# Crucible Phase 0 pilot — throwaway CLI harness

**This is the probe, not the engine** (PLAN.md R2, docs/09-roadmap.md Phase 0). It exists to
answer one question: *do you open Crucible daily for 2+ weeks and learn real Go from it?*
If yes, Phase 1 (spine + green-gate) gets built. If no, the content/loop gets fixed — not the
platform. Almost nothing here survives into the real engine; resist improving it.

## Quickstart

```console
$ make list                                   # lessons + pass state
$ make lesson ID=go04a-channel-ownership      # teach → test session
$ make review ID=go04a-channel-ownership      # test-first, reveal-on-miss (spaced review)
$ make status                                 # streak + honest numbers
$ make verify                                 # prove every lesson is gradeable (runs all Go refs)
```

Uses the `crucible` conda env (wired into the Makefile) and the system Go toolchain
(go1.26.x). Set `$EDITOR` for code/essay items; unset, the harness waits while you edit the
answer file in another window.

**Press `?` at any prompt** for an "explain like I'm 10" hint on whatever is on screen. Hints
are reference-free by construction — the prompt forbids revealing a graded answer, and the
model only ever sees the teach material, never the rubric or the reference. Each hint bumps
`hints_used` in the attempt log, so where you get stuck becomes data instead of a feeling.

The judge and hints read `OMNIROUTE_API_KEY` from the gitignored repo-root `.env`. Override
either model per-session: `CRUCIBLE_JUDGE_MODEL=... CRUCIBLE_HINT_MODEL=... make lesson ID=...`.

## What grades what (Phase 0 scope)

| strategy | grader | honest caveat |
|---|---|---|
| `deterministic_choice` | exact/Jaccard option match | — |
| `deterministic_output` | runs the program, compares to the **derived** output | `predict_race_verdict` is **probabilistic** (R4): N runs under `-race`; 0/N observed ≠ race-free |
| `hidden_tests` | temp Go module + `go test -race` + wall timeout + CPU rlimit (R3) | "hidden" tests are only *unshown* — the YAML is on your disk; real isolation is Phase 3 |
| `llm_judge` | reference-grounded **hosted judge** via the local OmniRoute gateway (`antigravity/claude-sonnet-4-6`); it rules per rubric criterion and the weighted score is folded **in Python**, so it cannot invent a total | R1 holds: the gateway is local, the models are **not** — these are metered network calls. Gateway down ⇒ self-grade at confidence LOW |

Attempts append to `pilot/attempts.jsonl` (`{ts, lesson, content_rev, assessment, strategy,
verdict, score, max, confidence, grader_id, latency_ms}`). Nothing re-grades it; Phase 2's
`recompute_from_log()` will fold it into θ. Your code/essay answers persist in
`pilot/answers/` so you can iterate across days.

## Limitations (what this harness does not do)

- No sandbox beyond timeout + CPU rlimit — it runs *your* code on *your* box (R3).
- The judge runs **one** sample, not R5's cap of 3 with early-stop — at n=1 attempts a spread
  nothing acts on isn't worth 3× the latency. It is not calibrated against a gold set (R7
  defers that), so treat a judge PASS as one strict reader's opinion, not a measurement.
- No mastery model, no scheduler, no spacing — `status` shows raw counts and streak only.
- No YAML schema gate — `verify` is one procedural pass (references must run green, buggy
  code must fail, predict outputs are derived not hand-typed, race items must trip). It
  catches broken lessons, not shallow ones.
- `verify` of race items proves the construction tripped **on this box today**, not that it
  always will (R4).
