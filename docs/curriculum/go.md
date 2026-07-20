# Go Curriculum — idiom-first, calibrated-beginner

This doc is the syllabus for Crucible's **Go** track: 13 build-and-verify modules that
deliberately skip the concepts you already own and drill the *idiom* a strong non-Go engineer
actually stumbles on. It defines the modules, their objectives, the adversarial testable skill that
gates each one, prerequisites, a suggested ordering, and the conclave hooks. It is the language-idiom
track only — not distributed-systems-in-Go (see the open question at the end).

## What this track teaches, and what it refuses to

You have shipped strict 2PL with wait-for-graph deadlock detection, lock-free
`ConcurrentHashMap`+`LongAdder` aggregation, and `@Version` optimistic locking. So this curriculum
does **not** teach "what a race is," "what a mutex is for," or basic HTTP semantics. Concurrency is a
discipline you already hold; Go is new *spelling* for it. Signalling that refusal up front is itself a
design choice — the rejected alternative is a from-first-principles concurrency course, which would
insult your level, waste your 25-minute sessions, and (the real failure mode) make you distrust that
the track is calibrated to you and quietly disengage.

What is genuinely new, and therefore what every module is built around:

- **Implicit interface satisfaction** — a type satisfies an interface by having the methods, and the
  interface is usually declared by the *consumer*, not the producer. Coming from Java's explicit
  `implements`, this inverts your instincts and is the single most disorienting idiom (M2).
- **Errors as ordinary return values** — no `try`/`catch`; an error is a value you must not drop. This
  maps cleanly onto the `{code, message, details}` envelope you already reproduce across C++/Node/
  Python/Java. Frame: *your envelope pattern, minus exceptions* (M3).
- **Go's happens-before memory model** and "share memory by communicating" — the novel content in
  concurrency is not the concurrency, it is which of Mutex / channel / atomic is idiomatic *here* and
  what `-race` will actually print (M4, M5).
- **The tool-enforced style** that C/Java/JS habits fight — corrected mechanically, not by willpower
  (M1, M12).

### The altitude ramp

The track ramps from a **scaffolded on-ramp** to **from-scratch primitives under `go test -race`**.
M1 hands you a broken file and a lint config to fix — low altitude, fast wins, tooling wired before you
write anything. By M5 you are predicting the exact `-race` report and defending a Mutex-vs-atomic
choice with a benchmark. By M13 you are hardening a real slice of your own SFU behind a green gate.
This is the same primitive-from-scratch spine you already use elsewhere; the ramp exists only so the
*accent* is fixed before the hard modules, not so the modules are easy.

### The one highest-leverage intervention is a reflex, not a concept

The biggest early risk is not misunderstanding Go — it is writing *correct* Go *non-idiomatically*, and
that fix is mechanical. Three documented tells, and how each dies in M1:

| Habit (from C/Java/JS) | Why it's wrong in Go | Mechanical fix |
|---|---|---|
| `var x int = 0` where `:=` fits | verbose; `var` is for zero-value or package-level decls | **goimports/gofmt on save** normalizes; `:=` becomes reflex |
| trailing semicolons | the lexer inserts them; hand-written ones are noise | gofmt strips them; you stop typing them within a week |
| committing the built binary | `go build` drops an artifact next to source | `.gitignore` the binary; **verify with `go build && git status` clean**, not just described |

None of these are *bugs* — they are accent. But if M1 comes last, every later exercise re-teaches the
same accent, so M1 is non-negotiably first. One precision from the research: wire **goimports** (or
`gopls format`), not bare **gofmt** — gofmt does not manage import ordering, so a gofmt-only setup
leaves you fighting imports by hand.

## The modules

Objectives and testable skills below are compressed from the track research; the exit criterion for
every module is the same shape — a `go test -race`-clean, lint-clean artifact you can benchmark, with
the adversarial skill **demonstrated, not read**. A module is not passed until you have made the failure
mode happen and then fixed it.

| Module | Objectives (WHY) | Gating testable skill (adversarial) | Prereqs |
|---|---|---|---|
| **M1 — Idiom Reset + the tooling loop** | Replace C/Java/JS accent with Go defaults *before* building; make style machine-enforced so idiom is a reflex, not an afterthought. Internalize zero values, `:=` vs `var`, no semicolons, short receiver names. | Reformat a 40-line file written in your accent (`var x int = 0`, trailing `;`, Java-style getters, committed binary) to idiomatic Go and explain each change — verified by `gofmt -d` **and** `golangci-lint run` both clean; then commit a `.gitignore` and prove `git status` is clean after `go build`. | none |
| **M2 — Type system & interfaces (implicit satisfaction)** | Master structural satisfaction and why the *consumer* declares the interface; design the smallest interface that works ("accept interfaces, return structs"); understand value-vs-pointer method sets. | Write a type that **fails** to satisfy an interface via a pointer-receiver method set, explain the compiler error, fix it two ways (take the address vs change the receiver); then construct the **nil-interface-holding-nil-pointer** bug where `err != nil` is unexpectedly true and write the test that catches it. | M1 |
| **M3 — Errors as values (`Is`/`As`, `%w`, sentinel vs typed)** | Treat errors as return values that are never silently dropped — the Go dialect of your envelope; choose deliberately between sentinel (`errors.Is`), typed (`errors.As`), and wrapped (`%w`); map a domain hierarchy to HTTP codes in **one** place. | Wrap a sentinel `ErrNotFound` and a typed `*ValidationError` across three layers, recover both with `errors.Is`/`errors.As` in tests; build a central `func httpStatus(err error) int` proven table-driven; then argue one case where wrapping is **wrong** (leaking an internal type across a boundary) and sanitize it. | M2 |
| **M4 — Goroutines, channels, `select` & context (idiom)** | Express fan-in/out, pipelines, worker pools, cancellation as Go patterns mapped to structures you already know; master `select`, done-channels, context propagation; know the ownership rule (who creates a channel closes it). | Build a bounded worker pool with graceful shutdown via context cancellation, prove **no goroutine leak** under `-race` (goleak or a drain assertion); reproduce the "send on closed channel" panic and the loop-var-capture bug (pre-1.22), fix both; **decide channel vs Mutex for three scenarios and name the rejected alternative for each**. | M1 |
| **M5 — Sync primitives & the Go memory model (happens-before)** | State Go's happens-before guarantees precisely (channels, Mutex, `sync/atomic`); choose Mutex vs channel vs atomic on idiom + *measured* cost; use `sync.Once`/`WaitGroup`/`RWMutex`/`atomic.Pointer` correctly. | Write a data-race program, **predict the `-race` report** (which goroutines, which access — reported as probabilistic, see below), fix it three ways (Mutex, atomic, channel) and **benchmark all three under contention** (`-bench -cpu`); then show a case where atomic is *wrong* because it guards a multi-word invariant. | M4 |
| **M6 — `defer` / `panic` / `recover` (nuance)** | Correct LIFO + immediate-arg-evaluation `defer`; know panic is for programmer bugs / unrecoverable invariants, **not** control flow (the explicit anti-pattern from Java exceptions); recover only at trust boundaries. | Predict the output of a function with three defers whose args reference a later-mutated variable; show the defer-in-a-loop file-handle leak and fix it; write a recover that converts a panic to a returned error, then show why the same recover one call deeper does **not** catch it. | M3 |
| **M7 — Generics (type params, constraints — and when to avoid)** | Write parameterized code with constraints where it genuinely cuts duplication/allocation; **default to interfaces first** — the idiomatic bias is toward *not* using generics; understand inference limits (no Java covariance, no C++ specialization). | Implement generic `Map`/`Filter`/`Reduce` + a type-safe `Set`, benchmark against an `any`-based version to show the boxing/allocation difference; given three signatures, decide generics vs interface and defend each; then show a case where generics *hurt* readability and rewrite back to an interface. | M2 |
| **M8 — `encoding/json` edge cases** | Control (de)serialization with struct tags; know `omitempty`'s exact truthiness rules and its failure on bools; custom `Marshaler`/`json.Number`; streaming with `Encoder`/`Decoder`. | Reproduce the **`omitempty`-on-bool trap** (`false` is omitted) and fix with `*bool` or a custom Marshaler, asserting the wire bytes; implement `UnmarshalJSON` accepting either string or number from an external API with a fallback that never hard-fails; show float64 precision loss on a large int and fix with `json.Number`. | M2 |
| **M9 — `net/http` server & client internals** | Server model (one goroutine per request, Go 1.22 method+path `ServeMux`, handler/context lifecycle); build clients with a shared tuned `Transport`, never the default client, always close `resp.Body`; compose middleware by handler-wrapping. | Demonstrate the `resp.Body`-leak bug exhausting the connection pool, then fix and show the difference under load; write a server with graceful `Shutdown` on SIGINT proven to drain in-flight requests via `httptest.Server`; route with `r.PathValue` and name the rejected alternative (a third-party router) and when you'd actually need one. | M3, M4 |
| **M10 — Testing: table-driven, `-race`, benchmarks, fuzzing** | Table-driven parallel-safe tests as default (your discipline, in Go form); run everything under `-race`; write benchmarks that **don't lie**; fuzz parsers/decoders; decide testify vs stdlib deliberately. | Write a benchmark measuring a real allocation using `b.ReportAllocs` and a **sink variable to defeat dead-code elimination**, interpret ns/op and allocs/op; inject a `FixedClock` via an interface (your pattern) to kill flakiness; add a fuzz target that finds a crash input and seed it. | M2, M3 |
| **M11 — Modules, workspaces & dependency hygiene** | `go.mod`/`go.sum`, semantic import versioning, **minimal version selection** and why it differs from npm/Maven; `go.work` for conclave's multi-module layout; prune the graph (`go mod tidy`, `go mod why`). | Set up a two-module `go.work` workspace and prove local lib edits are picked up without a published version; reproduce a `go.sum` verification failure and explain what it protects; predict which version MVS picks given a diamond dependency. | M1 |
| **M12 — Tooling & the static-analysis gate** | Make gofmt/goimports non-negotiable; know what `go vet` catches that the compiler doesn't; run staticcheck + golangci-lint as a green gate (your "four-command definition of done", in Go); add race+vet+lint to CI. | Write code that compiles but `go vet` flags (Printf mismatch, lost-cancel context, unreachable) and explain each; assemble a defended `.golangci.yml` including **one linter you deliberately disable with a reason**; make a repo pass `go vet ./... && staticcheck ./... && golangci-lint run && go test -race ./...` green. | M1, M10 |
| **M13 — Capstone: harden a conclave primitive** | Apply every prior module to a real slice of your SFU; produce a design note naming the rejected alternative per decision (your DESIGN_NOTES habit, in Go); ship behind the green gate. | Refactor one conclave subsystem to accept a small interface at its seam (M2) with a fake in tests; take the **lock-free upload meter**, prove correctness under `-race`, benchmark it and report ns/op + allocs/op; add context cancellation to a goroutine lifecycle proven leak-free; write a one-page note naming, for three decisions, the chosen idiom and the rejected alternative. | all |

### One precision on the `-race` gate (per Crucible resolution R4)

The M5 "predict the `-race` report" skill is **probabilistic, and reported as such** — not a clean
deterministic oracle. `go test -race` has false negatives (it only reports interleavings it actually
observes), and Go randomizes map-iteration order. So the canonical
[`predict_race_verdict`](../../content/examples/go04-concurrency-discrimination.yaml) item runs the
construction over **N ≫ 2 iterations** with a reliably-tripping race, and is graded as a probabilistic
signal with its confidence stated — never as "expected: DATA RACE, guaranteed." Do not let the module
overclaim determinism; the honest framing is the teaching point.

## Suggested ordering

The research is explicit and I follow it: **front-load interfaces and errors over concurrency, even
though concurrency looks like home turf.** The Go-specific discontinuities — implicit satisfaction,
errors-as-values, no exceptions — are where a strong non-Go engineer actually stalls; the goroutine
module is *fast* for you precisely because you own the discipline.

1. **M1** — idiom + tooling. First and non-negotiable; the gofmt/lint reflex must exist before any
   module code, or every later exercise re-teaches the accent.
2. **M2 → M3** — interfaces then errors: the conceptual spine. io, http, and testing all assume them.
3. **M4 → M5** — the concurrency pair (the vertical-slice anchor; see below).
4. **M6 → M7 → M8** — defer/panic, generics-with-a-bias-to-avoid, json edge cases.
5. **M9 → M10 → M11 → M12** — http internals, testing discipline, module hygiene, the static gate.
6. **M13** — the conclave capstone, once the rest is in hand.

The rejected ordering is *concurrency-first* (the intuitive "start where he's strong" move). It loses
because it front-loads the module you'll clear fastest and defers the ones that actually change how you
write Go — you'd write idiomatic goroutines wrapped in non-idiomatic interfaces and error handling.

### The concurrency-discrimination module is the vertical-slice anchor

**M4–M5 (goroutines/channels + the memory model) is Crucible's first end-to-end vertical slice**, tied
to conclave. It is the concurrency-*discrimination* module — its whole gating skill is *discriminating*
Mutex vs channel vs atomic and naming the rejected alternative, not writing concurrency. Its canonical
lesson, schema and all, is the worked example at
[`../../content/examples/go04-concurrency-discrimination.yaml`](../../content/examples/go04-concurrency-discrimination.yaml);
that file is the source of truth for lesson field names, and this syllabus should not invent a competing
schema. Building this slice first proves the teach→test loop on the module where your existing mastery
makes the *idiom* discontinuity cleanest to isolate.

### conclave mapping

Several modules use conclave as their running example so the curriculum produces real value in your
active project rather than throwaway katas:

- **M4/M5** — the goroutine lifecycle and the lock-free upload meter are direct conclave subsystems; the
  `context`+`WaitGroup` leak-free pattern is already how conclave shuts down.
- **M9** — the signaling coordinator's HTTP/WebSocket boundary and graceful shutdown.
- **M11** — `go.work` is the honest fix for conclave's multi-module local dev (rejected alternative:
  scattered `replace` directives).
- **M13** — the capstone hardens one real conclave subsystem end-to-end and gives team-visible code the
  idiom pass.

## Assumptions and cross-references

- **Go 1.22+ throughout** — per-iteration loop-variable semantics and method+path `ServeMux` routing are
  assumed. Where pre-1.22 code on the internet will mislead you (loop-var "fixes" for non-bugs, hand-rolled
  routers), the module flags it. Know your Go version or you'll fix non-bugs and miss real ones.
- **`testify` vs stdlib** defaults to **stdlib + a tiny assert helper** on your Maintainability-over-
  dependencies values; M10 inverts only if the team already standardized on testify.
- Grading and gate mechanics for this track live in the sibling feature spec —
  [`../02-features.md`](../02-features.md) — which owns how a lesson's deterministic `go test` and the
  design-defense judge are wired. The raw research this syllabus compresses is at
  [`../../RESEARCH/go-curriculum.md`](../../RESEARCH/go-curriculum.md).

## Limitations / open questions

- **This is a language-idiom track, not distributed-systems-in-Go.** It does not teach Raft/gossip/
  consistency implemented in Go. Given your stated "go deeper" goal, a distributed-internals track layered
  *on top* is the likely next step — but it is out of scope here and should not be smuggled into M13.
- **Generics depth is assumed shallow-by-design.** M7 biases toward *reading and avoiding* generics, not
  production-grade constraint design for a reusable library. If you want the latter, M7 needs to roughly
  double. Confirm before authoring.
- **The M13 capstone target is unpinned.** Signaling coordinator vs upload meter vs error/HTTP boundary —
  picking one now lets M4–M9 use it as the running example instead of three competing ones. Currently the
  upload meter is the assumed anchor (it's the cleanest `-race` + benchmark story); confirm.
- **What "passed" proves is bounded.** Clearing a module demonstrates the adversarial skill on a small
  artifact under `-race` — it does not prove production readiness of conclave, and a green `-race` run is a
  probabilistic absence-of-observed-race, not a proof of race-freedom (R4). The syllabus should not let a
  passed module imply more than that.
