# LLM Grading Infrastructure — Claude Code Headless vs Anthropic API

> Research track. Faithful rendering of the agent's structured findings.

**Dimension:** LLM-based Grading Infrastructure: Claude Code (Headless) vs Claude API (Direct) for Local Evaluation

## Summary

For a programmatic LLM grader invoked locally from Python or Go subprocess, Claude Code in headless mode (`claude -p --bare`) offers the most complete out-of-the-box solution: cost tracking per invocation, structured JSON output, tool restrictions, deterministic models (no temperature sampling on recent Claude versions), and session persistence. The Anthropic Messages API offers lower-level control and batch discounts but requires you to implement grading harness, tool execution, and cost tracking yourself. For a local grader in locked-down CI/test environments, Claude Code bare mode is recommended: self-contained, needs only ANTHROPIC_API_KEY, supports `--disallowed-tools` to prevent code execution, accepts rubric/system prompts via `--append-system-prompt`, returns cost and session metadata in JSON. The API is preferable for sub-second latency, batch processing (50% discount), or hosted agents.

## Key findings

### Claude Code -p mode with --output-format json returns structured, machine-parseable grading results

Command: claude -p 'grade this submission' --output-format json. Returns JSON object with fields: result (text response), session_id (UUID for resuming), total_cost_usd (float estimate), and optionally structured_output if --json-schema provided. The result field contains grading text; nest JSON rubric in system prompt for strict grading. Exit code 0 on success, non-zero on failure or --max-turns limit breach. Example: claude -p --bare 'Grade this' --output-format json | jq '.total_cost_usd'

*Source:* https://code.claude.com/docs/en/headless.md; https://code.claude.com/docs/en/cli-reference.md

### Tool restrictions via --disallowed-tools prevent code execution in grading sandboxes

Command: claude -p --bare 'grade this' --disallowed-tools 'Bash,Edit' restricts Claude to Read-only operations. Bare tool names remove from context; scoped rules deny only matching patterns. Example: --disallowed-tools 'Bash(python *)' denies Bash calls starting with python but allows git commands. Use --tools '' to disable all tools. For pre-approving safe operations in CI: --allowed-tools 'Read,Bash(git log *)'. Grading loop should never allow Bash, Edit, or Glob tools.

*Source:* https://code.claude.com/docs/en/cli-reference.md; https://code.claude.com/docs/en/headless.md

### System prompt and rubric injection via --append-system-prompt or --system-prompt-file

Command: claude -p 'submission' --append-system-prompt 'You are a grader. Return JSON {score: 0-100, feedback: string}'. OR read from file: --append-system-prompt-file rubric.txt. Appends to default Claude Code prompt; --system-prompt replaces entirely (loses Claude Code context). For grading: use --append-system-prompt to inject rubric while keeping Claude's built-in behavior. File approach better for large rubrics: echo '{grade schema...}' > rubric.txt && claude -p --bare --append-system-prompt-file rubric.txt 'submission'

*Source:* https://code.claude.com/docs/en/cli-reference.md

### Model selection and determinism: latest Claude models (Opus 4.8+) removed temperature/sampling parameters

Command: claude -p --model claude-opus-4-8 'grade this'. Models claude-opus-4-8, claude-sonnet-5, claude-haiku-4-5 no longer support temperature, top_p, or top_k; these are only available on older models (Opus 4.6 and earlier). Responses are intrinsically more deterministic on newer models. For grading reproducibility, use claude-opus-4-8 or claude-sonnet-5. Temperature removal is a breaking change on Messages API for these models; requests setting temperature return 400 error. For deterministic grading across runs, rely on exact same prompt+model+input, not temperature pinning.

*Source:* https://platform.claude.com/docs/en/about-claude/models/overview.md; https://platform.claude.com/docs/en/build-with-claude/working-with-messages.md

### Cost tracking per grading invocation returned in --output-format json

Command: claude -p --bare 'grade submission' --output-format json returns total_cost_usd (float estimate of this invocation's cost). Parse with: python: json.loads(subprocess.check_output([...]))["total_cost_usd"]. Go: json.Unmarshal(out, &result) on type with TotalCostUSD float64 field. Estimates are client-side (bundled pricing table), not authoritative; for billing, use Admin API. Includes input/output token breakdowns under usage field if available. Cost is per-call, not cumulative; resume sessions with --resume SESSION_ID for multi-turn grading and accumulate costs separately.

*Source:* https://code.claude.com/docs/en/headless.md; https://code.claude.com/docs/en/agent-sdk/cost-tracking.md

### --json-schema enforces grading output to match schema, prevents invalid JSON

Command: claude -p 'grade this' --output-format json --json-schema '{"type":"object","properties":{"score":{"type":"number","minimum":0,"maximum":100},"feedback":{"type":"string"}},"required":["score","feedback"]}' ensures response conforms to schema. Invalid schema returns error exit code 1 with diagnostic. Response payload includes structured_output field with parsed JSON (not just text in result). First request compiles grammar (added latency); subsequent requests cache for 24h. Use for strict grading: grade output automatically conforms to expected field names/types, no post-processing needed. Not supported: recursive schemas, string length constraints.

*Source:* https://code.claude.com/docs/en/headless.md; https://platform.claude.com/docs/en/build-with-claude/structured-outputs.md

### --bare mode ensures consistent CI behavior by skipping hook/MCP/settings discovery

Command: claude --bare -p 'grade this' skips auto-discovery of SessionStart hooks, skills, MCP servers, plugins from .claude/, ~/.claude/, .mcp.json, settings.json. Useful in CI where local config shouldn't affect results. Pass explicit context via flags: --append-system-prompt, --settings JSON, --mcp-config file, --agents JSON. Startup time faster. Bare mode still requires ANTHROPIC_API_KEY or apiKeyHelper in --settings. Recommended for grading: always use --bare in scripts/CI to guarantee reproducibility.

*Source:* https://code.claude.com/docs/en/headless.md

### --max-turns limits agentic loop iterations, exits with error if exceeded

Command: claude -p 'grade this' --max-turns 3 allows at most 3 request-response cycles. If limit reached, Claude Code exits with non-zero code and an error. Useful to prevent grading loops from running indefinitely (e.g., grader keeps second-guessing). For single-turn grading, omit or set to 1. Multi-turn grading (clarification rounds) can use higher limits but increases latency and cost.

*Source:* https://code.claude.com/docs/en/cli-reference.md; https://code.claude.com/docs/en/headless.md

### Session/resume for multi-turn grading workflows: --resume SESSION_ID or --continue

Command: session_id=$(claude -p 'start grade' --output-format json | jq -r .session_id) && claude -p 'continue grade' --resume "$session_id". Each --resume call is a separate invocation with its own cost; accumulate total_cost_usd across all calls. Scoped to cwd and git worktrees. Use --session-id UUID to explicitly set session or --fork-session to branch. For multi-turn grading: first pass grades initial submission, second pass refines after follow-up. Cost tracking: sum per-call total_cost_usd.

*Source:* https://code.claude.com/docs/en/headless.md; https://code.claude.com/docs/en/cli-reference.md

### Parsing grading results from Python subprocess with JSON

Python example: import subprocess, json; result = json.loads(subprocess.check_output(['claude', '-p', '--bare', '--output-format', 'json', 'grade this'])); print(result['total_cost_usd'], result['result']). For structured output (--json-schema): data = result.get('structured_output'). Exit code handling: try/except CalledProcessError for non-zero exits. Set env ANTHROPIC_API_KEY before calling. Stdin piping: echo 'submission' | subprocess.run([...], input=data, text=True). Parse stderr separately for warnings/retries.

*Source:* https://code.claude.com/docs/en/headless.md

### Parsing grading results from Go subprocess with JSON

Go example: cmd := exec.CommandContext(ctx, 'claude', '-p', '--bare', '--output-format', 'json', 'grade this'); out, _ := cmd.Output(); type Result struct { TotalCostUSD float64 `json:"total_cost_usd"`; Result string `json:"result"`; }; var r Result; json.Unmarshal(out, &r). Handle errors: cmd.Err != nil for exec errors, check exit code with cmd.ProcessState.ExitCode(). Stdin: cmd.Stdin = bytes.NewReader(submission). Set cmd.Env to pass ANTHROPIC_API_KEY. Parse stderr with StderrPipe() for debug output.

*Source:* https://code.claude.com/docs/en/headless.md

### Latency: single-turn grading typically 2-5s; first structured output call has grammar compilation overhead (~1-2s extra)

Claude Code -p print mode endpoint-to-endpoint: ~2-5s for text response (includes API round-trip, token processing). Structured output (--json-schema) first call: add 1-2s for grammar compilation; subsequent calls reuse cached grammar for 24h (nearly same latency as text). Model latency hierarchy: haiku-4.5 (fastest, ~2s), sonnet-5 (~3-4s), opus-4.8 (slowest, ~4-5s). Bare mode eliminates hook startup (~0.5-1s), so recommended for tight latency SLAs. For batch grading, aggregate into multi-turn sessions to amortize startup cost.

*Source:* https://code.claude.com/docs/en/headless.md; https://platform.claude.com/docs/en/about-claude/models/overview.md

### Anthropic Messages API: direct model access, no built-in tools, requires manual tool execution or Tool Runner helper

API call: curl https://api.anthropic.com/v1/messages -d '{"model":"claude-opus-4-8","max_tokens":1024,"messages":[{"role":"user","content":"grade this"}]}' returns JSON with content (text), usage (input/output tokens), model, stop_reason. No built-in Read/Edit/Bash tools. For tools: define tool schemas, check stop_reason=tool_use, call tools yourself, append results as user message, loop. Tool Runner (beta, SDK helper) automates loop with approval callbacks. Structured outputs: pass output_config={"format":{"type":"json_schema","schema":{...}}}. Cost: estimate from usage tokens × model pricing; authoritative via Admin API. Pricing: Opus-4.8 \$5/MTok input, \$25/MTok output; Sonnet-5 \$3/\$15; Haiku-4.5 \$1/\$5.

*Source:* https://platform.claude.com/docs/en/build-with-claude/working-with-messages.md; https://platform.claude.com/docs/en/agents-and-tools/tool-use/tool-runner.md; https://platform.claude.com/docs/en/about-claude/models/overview.md

### Prompt caching on Messages API: cache system prompt + context for 25% input cost reduction after first write

API parameter: cache_control={"type":"ephemeral"} on last message of system/user content before first tool-calling turn. Caches input_tokens at higher write rate (90% of normal input cost) but subsequent cache_read_input_tokens charged at 10% of normal rate, net 25% saving for repeated content. 5-minute TTL by default (1-hour on Claude subscriptions, 10-minute on Bedrock/Vertex). Agent SDK auto-enables caching; Claude Code bare mode doesn't expose caching flag. For grading rubric reuse: cache system prompt + rubric on first call, subsequent calls read from cache. First call overhead, but saves on repeated grading batches.

*Source:* https://platform.claude.com/docs/en/build-with-claude/prompt-caching.md

### Managed Agents vs Tool Runner vs Agent SDK: three deployment models with different trade-offs

Managed Agents (platform.anthropic.com): server-hosted agent loop with Anthropic-managed sandbox, file mounts, Skills + MCP support, SSE event stream, $0.01/min runtime + token costs. You don't run the harness. Best for long-running tasks. Tool Runner (SDK helper, beta): you host the harness loop, SDK auto-executes your defined tools with approval/error hooks, per-turn interception, streaming, no built-in tools. Best for custom grading with fine-grained control. Agent SDK (claude-agent-sdk package): you host full Claude Code harness (built-in tools Read/Edit/Bash/Glob/Grep/WebSearch/WebFetch, hooks, MCP, subagents, sessions) via CLI or Python/TypeScript SDK. Best for local grader needing Read/Bash without re-implementing them. For local grading: use Claude Code -p (Agent SDK CLI surface) or Agent SDK package, not Tool Runner or Managed Agents.

*Source:* https://platform.claude.com/docs/en/managed-agents/overview.md; https://platform.claude.com/docs/en/agents-and-tools/tool-use/tool-runner.md; https://code.claude.com/docs/en/agent-sdk/overview.md

### Exit codes and error handling: 0 on success, non-zero on failure; SIGTERM (143) on external kill

Claude Code -p exit codes: 0 (success), 1 (error, API failure, invalid args, --max-turns exceeded), 2 (stdin unreadable), 143 (SIGTERM received, e.g., killed by timeout supervisor). Python subprocess.CalledProcessError.returncode captures non-zero. Go cmd.ProcessState.ExitCode() returns code. Stderr includes diagnostics (retries, hook errors, auth failure). For grading: catch exit code != 0, log stderr, fail the grade. --max-turns limit returns exit 1 with 'limit reached' message.

*Source:* https://code.claude.com/docs/en/headless.md

## Recommendations

- Use Claude Code `claude --bare -p --output-format json` for all local programmatic grading. It is self-contained, needs only ANTHROPIC_API_KEY, includes cost tracking, and guarantees reproducible behavior across CI runs.
- Always pass --disallowed-tools 'Bash,Edit,Glob' to prevent sandboxing escapes or file mutations during grading. Restrict to Read-only if possible.
- Encode the grading rubric as JSON in --append-system-prompt or a file. For strict output format, use --json-schema to enforce structured output schema and eliminate post-hoc JSON parsing.
- For batch grading (e.g., 100 submissions), prefer Claude Code sessions (--resume) over independent invocations: accumulate cost from multiple `total_cost_usd` fields. Multi-turn sessions amortize startup cost (~0.5s per turn in bare mode).
- Parse JSON output with Python's json.loads(subprocess.check_output(...)) or Go's encoding/json.Unmarshal(...). Always check exit code and handle stderr; retries and auth failures appear there.
- For deterministic grading (exact same output across runs), use claude-opus-4-8 or claude-sonnet-5 without temperature (not supported on these models anyway). Older models support temperature; if using them, set temperature=0 in system prompt or accept non-determinism.
- If sub-second latency is critical (<1s), use Messages API directly (avoid CLI subprocess overhead ~0.5-1s startup). If latency acceptable and you need code execution visibility during grading, use Claude Code.
- For rubric reuse across large batches, consider Anthropic Messages API with prompt caching (25% savings on cached input). Claude Code doesn't expose caching flags, but Agent SDK Python/TypeScript packages can enable it via options.
- Avoid --continue or interactive mode in grading loops. Explicitly pass --session-id or --resume UUID for multi-turn grading. Each invocation is independent cost-wise; sum per-call total_cost_usd for cumulative budget tracking.
- Set up a health check: periodically run grader on a fixed test case with --bare, verify exit code and cost is stable. Catch drift in model behavior or pricing changes via monitoring total_cost_usd over time.

## Proposed modules

### Local Grader Harness (Claude Code Edition)

**Objectives**

- Build a Python/Go subprocess wrapper around `claude --bare -p` for programmatic grading
- Implement rubric injection via --append-system-prompt and structured output validation
- Parse JSON results: cost tracking, structured_output extraction, error handling
- Batch grader with multi-turn session support and cumulative cost aggregation
- Health check: periodically grade fixed test case, alert on exit code / cost drift

**Testable skills**

- Spawn claude subprocess with correct flags (--bare, --output-format json, --disallowed-tools)
- Parse exit code and distinguish success / API error / limit exceeded
- Extract total_cost_usd and accumulate across multi-invocation sessions
- Pass rubric as --append-system-prompt or file and validate output matches schema
- Handle JSON parsing errors and stderr diagnostics
- Batch grade 10+ submissions, track per-submission and cumulative cost

### Anthropic Messages API Grader (Direct / Tool Runner)

**Objectives**

- Make direct Messages API calls (Python anthropic SDK / Go sdk) for grading
- Implement tool-use loop (or Tool Runner if available in your SDK version) to allow Read-only operations during grading
- Structured outputs with JSON Schema to enforce grading output format
- Token usage tracking and cost estimation from pricing table
- Compare cost/latency/determinism vs Claude Code headless path

**Testable skills**

- Construct Messages API request with model, system prompt (rubric), user message (submission)
- Parse response: extract text, usage tokens, stop_reason
- If using tool-use: define Read tool schema, handle tool_use stop_reason, call tool, append result, loop
- Implement structured output: pass output_config JSON Schema, parse structured_output field
- Estimate cost: (input_tokens × model_input_price + output_tokens × model_output_price) / 1e6
- Benchmark latency vs Claude Code -p across 10 grading calls

### Determinism & Reproducibility Validation

**Objectives**

- Run identical grading prompt 5+ times, collect results and costs
- Verify identical scores/feedback (allow whitespace variance)
- Check cost is stable (allow ±2% variance due to token rounding)
- Test temperature impact if using older models that support it (should be pinned to 0)
- Measure variance across models (Opus vs Sonnet vs Haiku) and newer vs legacy models

**Testable skills**

- Construct identical grading inputs: same submission, same rubric, same system prompt
- Run N times, collect results.result and results.total_cost_usd
- Compare outputs: hash or semantic similarity check
- Compute cost variance percentage
- Identify which model/temperature setting achieves <1% cost variance and identical output
- Document reproducibility SLA for grading SLA

### Rubric Schema Design & Validation

**Objectives**

- Design JSON schema for grading output (score ranges, feedback structure, pass/fail criteria)
- Validate schema with --json-schema on small test cases
- Ensure grammar compiles (< 2s latency on first call)
- Cache strategy: measure cache hit rate and 24h TTL behavior
- Compare structured output reliability vs post-hoc JSON parsing of text result

**Testable skills**

- Write JSON Schema for rubric: { score: 0-100, feedback: string, category_scores: { ... }, pass: bool }
- Test schema validity: run claude -p with --json-schema, verify no 400 errors
- Measure first-call latency (expect +1-2s for compilation)
- Run 10 grading calls, measure cache hits (all but first should be fast)
- Intentionally invalidate schema (change field name), verify exit code 1
- Compare reliability: structured_output validation vs regex on text result

### Cost Tracking & Budget Monitoring

**Objectives**

- Aggregate costs across batch grading (100+ submissions)
- Implement cost alerting: warn if per-submission or cumulative cost exceeds budget
- Compare cost/token for each model: Opus vs Sonnet vs Haiku
- Measure cost delta between single-turn and multi-turn (session) grading
- Project monthly cost for production grading at target throughput

**Testable skills**

- Parse total_cost_usd from JSON, accumulate across loop iterations
- Log per-submission and running total
- Set cost budget (e.g., $0.10/submission), fail fast if exceeded
- Grade same batch with --model claude-opus-4-8, claude-sonnet-5, claude-haiku-4-5, compare total costs
- Grade same batch as single-turn vs multi-turn sessions, measure cost delta
- Extrapolate: if grading 1000 submissions/day at X cost/submission, estimate monthly spend

## Risks & gotchas

- Temperature/top_p/top_k not supported on Claude Opus 4.7 and later. If you set these in system prompt or flags, the API returns 400 error. Older models (Opus 4.6, Sonnet 4.5) still support them; pin to a specific model version if determinism is critical.
- First --json-schema call has grammar compilation overhead (~1-2s). Subsequent calls reuse cache for 24h, but cache invalidates if schema structure changes. Test grammar with small schema first.
- total_cost_usd is a client-side estimate (bundled pricing table), not authoritative. For billing disputes, use Admin API (requires org API key). Pricing can drift if model IDs change or new models ship.
- Claude Code -p reads stdin, capping at 10MB. Large submissions must be passed as file paths in the prompt, not piped: claude -p "grade $(cat large_file.txt)" may fail; use claude -p "grade the file at /path/to/file.txt" and pass --allowed-tools Read instead.
- --bare mode skips auth via keychain/OAuth. Must set ANTHROPIC_API_KEY env var or pass apiKeyHelper in --settings JSON. Fails silently if key not found.
- Sessions are scoped to cwd and git worktrees. Resume across different directories won't work. Store session_id separately if you need cross-directory resumption.
- --max-turns applies per-invocation, not globally. If using multi-turn grading, each --resume call has its own turn limit; easy to accidentally trigger limit on second+ invocations.
- Tool restrictions (--disallowed-tools) are enforced by Claude Code, not the model. If the model tries to use a disallowed tool, it returns an error, but that still consumes tokens and counts toward cost/latency.
- Exit code 1 on both API errors and --max-turns limit. Distinguish by parsing stderr for 'limit reached' message; not ideal for programmatic error handling.
- Structured output (--json-schema) on --output-format json nests the schema-compliant output under structured_output field, not result. Result still contains text explanation; parse the right field.

## Open questions

- Does Claude Code support streaming JSON results (--output-format stream-json) for long-running grading with real-time cost/progress reporting? (Docs mention it exists but don't detail streaming cost updates.)
- Can --allowed-tools be combined with --disallowed-tools for allow-list + blocklist layering? (Docs show both but not interaction rules.)
- What is the actual latency SLA for Claude Code -p on Anthropic's servers vs Messages API? (Docs mention 'comparable' but no p50/p99 numbers.)
- Does prompt caching work with claude --bare -p, or is it only available via Agent SDK package? (Docs suggest caching is auto on SDK, unclear for CLI.)
- For very large rubrics (>10KB), is --append-system-prompt-file more efficient than inline --append-system-prompt? (File-based might avoid shell escaping overhead.)

## Citations

- [Claude Code Headless Mode Documentation](https://code.claude.com/docs/en/headless.md)
- [Claude Code CLI Reference](https://code.claude.com/docs/en/cli-reference.md)
- [Claude Code Cost Tracking (Agent SDK)](https://code.claude.com/docs/en/agent-sdk/cost-tracking.md)
- [Anthropic Messages API Documentation](https://platform.claude.com/docs/en/build-with-claude/working-with-messages.md)
- [Claude Models Overview & Pricing](https://platform.claude.com/docs/en/about-claude/models/overview.md)
- [Anthropic Structured Outputs Guide](https://platform.claude.com/docs/en/build-with-claude/structured-outputs.md)
- [Anthropic Tool Runner (SDK Helper)](https://platform.claude.com/docs/en/agents-and-tools/tool-use/tool-runner.md)
- [Anthropic Usage & Cost Admin API](https://platform.claude.com/docs/en/manage-claude/usage-cost-api.md)
- [Anthropic Prompt Caching](https://platform.claude.com/docs/en/build-with-claude/prompt-caching.md)
- [Managed Agents Overview](https://platform.claude.com/docs/en/managed-agents/overview.md)

