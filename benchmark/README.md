# Benchmark: does routing actually save money at equal quality?

This harness measures the policy's core claim — **route each task class to the cheapest model
that does it well** — against the honest baseline: *running everything on the top tier (Fable).*

It is deliberately falsifiable. The interesting half of the claim is not "Haiku is cheaper per
token" (trivially true) but "the cheap model does the work **just as well**." So every task is
scored for correctness, and cost only counts at equal quality.

## Method

- **Two arms, same tasks:**
  - **Routed** — each task on its policy tier (locate/enumerate → Haiku, interpretive → Sonnet).
  - **Baseline** — every task on **Fable** (the "just use the big model" default).
- **Faithful execution:** each task runs as a real headless Claude Code session
  (`claude -p --model <m> --output-format json`) *inside a fixture repo*, with read-only tools
  (`Bash/Grep/Glob/Read`) and MCP disabled. The result JSON reports **real billed cost**
  (`total_cost_usd`) and token usage — not estimates.
- **Scoring:**
  - *locate / enumerate* — objective, against a grep-derived ground truth (file set or count).
  - *interpretive* ("how/why does X work") — an LLM judge (Opus) using a **mechanism-credit
    rubric**: it checks whether the answer conveys each grounded *key point*, and does **not**
    require exact symbol names. **3 samples per answer, majority vote.**
- **Stability:** every cell runs **n=3 trials**; cost is the mean, quality is the pass-rate.
- **Contamination guard:** a run that emits more than one `ANSWER:` line is flagged and excluded
  (this caught a real stdin-bleed bug during development — see Limitations).

## Run it

```bash
cd benchmark
FIXTURE=/path/to/some/repo TRIALS=3 ./run.sh   # runs both arms, all trials (idempotent)
python3 judge.py                                # grades interpretive answers (cached)
python3 score.py                                # prints the table below
```

Requires the `claude` CLI logged in. Each run spends real money under your account
(the Fable baseline arm is the expensive part).

## Current results (n=3, fixture: a ~270-file Rust+TS repo)

| Tier | Tasks | Quality (both arms) | Routed | Baseline (Fable) | Savings |
|---|---|---|---|---|---|
| Exploration (Haiku) | 4 locate/enumerate | 12/12 = 12/12 | **$0.093** | $1.056 | **91%** |
| Interpretive (Sonnet) | 2 how/why | 6/6 = 6/6 | $0.839 | $1.235 | 32% |
| **Full mix** | 6 | **18/18 = 18/18 (100%)** | **$0.931** | **$2.291** | **59%** |

**Read:** on this mix, routing was **59% cheaper at identical quality**, and **91% cheaper on the
exploration work** that dominates a real session's delegated tokens. Fable's exploration runs cost
~$0.25–0.30 each while producing *fewer* output tokens than Haiku — that is the "context tax at
top-tier prices" the policy eliminates.

## Limitations (read before citing a number)

This is an honest MVP, not yet a publishable headline:

1. **Quality saturated at 100% on both arms.** The task set is not hard enough to find where a
   cheap model *breaks*. It proves "equal quality, less cost" *at this difficulty* but has not
   located the failure edge — which is where "escalate, don't retry" earns its place. A stronger
   benchmark needs harder, discriminating tasks.
2. **Single fixture.** One repo. A real claim needs ≥2–3, including a *pinned public* repo so
   anyone can reproduce.
3. **Small set.** 6 tasks, n=3. Directionally sound; thin for a headline.
4. **Implementation tier untested.** The Opus (substantive-implementation) rung needs
   git-worktree isolation to score safely and isn't covered yet.

## Development notes (bugs this harness caught)

- **stdin bleed → cross-task contamination.** A `while read < file` loop sharing stdin with
  `claude -p` fed each run the *remaining* questions; every model silently answered the whole set.
  Fixed with `</dev/null` on the run and a dedicated FD for the loop. The `ANSWER:`-count guard now
  fails the build if it recurs.
- **Judge/reference calibration.** An early run "found" Sonnet lagging Fable on interpretive tasks.
  It was an artifact: a wrong reference answer plus a single over-strict judge. With code-verified
  references and a 3-sample mechanism-credit rubric, the gap vanished (both 6/6). *Audit your
  measurement tool before trusting its output.*
