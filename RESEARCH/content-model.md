# Content-as-Data Model + Question-Type Taxonomy

> Research track. Faithful rendering of the agent's structured findings.

**Dimension:** Content-as-data model + question-type taxonomy for a teach-and-test workbook (schema, grading map, AI-authoring pipeline, versioning + green-gate)

## Summary

A single content-as-data model where each lesson file co-locates teaching, worked examples, one-or-more assessments, per-assessment rubric, reference answer, and deterministic tests — mirroring the DSA workbook's JSON-topic files but adding a gradeable-assessment spine. The design's load-bearing idea, taken straight from his set-containment anti-fabrication guard, is that correctness is proven by construction, not asserted: every code/output "reference answer" is EXECUTED by the gate and the lesson is rejected unless it reproduces; every LLM-judge rubric is run against its own gold answer and rejected if the gold answer can't clear it; and a coverage-closure check makes a lesson with any ungradeable objective impossible to commit. YAML is the authoring source-of-truth (block scalars beat JSON escaping for embedded code/prose — his AUTHORING.md literally complains about escaping), compiled to JSON validated by a two-layer gate: a declarative JSON Schema for shape + a procedural validator (like his validate.mjs) for the semantic/executable guards a schema can't express. Ten question types each map to exactly one of three grading strategies (deterministic, hidden-tests, LLM-judge), and the AI-authoring pipeline is a bounded self-repair loop that quarantines rather than hard-fails, with "no gradeable assessment" and "reference answer doesn't reproduce" as the two non-negotiable hard errors.

## Key findings

### Lesson schema co-locates teaching + assessments + rubric + reference + deterministic tests in one file, keyed on a coverage graph between objectives, teach blocks, and assessments

Fleshed-out example (YAML source-of-truth, compiled to JSON for runtime). Top-level: schema_version (int, gate refuses unknown/newer), id (globally-unique kebab, MUST start with '<tag>-'), tag, title, track, week, priority (attack|moderate|review|meta), content_rev, prerequisites[] (ids the gate asserts exist), summary, learning_objectives[], teach[], worked_examples[], assessments[] (>=1 REQUIRED), figures{}. The invariant: union of assessments[].covers MUST equal the set of learning_objective ids, and every objective must also be taught by >=1 teach/worked block via `covers` — orphan objective or orphan assessment fails the gate.

```yaml
schema_version: 1
id: sys07-2pl-deadlock        # kebab, MUST start with '<tag>-'
tag: sys07
title: "Strict 2PL & Deadlock Detection"
track: systems
week: "Week 3 · Module 07"
priority: attack
content_rev: 4                # bumped on any content edit; git is the store
prerequisites: [sys06-locking-basics, sys05-txn-acid]
summary: >
  Strict 2PL is the 'hold every lock until commit' rule that buys serializability
  and cascadeless recovery — at the price of deadlocks you must detect.

learning_objectives:          # each MUST be taught AND assessed via `covers`
  - { id: sys07-o1, bloom: understand, text: "Why strict 2PL gives a serializable, cascadeless schedule" }
  - { id: sys07-o2, bloom: apply,      text: "Detect a deadlock from a wait-for graph and pick a victim" }
  - { id: sys07-o3, bloom: analyze,    text: "Trade-off: deadlock detection vs prevention (wait-die/wound-wait)" }

teach:
  - heading: "The two phases, and why 'strict'"
    covers: [sys07-o1]
    body: |
      > [!KEY] 'Strict' means release NOTHING until commit/abort — that is what kills cascading aborts.
      [[fig:sys07-2pl-phases]]
  - heading: "Wait-for graphs & victim selection"
    covers: [sys07-o2, sys07-o3]
    body: |
      A cycle in the wait-for graph IS a deadlock...

worked_examples:
  - id: sys07-w1
    covers: [sys07-o2]
    prompt: "T1 holds A wants B; T2 holds B wants A. Draw the wait-for graph and resolve."
    solution: |
      Edges T1->T2 and T2->T1 form a 2-cycle => deadlock. Abort the younger (T2)...

assessments:                  # >=1 REQUIRED; union(covers) == objective ids
  - id: sys07-a1              # ---- MCQ (deterministic) ----
    type: mcq
    covers: [sys07-o1]
    difficulty: easy
    prompt: "Strict 2PL prevents cascading aborts because it..."
    grading:
      strategy: deterministic_choice
      options:
        - { text: "releases read locks early",         correct: false, why: "that's plain 2PL, allows dirty reads" }
        - { text: "holds all locks until commit/abort", correct: true,  why: "no txn reads another's uncommitted write" }
        - { text: "uses timestamps instead of locks",   correct: false, why: "different (optimistic/TO) family" }
        - { text: "detects wait-for-graph cycles",      correct: false, why: "deadlock detection, unrelated to cascades" }
    reference_answer: "holds all locks until commit/abort"

  - id: sys07-a2              # ---- multi-select (deterministic, partial credit) ----
    type: multi_select
    covers: [sys07-o3]
    grading:
      strategy: deterministic_choice
      partial_credit: jaccard        # all | jaccard
      options:
        - { text: "wait-die",   correct: true }
        - { text: "wound-wait", correct: true }
        - { text: "wait-for cycle check", correct: false, why: "detection, run periodically" }
        - { text: "timeout-abort",         correct: false, why: "a heuristic detector, not prevention" }
    reference_answer: ["wait-die", "wound-wait"]

  - id: sys07-a3              # ---- predict-output (gate EXECUTES the program; expected is DERIVED) ----
    type: predict_output
    covers: [sys07-o2]
    grading:
      strategy: deterministic_output
      runner: python3
      program: |
        print("deadlock: cycle [T1,T2]; victim=T2")
      expected_output: "deadlock: cycle [T1,T2]; victim=T2"   # gate asserts stdout == this
      match: exact                    # exact | trimmed | regex

  - id: sys07-a4              # ---- code-completion (hidden tests) ----
    type: code_completion
    covers: [sys07-o2]
    difficulty: hard
    grading:
      strategy: hidden_tests
      language: python
      starter: |
        def has_cycle(adj):   # adj: dict[int,list[int]]
            ...
      reference_solution: |            # gate RUNS this vs ALL tests; must be green or lesson REJECTED
        def has_cycle(adj):
            WHITE,GREY,BLACK=0,1,2; color={u:WHITE for u in adj}
            def dfs(u):
                color[u]=GREY
                for v in adj.get(u,[]):
                    if color.get(v,0)==GREY or (color.get(v,0)==WHITE and dfs(v)): return True
                color[u]=BLACK; return False
            return any(color[u]==WHITE and dfs(u) for u in adj)
      tests:
        - { name: two_cycle, visible: true,  input: "{1:[2],2:[1]}", expect: "True" }
        - { name: no_cycle,  visible: true,  input: "{1:[2],2:[]}",  expect: "False" }
        - { name: self_loop, visible: false, input: "{1:[1]}",       expect: "True" }
      timeout_ms: 2000

  - id: sys07-a5              # ---- code-from-scratch (hidden tests + OPTIONAL advisory llm review) ----
    type: code_from_scratch
    covers: [sys07-o2]
    grading:
      strategy: hidden_tests
      language: python
      reference_solution: | ...
      tests: [ ... ]
      llm_review: { enabled: true, weight_of_style: 0.0 }   # comment-only; tests decide pass/fail

  - id: sys07-a6              # ---- debug-this (gate runs BOTH: buggy MUST fail, fix MUST pass) ----
    type: debug_this
    covers: [sys07-o1]
    grading:
      strategy: hidden_tests
      language: python
      buggy: |               # gate asserts this FAILS >=1 test (else the bug is fake)
        def commit(t): t.release_read_locks_early(); t.write(); t.commit()
      reference_solution: |  # gate asserts this PASSES all tests
        def commit(t): t.write(); t.commit(); t.release_all_locks()
      tests: [ ... ]

  - id: sys07-a7              # ---- short-answer/definition (llm-judge: keyword set OR rubric) ----
    type: short_answer
    covers: [sys07-o1]
    grading:
      strategy: llm_judge
      judge_mode: keyword_or_rubric
      keyword_must:     [["acquire","lock"], ["no","release"]]   # inner=OR, outer=AND
      keyword_must_not: [["release"]]
      rubric: { pass_threshold: 0.7, criteria: [ { id: c1, weight: 1.0, text: "Only-acquire, no-release, before first unlock" } ] }
    reference_answer: |     # gate asserts this gold answer clears its OWN rubric + keyword guard
      The growing phase is where a transaction only acquires locks and releases none.

  - id: sys07-a8              # ---- explain-the-trade-off / design-essay (llm-judge: rubric + reference) ----
    type: explain_tradeoff
    covers: [sys07-o3]
    difficulty: hard
    grading:
      strategy: llm_judge
      judge_mode: rubric
      rubric:
        pass_threshold: 0.6
        criteria:
          - { id: c1, weight: 0.4, text: "Names contention level as the deciding variable" }
          - { id: c2, weight: 0.3, text: "Detection wastes work on abort; prevention wastes it on false aborts" }
          - { id: c3, weight: 0.3, text: "Reaches a defensible recommendation, not just a list" }
      anti_reward_hacking: { min_words: 40, penalize_if_contains: ["as an AI", "it depends"] }
    reference_answer: |
      Detection wins under low contention: cycles are rare, so you pay nothing on the common
      path and only abort on a real cycle. Prevention (wound-wait) wins under high contention
      where detection would thrash. Decide by measured lock-conflict rate.

  - id: sys07-a9              # ---- critique-this-design (llm-judge) ----
    type: critique_design
    covers: [sys07-o3]
    grading:
      strategy: llm_judge
      judge_mode: rubric
      rubric: { pass_threshold: 0.6, criteria: [ { id: c1, weight: 0.5, text: "Names timeout as a crude detector w/ false positives under load" }, { id: c2, weight: 0.5, text: "Proposes a concrete better alternative (wait-for graph + victim policy)" } ] }
    reference_answer: | ...

  - id: sys07-a10             # ---- Feynman / explain-back (llm-judge) ----
    type: feynman
    covers: [sys07-o1]
    grading:
      strategy: llm_judge
      judge_mode: rubric
      rubric: { pass_threshold: 0.6, criteria: [ { id: c1, weight: 0.5, text: "Analogy correctly maps hold-until-done to lock-until-commit" }, { id: c2, weight: 0.5, text: "No technical error introduced by the simplification" } ] }
    reference_answer: | ...

figures:                      # same referential-integrity + no-hardcoded-colors rules as DSA workbook
  sys07-2pl-phases:
    caption: "Lock count rising then held flat to commit (strict) vs sawtooth (plain 2PL)."
    svg: "<svg viewBox=\"0 0 660 220\" role=\"img\" ...>...</svg>"
```

*Source:* grounded in dsa-workbook/AUTHORING.md schema + scripts/validate.mjs

### Ten question types collapse onto three grading strategies; the type is a discriminated union on `grading.strategy`, not on `type` — so the runtime/grader has exactly 3 code paths

deterministic_choice (mcq, multi_select), deterministic_output (predict_output), hidden_tests (code_completion, code_from_scratch, debug_this), llm_judge (short_answer, explain_tradeoff, design_essay, critique_design, feynman). code_from_scratch may attach an ADVISORY llm_review whose weight_of_style defaults to 0.0 — the hidden tests always decide pass/fail so a flaky model review can never fail a correct solution (his 'LLM calls must never hard-fail the pipeline' rule). Grading strategy, not question type, drives both the grader and the gate's per-type structural checks. Full per-type mapping is in proposed_modules.

*Source:* task requirement (2) reconciled to his grading-seam taste

### Structural anti-fabrication guard = correctness proven by construction, mirroring his numeric set-containment résumé guard — five deterministic invariants the gate enforces with zero LLM in the loop

(1) GRADEABLE-OR-REJECT: a lesson with zero assessments cannot be committed. (2) COVERAGE-CLOSURE: union(assessments[].covers) must equal the declared objective-id set, and every objective must be taught by >=1 teach/worked block — orphan objective OR orphan assessment fails. (3) REPRODUCIBLE-ANSWER: every predict_output program is executed and stdout must equal expected_output (outputs are machine-DERIVED, never hand-typed); every hidden_tests reference_solution is executed and must pass ALL tests; debug_this additionally executes the `buggy` code and asserts it FAILS >=1 test (a fake bug is rejected). (4) RUBRIC-PASSES-OWN-REFERENCE: every llm_judge assessment must ship a non-empty reference_answer, and the authoring gate runs the judge on that gold answer — it must score >= pass_threshold and satisfy keyword_must / violate no keyword_must_not, else the rubric is broken and rejected. (5) LEAK-GUARD: string-containment check that no hidden test's input/expected appears in the visible prompt or starter code. These are structural guards that make a bad outcome impossible by construction, not by prompting — the exact pattern of his set-containment check that rejects any résumé bullet introducing an unsourced number.

*Source:* job aggregator anti-fabrication guard + validate.mjs referential-integrity checks

### AI-authoring pipeline is a bounded self-repair loop with a deterministic preflight; it quarantines rather than hard-failing the batch, and only two errors are non-negotiable

Stage 1 SKELETON: an LLM converts one source note/topic into a lesson draft against the pinned schema (an AUTHORING.md-style contract prompt, like his DSA authoring spec). Stage 2 STRUCTURAL PREFLIGHT (no LLM): JSON-parse self-check + schema-shape validate + gradeable-or-reject + coverage-closure; drafts missing an assessment or with an orphan objective bounce back with the specific failure as feedback. Stage 3 EXECUTABLE MATERIALIZATION: run every predict_output program and every hidden_tests reference_solution in a sandbox; non-reproducing gold answers bounce back to the LLM with the runner output as the repair prompt (bounded to N=3 retries, then QUARANTINE — never hard-fail the whole batch, graceful degradation with a surfaced reason). Stage 4 RUBRIC SELF-CONSISTENCY: run the judge on each llm_judge reference_answer; a gold answer that can't clear its own rubric bounces. Stage 5 ADVERSARIAL AUDIT (his multi-agent self-audit tell): a red-team LLM tries to answer MCQs by elimination (flags giveaway distractors), find teaching claims with no assessment, and find assessments that don't discriminate — findings are WARNINGS, advisory only. Stage 6 MERGE: only lessons green on the deterministic gate are committed; content_rev bumped. The two HARD errors that block commit are 'no gradeable assessment' and 'reference answer does not reproduce'; everything else is a warning.

*Source:* his multi-agent adversarial self-audit + graceful-degradation patterns

### Versioning is two-level and the green gate is two-layer (declarative shape + procedural semantics), matching his four-command green-gate and validate.mjs taste

VERSIONING: schema_version (file-top int) bumped only on breaking field changes; the gate refuses unknown or newer versions (pin-like his PLAN.md 'architecture contract: do not silently rename'). content_rev is a per-lesson revision bumped on any edit; git remains the actual version store (one file per lesson under content/<track>/<id>.yaml, compiled to build/<id>.json). GATE (`make gate` / `npm run gate`, exit non-zero on any error, warnings printed but non-blocking, errors-vs-warnings split exactly as validate.mjs): step 1 YAML->JSON compile + JSON-parse self-check; step 2 declarative JSON Schema (ajv) for shape — the formal artifact he asked for; step 3 procedural validator for what a schema CAN'T express (coverage-closure, referential integrity of prerequisites/covers/figure-tokens, gradeable-or-reject, leak-guard); step 4 executable materialization (run reference solutions + predict_output programs in sandbox); step 5 rubric-self-check; step 6 optional Playwright render QA (missing-figure sentinels, dark/light, console errors) as the second gate, as in qa.mjs. YAML-source / JSON-runtime is a deliberate trade-off: YAML block scalars beat JSON escaping for embedded code (his AUTHORING.md complains about escaping backslashes/quotes/newlines) while JSON keeps a fast formal schema gate and a clean runtime load.

*Source:* dsa-workbook validate.mjs + qa.mjs + CI gate; his PLAN.md architecture-contract habit

## Recommendations

- Make YAML the authoring source-of-truth and JSON the runtime artifact: block scalars (|) make embedded code and multi-line prose readable, and his own AUTHORING.md flags JSON escaping as a pain point. Compile YAML->JSON in the gate's first step so the formal JSON Schema still validates the runtime shape.
- Build the gate as two layers, not one: a declarative JSON Schema (ajv) for field shapes + a procedural validator (a validate.mjs sibling) for coverage-closure, referential integrity, gradeable-or-reject, the executable reference-answer checks, and rubric-self-check. A pure JSON Schema cannot execute a reference solution or diff a coverage graph — the interesting guards live in the procedural layer, exactly as his DSA validator's ladder cross-check and figure-token integrity do.
- Discriminate the union on grading.strategy, not on question type, so the grader and the per-type gate checks each have three branches (deterministic / hidden_tests / llm_judge) with a thin per-type adapter on top. This keeps ten UI-level question types over three grading engines.
- Wire the four hard invariants as the definition of done, and make the whole thing one command (`make gate`) that exits non-zero on any error while printing warnings non-blocking — mirror his errors-vs-warnings split and his four-command green gate. Run it in CI on push like the DSA Pages workflow.
- Keep the LLM strictly out of the pass/fail path for code: hidden tests always decide; llm_review is advisory at weight_of_style 0.0 by default. A flaky judge must never fail a solution that passes the tests — his 'LLM calls must never hard-fail the pipeline' rule.
- Bound the authoring self-repair loop (N=3) and QUARANTINE non-reproducing drafts into a review queue rather than dropping or force-committing them — graceful degradation with a surfaced reason, so a batch of 200 auto-authored lessons never silently ships a broken one.
- Pin schema_version and treat it like his PLAN.md architecture contract: the gate refuses unknown/newer versions, and a breaking field change requires an explicit migration + version bump, not a silent rename.

## Proposed modules

### MCQ — deterministic_choice

**Objectives**

- Grading: exact index/text match against the single option with correct:true; no model call; instant feedback surfaces each option's `why`
- Use for: recall and single-concept discrimination (bloom remember/understand)

**Testable skills**

- Gate: exactly one option has correct:true and it is in range
- Gate: every option carries a non-empty `why` rationale (kills giveaway distractors)
- Gate: reference_answer string equals the correct option's text

### multi_select — deterministic_choice

**Objectives**

- Grading: set-equality (partial_credit: all) or Jaccard overlap (partial_credit: jaccard) against the correct-option set
- Use for: 'which of these belong to family X' style analysis

**Testable skills**

- Gate: >=1 option correct:true and >=1 correct:false (a degenerate all-true/all-false is rejected)
- Gate: reference_answer array equals the set of correct-option texts
- Gate: partial_credit is one of {all, jaccard}

### short_answer / definition — llm_judge (keyword_or_rubric)

**Objectives**

- Grading: cheap path first — keyword_must (AND-of-OR groups) / keyword_must_not gate; if inconclusive, fall through to a one-criterion rubric judged by the LLM against pass_threshold
- Use for: one-sentence definitions where a keyword set is 90% sufficient (cost control)

**Testable skills**

- Gate: reference_answer satisfies keyword_must and violates no keyword_must_not
- Gate: reference_answer scores >= pass_threshold under the rubric (rubric-passes-own-reference)
- Gate: keyword groups are non-empty arrays

### explain_tradeoff / design_essay — llm_judge (rubric + reference)

**Objectives**

- Grading: weighted-criteria rubric scored by the LLM judge with the reference_answer supplied as the gold; anti_reward_hacking (min_words, penalize_if_contains) blocks keyword-stuffed non-answers
- Use for: the 'name the trade-off and the rejected alternative' assessments central to his ethos

**Testable skills**

- Gate: criteria weights sum to 1.0 (+/- epsilon)
- Gate: reference_answer non-empty and clears its own rubric at pass_threshold
- Gate: min_words and penalize_if_contains present for essay-length types

### code_completion — hidden_tests

**Objectives**

- Grading: learner fills a starter stub; run against visible + hidden tests in a sandbox; pass = all green within timeout_ms
- Use for: applying a template with the scaffold given (bloom apply)

**Testable skills**

- Gate: EXECUTES reference_solution against all tests — must be green or lesson rejected
- Gate: >=1 visible and >=1 hidden test
- Gate: leak-guard — no hidden test input/expect appears in starter or prompt

### code_from_scratch — hidden_tests (+ optional advisory llm_review)

**Objectives**

- Grading: hidden tests decide pass/fail; optional llm_review adds STYLE commentary at weight_of_style (default 0.0 = comment-only, never overrides the test verdict)
- Use for: full-implementation tasks where design quality matters but correctness is non-negotiable

**Testable skills**

- Gate: EXECUTES reference_solution — must pass all tests
- Gate: if llm_review.enabled, weight_of_style in [0,1]; verdict authority stays with tests
- Gate: >=1 hidden test present

### debug_this — hidden_tests (buggy fails, fix passes)

**Objectives**

- Grading: learner edits provided buggy code; must turn all tests green
- Use for: teaching a specific classic bug (off-by-one, early lock release) by making them feel it

**Testable skills**

- Gate: EXECUTES `buggy` code and asserts it FAILS >=1 test (a fake/no-op bug is rejected)
- Gate: EXECUTES reference_solution and asserts it PASSES all tests
- Gate: buggy and reference_solution are textually different

### predict_output — deterministic_output

**Objectives**

- Grading: exact/trimmed/regex match of learner's predicted stdout against expected_output
- Use for: 'trace this program' comprehension (bloom understand/analyze)

**Testable skills**

- Gate: EXECUTES `program` with `runner` and asserts its stdout equals expected_output — the expected value is machine-DERIVED, never hand-typed (anti-fabrication core)
- Gate: match is one of {exact, trimmed, regex}
- Gate: program terminates within timeout

### critique_design — llm_judge (rubric)

**Objectives**

- Grading: weighted-criteria rubric rewarding (a) naming the flaw and (b) proposing a concrete better alternative; reference_answer as gold
- Use for: evaluating a flawed design — the 'reject a design in writing by naming it' habit

**Testable skills**

- Gate: criteria weights sum to 1.0
- Gate: reference_answer clears its own rubric
- Gate: rubric has >=2 criteria (a critique that's all-or-nothing on one axis is rejected)

### feynman / explain_back — llm_judge (rubric)

**Objectives**

- Grading: rubric scores (a) analogy fidelity and (b) no technical error introduced by the simplification
- Use for: forcing the learner to teach it back — the deepest retention check

**Testable skills**

- Gate: reference_answer supplied and clears its own rubric
- Gate: a 'no error introduced by simplification' criterion is present
- Gate: criteria weights sum to 1.0

## Risks & gotchas

- Reward-hacking on llm_judge types: a learner (or the authoring model itself) can keyword-stuff a rubric. Mitigations built in — anti_reward_hacking.min_words + penalize_if_contains, and the rubric-passes-own-reference check — but rubric quality is still the soft underbelly; budget for periodic human spot-audits of judge scores vs. a held-out human-graded set (his A/B-measurement instinct applies to the grader itself).
- Executable materialization needs a real sandbox (timeout, no network, memory cap, per-language runner). Running untrusted reference solutions AND learner submissions is a container-isolation problem, not a nicety — treat it as the hard part and budget for it; a naive subprocess is an RCE.
- predict_output with nondeterministic programs (dict ordering, timestamps, floats, threads) will make expected_output flaky. Gate should reject programs whose stdout differs across two runs, or force a `match: regex`/normalized comparison — otherwise the anti-fabrication guarantee quietly breaks.
- Coverage-closure can be gamed by declaring a trivially-assessable objective. The adversarial-audit stage (flagging non-discriminating assessments and giveaway distractors) is the counter, but it's advisory — a determined author can still ship shallow-but-green content. The guard proves gradeability, not pedagogical depth.
- LLM-judge cost and latency at scale: keyword_or_rubric short-circuits cheap cases, but essay/critique/feynman types each cost a model call per grade. For a large learner base, cache by (assessment_id, normalized_answer) and consider a smaller judge model — he's already fine-tuned 0.5B judges, so a distilled rubric-grader is in reach.
- YAML-source / JSON-runtime means two representations can drift if anyone hand-edits the compiled JSON. Enforce compile-in-gate and .gitignore the build/ JSON (or commit it but assert it matches a fresh compile) so JSON is never the thing edited.

## Open questions

- Track granularity: one flat lesson namespace with a `track` tag (systems/ai/dsa/...), or per-track directories with their own module tables like the DSA t00-t15 assignment map? The latter gives per-track validate cross-checks against source notes.
- Should hidden-test languages be limited to Python at first (single sandbox runner) or multi-language (C++/Java/Go) from day one? Multi-language multiplies the sandbox and harness surface — recommend Python-first, seam designed for more.
- Judge model choice: hosted API vs. a self-hosted/fine-tuned small grader (he's already GRPO-trained 0.5B judges). Affects cost, determinism, and whether the rubric-self-check can run offline in the gate.
- Is learner state (attempts, scores, spaced-repetition scheduling) in scope for this schema, or strictly authored content? The schema above is content-only; learner progress likely belongs in a separate store keyed by assessment_id.
- Partial-credit policy per deployment: does a multi_select at 3/4 correct count as pass, and do essay sub-threshold scores give any credit or hard-fail? Needs a global grading policy doc, not just per-assessment thresholds.

## Citations

- [dsa-workbook/AUTHORING.md — his content-as-data topic authoring spec (JSON schema, figure-token integrity, no-hardcoded-colors rules)](/home/SammyUrfen/Codes/dsa-workbook/AUTHORING.md)
- [dsa-workbook/scripts/validate.mjs — his procedural green-gate validator (errors vs warnings, referential integrity, source cross-check)](/home/SammyUrfen/Codes/dsa-workbook/scripts/validate.mjs)
- [dsa-workbook/scripts/qa.mjs — Playwright render-QA second gate (missing-figure sentinels, console errors, theme toggle)](/home/SammyUrfen/Codes/dsa-workbook/scripts/qa.mjs)
- [dsa-workbook/.github/workflows — CI gate on push to main (his green-gate-in-CI taste)](/home/SammyUrfen/Codes/dsa-workbook/.github/workflows)

