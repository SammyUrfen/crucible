# Go track — ordered lesson backlog after the pilot

The Phase 0 exit criteria (see [`../09-roadmap.md`](../09-roadmap.md)) require "an ordered backlog
of the next ~35 lessons." This is that backlog, compressed from the module table in
[`go.md`](go.md). The pilot (14 lessons, `go04a`–`go05g` under `content/go/`) covers M4–M5, the
concurrency-discrimination vertical. Everything below is **authored only if the pilot passes its
2-week daily-use bar** — otherwise the honest outcome is to stop, not to write more content.

Ordering follows the syllabus rationale: idiom/tooling first (the accent must die before more
code), then the interfaces/errors conceptual spine, then the remaining modules, capstone last.

| # | id (proposed) | Module | Lesson |
|---|---|---|---|
| 1 | go01a-idiom-reset | M1 | The accent pass: `:=` vs `var`, zero values, semicolons — reformat a file written in C/Java accent |
| 2 | go01b-tooling-loop | M1 | goimports-on-save + golangci-lint wired; `.gitignore` proves `go build && git status` clean |
| 3 | go02a-implicit-satisfaction | M2 | Consumer-declared interfaces; satisfaction without `implements` |
| 4 | go02b-method-sets | M2 | Value vs pointer receivers; the type that fails to satisfy via pointer method set, fixed two ways |
| 5 | go02c-nil-interface-trap | M2 | The nil-interface-holding-nil-pointer bug where `err != nil` is true; the test that catches it |
| 6 | go02d-small-interfaces | M2 | Accept interfaces, return structs; designing the smallest interface that works |
| 7 | go03a-errors-as-values | M3 | The error return as his `{code,message,details}` envelope minus exceptions; never drop an error |
| 8 | go03b-wrapping | M3 | `%w`, `errors.Is`/`As` across three layers; sentinel vs typed chosen deliberately |
| 9 | go03c-error-boundaries | M3 | Central `httpStatus(err)` table-driven mapping; when wrapping leaks an internal type and must stop |
| 10 | go03d-error-hygiene | M3 | Errors in concurrent code: one writer per error var, error channels, mini-errgroup revisited |
| 11 | go06a-defer-mechanics | M6 | LIFO order + immediate argument evaluation; the three-defers prediction |
| 12 | go06b-defer-in-loops | M6 | The file-handle leak; per-iteration func extraction |
| 13 | go06c-panic-recover | M6 | Panic ≠ control flow; recover at trust boundaries only; why one frame deeper misses it |
| 14 | go07a-generics-when | M7 | Type params + constraints where they cut duplication; interfaces-first bias |
| 15 | go07b-generics-costs | M7 | `any`-boxing vs instantiation benchmark; a case where generics hurt readability, rewritten back |
| 16 | go08a-json-tags | M8 | Struct tags; `omitempty` truthiness and the bool trap (`*bool` / custom Marshaler, wire bytes asserted) |
| 17 | go08b-json-numbers | M8 | float64 precision loss on big ints; `json.Number`; string-or-number UnmarshalJSON fallback |
| 18 | go08c-json-streaming | M8 | `Encoder`/`Decoder` over `Marshal` for streams; token-level decoding |
| 19 | go09a-http-server-model | M9 | Goroutine-per-request; Go 1.22 method+path ServeMux; handler/context lifecycle |
| 20 | go09b-http-client-discipline | M9 | Shared tuned Transport, never default client; the `resp.Body` leak exhausting the pool |
| 21 | go09c-graceful-shutdown | M9 | `Shutdown` on SIGINT draining in-flight requests, proven via `httptest` |
| 22 | go09d-middleware | M9 | Handler-wrapping composition; the rejected third-party router and when it earns its place |
| 23 | go10a-table-driven | M10 | Table-driven parallel-safe tests + injected `FixedClock` (his pattern, Go spelling) |
| 24 | go10b-benchmarks | M10 | `b.ReportAllocs`, sink variables vs dead-code elimination, reading ns/op honestly |
| 25 | go10c-fuzzing | M10 | A fuzz target that finds a crash input in a parser; seeding the corpus |
| 26 | go11a-modules-mvs | M11 | `go.mod`/`go.sum`; minimal version selection vs npm/Maven; the diamond-dependency prediction |
| 27 | go11b-workspaces | M11 | `go.work` for conclave's multi-module layout (rejected: scattered `replace` directives) |
| 28 | go12a-vet-catches | M12 | Code that compiles but `go vet` flags: Printf mismatch, lost-cancel, unreachable |
| 29 | go12b-lint-gate | M12 | A defended `.golangci.yml` (one linter disabled with a reason); the four-command green gate in Go |
| 30 | go04h-pipelines | M4 depth | Multi-stage pipelines: bounded fan-in, cancellation propagation through stages |
| 31 | go04i-timers | M4 depth | `time.Timer`/`Ticker` correctness: Stop-drain idiom, `time.After` in loops revisited |
| 32 | go05h-sync-map-sharding | M5 depth | `sync.Map`'s narrow niche vs sharded mutexed maps; when either beats RWMutex |
| 33 | go13a-conclave-seam | M13 | Refactor one conclave subsystem to accept a small interface at its seam, fake in tests |
| 34 | go13b-conclave-meter-bench | M13 | Benchmark the real upload meter: ns/op + allocs/op reported, design note with rejected alternative |
| 35 | go13c-conclave-lifecycle-audit | M13 | Context-cancellation audit of one real goroutine lifecycle, leak-free proof + one-page design note |

## Authoring cost (to be measured, honestly)

The pilot's 14 lessons were AI-authored + adversarially reviewed in one session with the
executable `verify` pass as the gate; the wall-clock and per-lesson agent cost of that run is
recorded in the session log, but it is **not** the number the roadmap asks for — the roadmap
wants *his* hours-per-lesson for hand-authoring/curation, which only the 2-week pilot can
produce (each time a lesson needs editing, note the minutes). Until that number exists, treat
the 35-lesson backlog duration as **unknown**, not "fast because AI."

## Limitations

- Ids past the pilot are proposals; the M7 generics depth question and the M13 capstone target
  (upload meter assumed) are still the open questions flagged in [`go.md`](go.md).
- This backlog is the language-idiom track only — the distributed-systems-in-Go track (R6:
  orchestrated over Maelstrom/Gossip Glomers) is deliberately not smuggled in here.
