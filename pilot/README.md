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

## What grades what (Phase 0 scope)

| strategy | grader | honest caveat |
|---|---|---|
| `deterministic_choice` | exact/Jaccard option match | — |
| `deterministic_output` | runs the program, compares to the **derived** output | `predict_race_verdict` is **probabilistic** (R4): N runs under `-race`; 0/N observed ≠ race-free |
| `hidden_tests` | temp Go module + `go test -race` + wall timeout + CPU rlimit (R3) | "hidden" tests are only *unshown* — the YAML is on your disk; real isolation is Phase 3 |
| `llm_judge` | **no hosted judge yet** — self-grade vs the shown reference, confidence LOW (the R1 fail-open path as the only path) | self-grading honesty is on you until Phase 4 |

Attempts append to `pilot/attempts.jsonl` (`{ts, lesson, content_rev, assessment, strategy,
verdict, score, max, confidence, grader_id, latency_ms}`). Nothing re-grades it; Phase 2's
`recompute_from_log()` will fold it into θ. Your code/essay answers persist in
`pilot/answers/` so you can iterate across days.

## Limitations (what this harness does not do)

- No sandbox beyond timeout + CPU rlimit — it runs *your* code on *your* box (R3).
- No mastery model, no scheduler, no spacing — `status` shows raw counts and streak only.
- No YAML schema gate — `verify` is one procedural pass (references must run green, buggy
  code must fail, predict outputs are derived not hand-typed, race items must trip). It
  catches broken lessons, not shallow ones.
- `verify` of race items proves the construction tripped **on this box today**, not that it
  always will (R4).
