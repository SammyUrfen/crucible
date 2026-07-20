# Go Language Curriculum (idiom-first, calibrated-beginner)

> Research track. Faithful rendering of the agent's structured findings.

**Dimension:** Go language curriculum design (idiom-first, for a strong systems engineer who is a true Go beginner)

## Summary

A 13-module, build-and-verify Go curriculum that deliberately skips the concepts this learner already owns (concurrency as a discipline, locking, failure modes, system design) and instead drills Go IDIOM: implicit interface satisfaction, errors-as-values, the happens-before memory model, channel-vs-mutex-vs-atomic trade-offs, and the tool-enforced style that C/Java/JS habits fight. Every module names the rejected alternative (the thing he'd reach for from Java/Python) and is gated by a testable, adversarial skill — predict the -race verdict, make an interface unsatisfiable then fix it, break omitempty on a bool — rather than rote recall. The spine is the same primitive-from-scratch pattern he already uses: each module ends in something he can `go test -race` and benchmark, culminating in a capstone that hardens a piece of his conclave SFU. The single highest-leverage early intervention is not a concept but a reflex: gofmt/goimports on save and a golangci-lint gate, which mechanically kills the `var x int = …`, trailing-semicolon, and committed-binary habits before they calcify.

## Key findings

### His concurrency mastery is a teaching accelerant, not something to re-teach — reframe channels/mutex/atomic as syntax for a discipline he owns.

He has shipped 2PL + wait-for-graph deadlock detection, lock-free ConcurrentHashMap+LongAdder aggregation, and JPA @Version optimistic locking. So the goroutine/channel module must NOT explain 'what a race is' — it must answer 'which of Mutex/channel/atomic is idiomatic HERE and why', and force him to predict what -race prints. The novel content is Go's happens-before rules and 'share memory by communicating', not concurrency itself.

*Source:* Learner profile (CLAUDE.md) — concurrency-correctness track record

### The biggest early risk is not misunderstanding Go but writing correct Go non-idiomatically; the fix is mechanical (tooling), not conceptual.

Documented tells: `var x int = ...` over `:=`, trailing semicolons, committed build artifacts, C-like plain style. None are bugs — they're accent. A gofmt/goimports-on-save + golangci-lint pre-commit gate corrects all three mechanically and immediately, so it must come in Module 1, not last.

*Source:* Learner profile — Go proficiency + growth edges

### Implicit interface satisfaction is the single most Java-disorienting idiom and deserves its own module up front.

Coming from Java's explicit `implements`, the structural/duck-typed 'a type satisfies an interface just by having the methods, and the interface is usually declared by the CONSUMER not the producer' rule inverts his instincts. This unlocks 'accept interfaces, return structs' and 'the smallest interface that works' — which then makes the errors, io, and http modules land.

*Source:* Go idiom (Effective Go / 'accept interfaces, return structs')

### Errors-as-values maps cleanly onto his existing {code,message,details} envelope habit — teach it as the Go dialect of a pattern he already reproduces across 4 languages.

He already builds a custom error hierarchy -> one centralized handler -> a structured envelope in C++/Node/Python/Java. Go's version is sentinel errors (errors.Is), typed errors (errors.As), %w wrapping, and a central HTTP error-mapping middleware. Frame it as 'your envelope pattern, minus exceptions' — the discontinuity is 'no try/catch, errors are ordinary return values you must not drop'.

*Source:* Learner profile — structured error handling pattern

### Generics should be taught with a bias toward NOT using them — the idiom is 'reach for an interface first'.

For a strong engineer the temptation is to over-parameterize (C++ template instincts, Java generics). Go's community norm is: use type params only for container/algorithm code where an interface would force allocation or lose type safety (e.g. a generic Map/Filter, a typed sync.Pool, constraints.Ordered). The testable skill is deciding, given a signature, whether generics or an interface is more idiomatic — and defending it.

*Source:* Go generics guidance (when-to-use, go.dev blog norms)

### defer/panic/recover has real nuance he'll get wrong from a Java exceptions mental model, so it needs a dedicated module despite looking trivial.

Gotchas: deferred args evaluate immediately but the call runs LIFO at return; `defer` in a loop leaks until function exit; recover only works in a directly-deferred function; panic is for programmer bugs / unrecoverable state, NOT control flow (unlike Java exceptions). Naming the rejected alternative — 'don't use panic/recover as try/catch' — is the whole lesson.

*Source:* Go idiom — defer/recover semantics

## Recommendations

- Sequence: M1 (idiom+tooling) FIRST and non-negotiable — the gofmt/lint reflex must exist before he writes module code, or every later exercise re-teaches the same accent. Then M2 (interfaces) and M3 (errors) as the conceptual spine, because io/http/testing all assume them.
- Front-load interfaces and errors over concurrency even though concurrency looks like his home turf — the Go-specific discontinuities (implicit satisfaction, errors-as-values, no exceptions) are where a strong non-Go engineer actually stumbles; the goroutine module is fast for him.
- Make every module's exit criterion a `go test -race`-clean, lint-clean artifact he can benchmark — match his 'never say done without verification' and 'numbers over adjectives' values; a module isn't passed until the adversarial testable skill is demonstrated, not read.
- For each 'when to use X' decision (channel vs mutex vs atomic, generics vs interface, wrap vs sentinel), require him to WRITE the rejected alternative and one sentence on why it lost — this matches his DESIGN_NOTES habit and prevents cargo-culting the idiom.
- Anchor the capstone (M13) in conclave so the curriculum produces real value in his active project, not throwaway katas — and so team-visible code gets the idiom pass.
- Skip explicitly: 'what is a race', 'what is a mutex', basic HTTP semantics, what an interface is FOR — teach only Go's SPELLING of these. Signal this skipping up front so he trusts the curriculum respects his level.
- Adopt Go 1.22+ assumptions throughout (loop-var-per-iteration semantics, method+path ServeMux routing) so he doesn't learn deprecated workarounds — flag where pre-1.22 code on the internet will mislead him.

## Proposed modules

### M1 — Idiom Reset: Writing Go That Reads Like Go (+ the tooling loop)

**Objectives**

- Replace C/Java/JS accent with Go defaults BEFORE building anything, so idiom is a reflex not an afterthought
- Internalize zero values, `:=` vs `var`, no trailing semicolons, short receiver/variable names, and error-return-not-throw as the shape of all later code
- Wire gofmt/goimports-on-save + a golangci-lint pre-commit gate so style is machine-enforced, and fix .gitignore so build artifacts are never committed

**Testable skills**

- Given a 40-line file written in his C-like accent (`var x int = 0`, trailing semicolons, Java-style getters, committed binary), reformat it to idiomatic Go and explain each change — verified by `gofmt -d` and `golangci-lint run` both clean
- Predict the zero value of a struct with a slice, map, pointer, and int field, then write code that distinguishes 'absent' from 'zero' (nil map read vs write) without panicking
- State the rule for `:=` vs `var` and produce one case where each is the ONLY idiomatic choice (package-level var, shadowing in `if err :=`)
- Configure a .golangci.yml enabling govet + staticcheck + errcheck + ineffassign and make a repo pass it green; commit a .gitignore that excludes the built binary and prove `git status` is clean after `go build`

### M2 — The Type System & Interfaces (implicit satisfaction)

**Objectives**

- Master structural/implicit interface satisfaction and why the CONSUMER, not the producer, should usually declare the interface
- Design the smallest interface that works ('accept interfaces, return structs'), and know when `any`/type switches are honest vs a code smell
- Understand method sets: value vs pointer receivers and when a *T satisfies an interface but T does not

**Testable skills**

- Write a type that FAILS to satisfy an interface because of a pointer-receiver method set, explain the compiler error, then fix it two ways (take the address vs change the receiver)
- Given a function taking a concrete `*os.File`, refactor its signature to the smallest interface it actually uses (e.g. io.Writer) and prove the call sites still compile
- Implement a `type switch` over `any` for a JSON-ish value decoder, and articulate one case where an interface method would have been more idiomatic than the switch
- Explain nil-interface-vs-nil-pointer: construct the classic bug where a non-nil interface holds a nil pointer and `err != nil` is true unexpectedly; write a test that catches it
- Decide, for three signatures, whether to return a concrete struct or an interface, defending each against the rejected alternative

### M3 — Errors as Values (Is/As, %w, sentinel vs typed, HTTP mapping)

**Objectives**

- Treat errors as ordinary return values that must never be silently dropped — the Go dialect of his existing {code,message,details} envelope
- Choose deliberately between sentinel errors (errors.Is), typed errors (errors.As), and opaque wrapped errors (%w) — and build a custom hierarchy behind one central handler
- Map a domain error hierarchy to HTTP status codes in one place, the way his FastAPI/Spring handlers do

**Testable skills**

- Define a sentinel `ErrNotFound` and a typed `*ValidationError`, wrap them with `fmt.Errorf("...: %w", err)` across three layers, and write tests that recover both with errors.Is and errors.As
- Given a wrapped chain, predict which errors.Is / errors.As calls return true and why (unwrap semantics)
- Build a central `func httpStatus(err error) int` that maps his error hierarchy to 404/400/409/500 via errors.As, and prove it with a table-driven test
- Demonstrate the errcheck failure mode: an ignored error that corrupts state, then show the lint rule that would have caught it
- Argue when NOT to wrap (leaking an internal error type across an API boundary) and rewrite to a sanitized boundary error

### M4 — Goroutines, Channels, select & context (the idiom, not the concept)

**Objectives**

- Express fan-in/fan-out, pipelines, worker pools, and cancellation as Go patterns — mapping each to a concurrency structure he already knows
- Master `select`, done-channels, timeouts, and context propagation/cancellation as the idiomatic replacement for manual coordination
- Know the ownership rule: who creates a channel closes it; never leak a goroutine

**Testable skills**

- Build a bounded worker pool over a channel of jobs with graceful shutdown via context cancellation, and prove with `go test -race` that no goroutine leaks (goleak or a WaitGroup-drain assertion)
- Implement a fan-out/fan-in pipeline with a `done` channel and show that closing `done` unblocks every stage (write the test that would hang if you got it wrong)
- Use `select` with `context.Done()` and a `time.After` timeout in one call site; explain why `context.WithTimeout`+`defer cancel()` is correct and what leaks if you forget cancel
- Reproduce the classic 'send on closed channel' panic and the 'loop-variable captured by goroutine' bug (pre-1.22 semantics), then fix both idiomatically
- Decide for three scenarios whether a channel or a shared-state+Mutex is the idiomatic tool, and name the rejected alternative for each

### M5 — Sync Primitives & the Go Memory Model (happens-before)

**Objectives**

- State Go's happens-before guarantees precisely: what channel ops, Mutex, and sync/atomic promise about visibility across goroutines
- Choose Mutex vs channel vs atomic on idiom + measured cost, not habit — and know why 'atomic for a counter, Mutex for an invariant, channel for ownership transfer' is the default
- Use sync.Once, sync.WaitGroup, sync.RWMutex, and sync/atomic (incl. atomic.Pointer, atomic.Value) correctly

**Testable skills**

- Write a data-race program, predict the exact -race report (which goroutines, which access), then fix it three ways (Mutex, atomic, channel) and benchmark all three under contention with `go test -bench` + `-cpu`
- State the happens-before relationship established by a channel send/receive and by Mutex Unlock/Lock, and construct a case where removing the sync makes a read observe a stale value
- Implement a lock-free counter with atomic.Int64 and show it matches his LongAdder mental model; then show a case where atomic is WRONG because it guards a multi-word invariant
- Use sync.Once for lazy singleton init and prove (via -race) it's safe where a plain nil-check would race
- Given a hot read/rare write struct, justify RWMutex vs atomic.Pointer with a benchmark, naming the rejected alternative

### M6 — defer / panic / recover (nuance)

**Objectives**

- Use defer for cleanup with correct LIFO + immediate-argument-evaluation semantics, and avoid the defer-in-loop leak
- Understand that panic is for programmer bugs / unrecoverable invariants, NOT control flow — the explicit anti-pattern coming from Java exceptions
- Recover only at trust boundaries (goroutine top, request handler) and re-panic or convert to error deliberately

**Testable skills**

- Predict the output of a function with three defers where deferred args reference a variable mutated after the defer statement (evaluated-now vs run-later)
- Show the defer-in-a-loop resource leak (file handles) and fix it by extracting a function or calling Close explicitly
- Write a recover in a directly-deferred function that converts a panic to a returned error; then show why the same recover placed one call deeper does NOT catch it
- Build an HTTP middleware that recovers a panicking handler, logs it, and returns 500 — and a test that asserts the server stays up after a handler panics
- Argue one case where panic IS correct (unrecoverable init / must-not-happen invariant) and one where it's abuse of exceptions-as-control-flow

### M7 — Generics (type params, constraints — and when to avoid)

**Objectives**

- Write type-parameterized functions/types with constraints (comparable, constraints.Ordered, custom method constraints) where they genuinely reduce duplication or allocation
- Default to interfaces first; reach for generics only for containers/algorithms — the idiomatic bias is toward NOT using them
- Understand type inference limits and why generics don't give you Java-style covariance or C++ specialization

**Testable skills**

- Implement generic Map/Filter/Reduce over slices and a generic type-safe Set, then benchmark against an `any`-based version to show the allocation/boxing difference
- Given three signatures, decide generics vs interface and defend it (e.g. a Number sum needs constraints.Ordered; a plain io sink needs an interface)
- Write a constraint requiring a method set (a `~[]byte` underlying-type or method constraint) and explain what type inference can and cannot deduce
- Show a case where generics HURT readability and rewrite it back to an interface, naming why the interface is more idiomatic
- Explain why Go has no generic methods on non-generic types and what that forces in API design

### M8 — encoding/json Edge Cases (omitempty, custom Marshaler, streaming)

**Objectives**

- Control (de)serialization precisely with struct tags, and know omitempty's exact truthiness rules and its failure on bools/zero-but-present values
- Implement custom MarshalJSON/UnmarshalJSON and json.Number for lossless numeric handling
- Stream large payloads with json.Encoder/Decoder instead of Marshal-to-[]byte, and handle unknown/extra fields

**Testable skills**

- Reproduce the omitempty-on-bool trap (false is omitted) and fix it with a *bool or a custom Marshaler; write a test asserting the wire bytes
- Implement UnmarshalJSON for a type that accepts either a string or a number from an external API, with a fallback that never hard-fails (his graceful-degradation habit)
- Show float64 precision loss on a large int and fix it with json.Number or a custom decoder using Decoder.UseNumber()
- Stream-decode a large JSON array with json.Decoder.Token()/Decode() and prove constant memory vs json.Unmarshal
- Use DisallowUnknownFields and explain when strict vs lenient decoding is the right boundary policy

### M9 — net/http Server & Client Internals

**Objectives**

- Understand the server model: one goroutine per request, ServeMux (incl. Go 1.22 method+path patterns), Handler/HandlerFunc, and context lifecycle
- Build clients correctly: a shared, tuned http.Client + Transport (connection pooling, timeouts), never the default client in prod, always close resp.Body
- Compose middleware idiomatically (Handler-wrapping) and propagate cancellation via request context

**Testable skills**

- Write a server with graceful shutdown (srv.Shutdown on SIGINT) and a test using httptest.Server that asserts in-flight requests drain
- Demonstrate the resp.Body-leak bug (no Close / no io.Copy(io.Discard)) exhausting the connection pool, then fix it and show the difference under load
- Configure an http.Client with per-request context timeout AND a Transport with sane MaxIdleConns/IdleConnTimeout, explaining why the default client's zero timeout is a footgun
- Build a chain of middleware (logging, recover, auth) as Handler wrappers and test ordering with httptest
- Use Go 1.22 `r.PathValue` routing (`GET /items/{id}`) and write table-driven handler tests, naming the rejected alternative (a third-party router) and when you'd actually need one

### M10 — Testing: table-driven, -race, benchmarks, fuzzing

**Objectives**

- Write table-driven, deterministic, parallel-safe tests as the default (his existing discipline, in Go form) with t.Run subtests and t.Cleanup
- Run everything under -race in CI; write benchmarks that don't lie (b.ResetTimer, b.ReportAllocs, avoid compiler elision) and fuzz targets for parsers/decoders
- Decide testify vs stdlib deliberately — stdlib + a tiny assert helper as default, testify only where it earns its dependency

**Testable skills**

- Convert a set of assertions into a table-driven test with t.Run subtests and t.Parallel(), and show it still passes under -race
- Write a benchmark that measures a real allocation, using b.ReportAllocs and a sink variable to defeat dead-code elimination; interpret ns/op and allocs/op
- Add a fuzz target for a parser (e.g. his SQL-lexer-style code or a JSON decoder) and let it find a crash/panic input, then add it as a seed corpus
- Inject a FixedClock via an interface (his pattern) so a time-dependent test is deterministic, and prove flakiness is gone
- Argue testify-vs-stdlib for one real test file and justify the choice on his Maintainability-over-dependencies values

### M11 — Modules, Workspaces & Dependency Hygiene

**Objectives**

- Understand go.mod/go.sum, semantic import versioning, minimal version selection (MVS) — and why it differs from npm/Maven resolution
- Use go.work workspaces to develop conclave's multi-module layout locally without replace-directive hacks
- Vet and prune dependencies: go mod tidy, why-a-dep (go mod why), and keeping the graph small on principle

**Testable skills**

- Set up a two-module workspace (e.g. server + shared lib) with go.work and prove local edits to the lib are picked up without a published version
- Explain what go.sum protects against and reproduce a verification failure, then explain MVS by predicting which version go picks given a diamond dependency
- Run go mod tidy on a repo with an unused and a missing dependency and explain each diff line
- Use go mod why to justify (or remove) a transitive dependency, applying his 'small graph' bias
- Explain when a major-version bump forces a /v2 import path and migrate a toy module across it

### M12 — Tooling & the Static-Analysis Gate

**Objectives**

- Make gofmt/goimports non-negotiable and understand what go vet catches that the compiler doesn't
- Configure staticcheck + golangci-lint as a green gate (his 'four-command definition of done' in Go form) and read their findings critically, not cargo-culting
- Add race + vet + lint to CI so the gate runs on every push

**Testable skills**

- Write code that compiles but go vet flags (Printf format mismatch, lost-cancel context, unreachable), and explain each finding
- Assemble a .golangci.yml with a defended linter set (govet, staticcheck, errcheck, ineffassign, gocritic, and one you deliberately DISABLE with a reason)
- Set up a CI workflow (or Makefile target) running `go vet ./... && staticcheck ./... && golangci-lint run && go test -race ./...` and make a repo pass green
- Identify one staticcheck finding that is a false-positive-in-context and suppress it with a justified //nolint comment (WHY, not blanket)
- Measure lint+test wall-clock and decide what belongs in the pre-commit hook vs CI

### M13 — Capstone: Harden a conclave Primitive (build-and-verify)

**Objectives**

- Apply every prior module to a real slice of his own SFU: pick a subsystem (signaling coordinator, the upload meter, goroutine lifecycle, or an error-mapping HTTP boundary) and make it idiomatic + tested
- Produce a small design note naming the rejected alternative for each key decision (channel vs mutex, interface seam, error strategy) — his existing DESIGN_NOTES habit, in Go
- Ship it behind the green gate: -race clean, benchmarked, lint-clean, no committed artifacts

**Testable skills**

- Refactor one conclave subsystem to accept a small interface at its seam (per M2) and add a fake in tests, proving the seam is real
- Take his lock-free upload meter and prove correctness under -race, then benchmark it and report ns/op + allocs/op (numbers, not adjectives)
- Add context-based cancellation to a goroutine lifecycle and prove no leak with goleak or a drain assertion
- Map the signaling layer's domain errors to WebSocket/HTTP responses through one central handler (per M3), tested table-driven
- Write a one-page design note that names, for three decisions, the chosen Go idiom and the rejected alternative — the deliverable that proves the curriculum landed

## Risks & gotchas

- nil-interface-vs-nil-pointer (a non-nil interface value holding a nil concrete pointer) will bite him in error handling — surface it early in M2, not as a footnote.
- The loop-variable capture bug changed semantics in Go 1.22; tutorials and StackOverflow answers are split — he must know his Go version or he'll 'fix' non-bugs and miss real ones.
- Over-engineering risk from his systems background: he may reach for generics/channels where a plain slice+Mutex is idiomatic. The curriculum's 'name the rejected alternative' gate is specifically designed to counter this — but watch for it.
- Benchmarks that lie: compiler dead-code elimination and unset b.ResetTimer produce fantasy numbers; given his 'numbers over adjectives' ethos he'll trust them — M10 must teach the sink-variable + ReportAllocs discipline explicitly.
- goimports vs gofmt: goimports is a superset (manages imports); if he wires only gofmt-on-save he'll still fight import ordering. Specify goimports (or gopls format) in M1.
- Committed-artifact habit is documented and recurring — the .gitignore fix in M1 must be verified with an actual `go build && git status` check, not just described, or it won't stick.
- context misuse: storing a context in a struct, or using context.Value for non-request-scoped data, is a common strong-engineer mistake — call it out in M4 as an anti-pattern with the rejected alternative (explicit parameters).

## Open questions

- Target depth on generics: does he want production-grade constraint design (for a reusable lib) or just enough to read/avoid them? The module assumes the latter bias — confirm.
- Which conclave subsystem should the M13 capstone target — signaling coordinator, upload meter, or the error/HTTP boundary? Picking now lets earlier modules use it as the running example.
- Preference on testify vs stdlib as the house style — the curriculum defaults to stdlib+tiny helper on his Maintainability values, but if the team already uses testify, M10 should invert.
- Does he want a distributed-internals track (raft/gossip/consistency in Go) layered ON TOP after this — this syllabus is language-idiom, not distributed-systems-in-Go, which he may want next given his stated 'go deeper' goal.

## Citations

- [Effective Go — interfaces, errors, concurrency idioms](https://go.dev/doc/effective_go)
- [The Go Memory Model](https://go.dev/ref/mem)
- [Go blog — When To Use Generics](https://go.dev/blog/when-generics)
- [Go blog — Working with Errors in Go 1.13 (Is/As/%w)](https://go.dev/blog/go1.13-errors)
- [Go 1.22 release notes — loop variable and ServeMux routing changes](https://go.dev/doc/go1.22)

