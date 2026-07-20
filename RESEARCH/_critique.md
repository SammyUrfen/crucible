# CRITIQUE — adversarial completeness & abandonment review

> Adversarial review of the first-draft synthesis. Its corrections are folded into PLAN.md as resolutions **R1–R10**.

## Gaps

### LLM judge — offline/local claim vs reality

**Gap:** The design's headline framing is internally incoherent: it calls the judge 'local, offline-capable, self-hosted, matching his self-hosting ethos' and lists 'NOT reliant on a hosted frontier judge' as a non-goal — but `claude --bare -p` with claude-opus-4-8/sonnet-5 IS a network client to Anthropic's hosted frontier API (needs ANTHROPIC_API_KEY, costs metered dollars, requires connectivity). It is neither local nor offline, and it IS a hosted frontier judge. The whole trust/cost/reproducibility story is built on a false premise.

**Suggestion:** Pick one and re-derive downstream claims honestly: (a) accept it's a hosted, metered, network-dependent frontier judge — drop 'offline/local-first/self-hosted' for grading, add a real cost budget and a network-down fail-open path; or (b) use a genuinely local model (Ollama/llama.cpp) and re-baseline the entire trust posture, because a local 7-8B judge is dramatically weaker and gameable. You cannot have the frontier judge's quality AND the offline/self-hosted ethos simultaneously; the synthesis currently claims both.

### Content-authoring throughput (the stated #1 real risk)

**Gap:** The engine is sequenced before the content, and the green-gate makes each lesson HARDER to author (every reference must execute green, every rubric must clear its own gold, coverage-closure must hold). The AI-authoring pipeline that makes content scalable is Phase 5 — after all grading infra. So through Phases 0–4 he hand-authors, fighting the gate, with no throughput estimate (hours/lesson) and no target curriculum count. ~50 modules (13 Go + 9 Python + 12 distributed + 16 case-study) each with multiple executable assessments + calibrated rubrics is the actual bottleneck, and it's deferred and unquantified.

**Suggestion:** Invert the risk: do a content-first pilot BEFORE the sandbox/anti-gaming cathedral. Hand-author 10–15 real lessons in his single highest-value domain (Go, tied to conclave), grade code with plain `go test` at first, and confirm he actually uses it daily. Put a per-lesson authoring-cost estimate and a concrete curriculum backlog (which 50 lessons, ordered) in the plan. Bring the AI-authoring pipeline forward — it's the thing that determines whether this is a workbook or a demo with 3 lessons.

### Sandbox — threat model vs effort

**Gap:** The single hardest, most-budgeted component (rootless container + seccomp + gVisor + cgroups) is justified by 'untrusted code,' but for a solo learner the code being run is HIS OWN answers on HIS OWN machine — the RCE threat is near-zero for v1. The genuine untrusted surface (AI-authored references) only appears in Phase 5. The design front-loads a security cathedral against a threat that doesn't exist until much later, on the critical path to any learning value.

**Suggestion:** Descope the sandbox for v1 to plain local `go test`/`pytest` with a wall-clock timeout + resource ulimit — good enough for his own code on his own box. Promote the hardened sandbox to when AI-authored or shared content actually exists (Phase 5+), and budget it as its own project then. This removes the hardest blocker from the path to first learning value.

### Go sandbox operational reality

**Gap:** A no-network Go sandbox breaks on any import outside stdlib: `go test` will try to fetch modules and fail with GOPROXY unreachable. Also, `go build`+`-race` is CPU/memory-heavy and multi-second cold; per-item compile with a fresh container is slow, and Go panics/compile errors print source file paths and lines — scrubbing that to hide hidden-test/reference source is fiddly and easy to get wrong (a compile error in a hidden test file dumps its source).

**Suggestion:** Pre-bake a module cache (GOFLAGS=-mod=vendor or a populated GOMODCACHE with GOPROXY=off) into the runner image; mount a persistent build cache so compiles are warm; and explicitly design the output-scrubbing for Go's file:line:panic format with a test that a hidden-test compile error does NOT leak. Treat these as first-class, not footnotes.

### predict_race_verdict soundness

**Gap:** It's called 'the cleanest deterministic+adversarial Go signal,' but `go test -race` has FALSE NEGATIVES by design — the detector only reports races it actually observes on the scheduled interleaving; a racy program can print no DATA RACE on a given run. So the 'expected: DATA RACE' oracle is nondeterministic, and a learner (or the gate) can see a green run on genuinely racy code. Separately, the nondeterminism gate ('reject if stdout differs across TWO runs') is too weak — Go deliberately randomizes map iteration order, so any map-printing program is nondeterministic and two runs can coincidentally match.

**Suggestion:** Demote predict_race_verdict from 'cleanest signal' or harden it: run N≫2 iterations, use race constructions known to trip reliably, and/or `GORACE` tuning; accept it's probabilistic and report it as such. For predict_output nondeterminism, run many iterations and/or statically flag map-range/goroutine/time/float patterns rather than trusting a 2-run diff.

### Missing question / assessment types

**Gap:** The taxonomy omits several types the research explicitly calls for: (1) paper/reading comprehension — the distributed track is anchored on DDIA + Raft/Dynamo/Spanner papers, but no item verifies he absorbed a safety argument or invariant from reading; (2) capacity / back-of-envelope numeric derivation — repeatedly demanded ('crossover point, load variance, bottleneck math, stopping rule') but there's no dedicated numeric-derivation-with-tolerance type with a computable oracle; (3) refactor-to-idiomatic — the research says convert exercism's 'now make it idiomatic' pass into a solo second pass, but idiom isn't captured by hidden tests, so it needs its own judge-graded type; (4) benchmark-reproduction artifact — the A/B and GOOGLY modules recommend he COMMIT a reproducible harness, but there's no graded 'produce and defend a measurement' item type.

**Suggestion:** Add these four types with explicit strategy mappings: paper-comprehension and refactor-to-idiomatic → llm_judge (reference-grounded); capacity-derivation → deterministic numeric-with-tolerance where the oracle is a worked formula; benchmark-reproduction → hybrid (deterministic 'harness runs and emits p50/p99' gate + judge on the written defense).

### Build-vs-reuse: duplication of best-in-class external graders

**Gap:** The research itself names MIT 6.824's autograder, Maelstrom/Gossip Glomers, and CodeCrafters as the gold-standard graders for exactly the build-a-primitive and distributed tracks — and warns 'the harness can crowd out the actual studying.' The design nonetheless plans to hand-roll the sandbox + hidden-tests + fault-injection checker to grade content those tools already grade better. The parts that are genuinely novel (defend-and-extend design memos, explain-it-back on his own repos) need only the LLM judge, NOT the heavy sandbox. The infra investment is concentrated where external tools already win, and thin where the workbook is actually differentiated.

**Suggestion:** Reframe the workbook as an orchestrator/tracker LAYERED over external labs, not a replacement grader: let 6.824/Maelstrom/CodeCrafters own the code conformance, and have the workbook add what they lack — the design-defense judge, spacing, mastery/θ tracking, and the 'name the rejected alternative + failure mode + number' rubric. Only hand-roll a grader where no external one exists.

### Anti-gaming subsystem — possibly misallocated priority

**Gap:** The entire anti-gaming subsystem is predicated on 'he is both author and beneficiary of a high grade, so he'll game it.' But gaming pressure exists when a grade has EXTERNAL value (credential, boss); here the grade's only value is accurate self-knowledge, which he WANTS. A self-motivated learner has little incentive to self-game — and he controls all the tunables anyway (pass_threshold, K, goal θ, config table), so the ultimate 'gaming' (lower the bar, don't open the app) is untouched by gold-sets and retry-logging. The real failure mode is disengagement and false-confidence from a lenient judge, which reference-grounding + deterministic-wins already handle cheaply. The gold-set-calibration + retry-trace + logged-attempt machinery may be over-built relative to the actual risk (motivation + content volume).

**Suggestion:** Keep the two cheap structural guards (reference-grounding, deterministic-wins) — they're near-free and prevent false confidence. Right-size the rest: a hand-audit of a random sample is enough; defer the full gold-set-reproduction-before-trust harness until there's evidence he'd game it. Redirect that engineering into content volume and daily-use ergonomics, which are the real risks.

### recompute_from_log reproducibility scope

**Gap:** 'recompute_from_log() reproduces θ bit-for-bit' is only true because the log stores the GRADE (y-value); the fold replays stored numbers. It does NOT re-grade. Any attempt graded by the LLM judge is not reproducibly re-gradable (nondeterministic + hosted + model may change), so retuning a RUBRIC is not a replay — it requires re-grading (network, cost, drift). The elegant event-sourcing property applies to the scheduler arithmetic only, not to grading.

**Suggestion:** State this boundary explicitly: replay reproduces θ from stored grades after retuning SCHEDULER constants (K, half-life, weights). Retuning a rubric or swapping the judge model invalidates stored y-values and needs a re-grade pass, which is neither free nor deterministic. Don't let the 'bit-for-bit' claim imply grade reproducibility.

### Mastery model — transfer, gate-vs-θ, double decay

**Gap:** Three unspecified issues: (1) No inter-skill transfer — each θ is independent with only a family cold-start prior, so an advanced learner re-measures correlated skills redundantly and mastery in go04 doesn't inform go05. (2) The behavioral mastery gate (build + name alternative + failure mode with a number) is described as a one-time per-module unlock, but its relationship to the continuous θ is undefined — does passing set θ? Can θ decay back below goal and re-lock a module already 'passed'? (3) Two decay mechanisms coexist (Elo-with-decay θ AND FSRS-lite half-life for spacing) with no statement of how they interact or avoid double-counting forgetting.

**Suggestion:** Add a lightweight prereq-propagation prior (clearing go04 raises the prior on children). Define the gate→θ relationship precisely (e.g. gate is a discrete unlock latch, θ drives review scheduling, and a decayed θ schedules review but does NOT re-lock). State that half-life governs review timing and θ-decay governs ability estimate, and show they don't both penalize the same forgetting event.

### Session latency budget

**Gap:** A 25-min / 8–12-item session must absorb: container spin-up per code item, multi-second Go compile+`-race`, plus 3–5× judge sampling per design item where each `claude -p` call is seconds of network round-trip. A single design item could cost 15–30s of waiting; two code items add tens of seconds of compile. The 25-min box could be dominated by grading latency — and daily-driver friction is the top predictor of abandonment.

**Suggestion:** Define an explicit per-item latency budget and engineer to it: warm/persistent runner with cached build artifacts, parallelize the 3–5 judge samples, cap sampling to 3 with early-stop on agreement, and grade code asynchronously so the session keeps moving. Measure p50/p90/p99 of grading latency as a first-class health metric, not just of his answers.

### Hint / scaffolding ladder for the Go on-ramp

**Gap:** config carries a `hint_penalty` but there's no hint DESIGN. For a true-beginner Go learner, hitting an opaque hidden-test failure with no scaffold is exactly the 'fighting syntax instead of learning the concept' failure the risks section warns about. The on-ramp altitude asymmetry needs a graduated hint/scaffold mechanism, which is absent.

**Suggestion:** Design a hint ladder (compile-error explanation → conceptual nudge → partial scaffold → reveal), each rung logged with its penalty, available on the Go on-ramp and suppressed on Python-deep items. Without it the on-ramp asymmetry is a label, not a mechanism.

### Composite-item credit assignment

**Gap:** Composite items (code + design prose) cover multiple objectives across possibly different skills, with 'deterministic as a hard gate.' But a single attempt then produces one grade that must update multiple θ's — the credit-assignment rule (which skill's θ moves, by how much, when the composite partially fails) is unspecified. This is a real modeling hole for multi-objective items.

**Suggestion:** Specify per-objective sub-scores from the envelope's per_criterion[] mapped to the objective's skill, and update each skill's θ from its own sub-score, with the deterministic hard-gate failure attributed to the correctness skill only — don't collapse a multi-skill item into one θ update.

### Content aging / maintenance

**Gap:** Go 1.22+ assumptions, pinned library versions (pydantic-v2, SQLAlchemy 2.0, pion), and 'production current' distributed tooling all age. A pinned schema_version plus per-lesson executable references means a toolchain bump can turn dozens of green lessons red at once, and there's no maintenance model or changed-only gating.

**Suggestion:** Add incremental/changed-only gate execution (don't re-run all 50 references every commit), a toolchain-pin per track, and a periodic 'gate against latest toolchain' job so aging is caught deliberately rather than as a mass breakage.

## Abandonment risks

- Infra-first runway: Phases 0–4 build the grading engine, sandbox, and mastery fold before there is real learning content or a session worth doing daily. Building the engine scratches exactly his systems-builder itch — so he 'finishes' the fun part (the platform) and never sustains the boring part (studying daily). The tool becomes the procrastination.
- Content runs dry after a week: the vertical slice is one hand-authored lesson and the scalable authoring pipeline is last. He does 3–5 lessons, hits the end, and the workbook has nothing left to teach while the engine is still 'impressive.'
- Per-session latency drag: container spin-up + multi-second Go compile/`-race` + 3–5× hosted-judge round-trips make a 25-minute session feel sluggish and metered. Daily-driver friction is the classic silent killer.
- Green-gate authoring friction: every lesson must survive executable references + self-clearing rubrics + coverage-closure. Authoring becomes a fight with the gate, so he stops adding content — and without new content the tool is dead.
- Realizing external labs are better: partway through he notices MIT 6.824's autograder, Maelstrom, and CodeCrafters already grade the build-a-primitive and distributed work more rigorously than his hand-rolled sandbox, and concludes he should just do those labs directly — abandoning the wrapper.
- Metered-cost anxiety + arguing with a weak judge: a hosted, per-call-billed judge that he disagrees with on design essays is both a running cost and a daily irritation; disputing a grade every session is demoralizing and erodes trust in the whole system.
- The desirable-difficulty accuracy dip (interleaving + generate-before-reveal lower in-session scores by design) reads as 'the workbook isn't working' unless it's framed loudly and continuously — an unframed dip drives 'this is making me worse' quitting.
- He controls all the tunables: on a bad day he lowers goal θ / pass_threshold and the elaborate anti-gaming layer does nothing to stop the one form of gaming that matters — quietly relaxing the bar or not opening the app.

## Must fix before build

- Resolve the local/offline vs hosted-frontier-API contradiction for the judge before anything else — the current framing claims both and they are mutually exclusive. Decide: hosted frontier (accept cost + network + no true model pin, drop the offline claim) or genuinely local model (accept far weaker judge, re-baseline all trust guarantees). Every downstream cost, reproducibility, and trust claim depends on this.
- Run a content-first pilot before the infra: hand-author 10–15 real lessons in his top-priority domain (Go for conclave), grade code with plain `go test`/`pytest`, and confirm he actually uses it for two+ weeks. Prove daily usage and learning value BEFORE building the sandbox, anti-gaming, and mastery-fold machinery. Do not build the cathedral for an unvalidated behavior.
- Descope the v1 sandbox to plain local execution with timeouts/ulimits (his own code, his own machine, ~zero RCE threat) and defer the hardened container to when AI-authored/shared content exists. If a hardened sandbox is kept, first solve the Go no-network module-cache problem and the panic/compile-error source-leak scrubbing — both currently unaddressed and both break the runner.
- Fix the race-verdict / nondeterminism soundness: `go test -race` has false negatives and Go randomizes map iteration, so the 'DATA RACE' oracle and the 2-run stdout-diff check are both unsound. Either harden them (N≫2 runs, reliably-tripping constructions, static nondeterminism flagging) or demote predict_race_verdict from 'cleanest deterministic signal.'
- Set an explicit per-session latency budget and a per-lesson + per-session LLM cost ceiling, then engineer to them (warm runner + cached builds, parallel/capped judge sampling, async code grading, total_cost_usd budget alarm). Unbudgeted latency and metered cost are direct abandonment drivers.
- Reframe scope against external graders: decide in writing what the workbook UNIQUELY adds (design-defense judge on his own repos + spacing + mastery/θ tracking + the rejected-alternative rubric) and reuse 6.824/Maelstrom/CodeCrafters for code conformance instead of re-implementing their graders. Otherwise the harness crowds out the studying, exactly as the research warns.
- Right-size the anti-gaming investment to the actual risk (disengagement and lenient-judge false confidence, not adversarial self-gaming): keep only the two near-free structural guards (reference-grounding, deterministic-wins) for v1 and redirect the gold-set/retry-trace engineering into content volume and daily-use ergonomics.

