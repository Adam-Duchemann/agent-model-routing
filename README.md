# claude-code-model-routing

**Route delegated work to the cheapest Claude model that does it well.**

A drop-in `CLAUDE.md` policy for [Claude Code](https://claude.com/claude-code) that keeps your expensive top-tier model focused on planning and judgment, while codebase exploration and implementation run on cheaper tiers — automatically, on every task.

## The problem

When Claude Code delegates work to subagents (Explore, Plan, general-purpose, or your custom agents), **subagents inherit the session model by default**. Run your session on a top-tier model and every grep sweep, file enumeration, and boilerplate edit a subagent performs is billed at top-tier prices — for work a fast model does just as well.

The fix is not "use the big model less." Different task classes have different token/difficulty profiles, and the trick is matching them:

| Task class | Token volume | Difficulty | Right tier |
|---|---|---|---|
| Codebase exploration | high | low | fast + cheap |
| Implementation | medium | medium | workhorse |
| Planning / architecture / review | low | high | your best model |

Planning is low-token, high-difficulty — exactly where a premium model pays for itself. Exploration is high-token, low-difficulty — the single best thing to push down-tier. Raw tool output read on your top-tier main thread is the most expensive token in the system.

## The routing policy

The policy this repo installs (full text: [`rules/model-routing.md`](rules/model-routing.md)):

| Task class | Model | How |
|---|---|---|
| Planning, architecture, hard algorithms, adjudication | **Top tier** (main thread) | never delegated — it holds the conversation context |
| Locate / enumerate / grep-sweep exploration | **Haiku** | `Explore` agent + `model: haiku` |
| Interpretive exploration ("how/why does X work") | **Sonnet** | `Explore` agent + `model: sonnet` |
| Routine implementation (boilerplate, tests, mechanical refactors) | **Sonnet** | subagent + `model: sonnet` |
| Substantive implementation of a planned change | **Opus** | subagent + `model: opus` |
| Verify / review the implemented diff | **Top tier** (main thread) | review the diff where the context lives |
| Hard, self-contained problem while on a lower main model | **Top-tier subagent** — user-approved only | Claude asks you to validate the bump first |

Plus the guardrails that make it hold up in practice:

- **Size gate** — trivial work (single-file edit, rename, typo) stays inline; delegation's cold-start handoff tax exceeds the savings.
- **Escalate, don't retry** — a shallow Haiku exploration result gets re-run at Sonnet, never redone on the expensive main thread (that pays twice).
- **Explorer output contract** — exploration results must include `file:line` + a short excerpt per hit, so the main thread can verify without re-searching.
- **No self-certification** — implementation subagents don't declare their own work verified; the diff comes back to the main thread for review.
- **Upward bumps are opt-in** — spawning a subagent on a *more* expensive model than the session always requires explicit user approval, per occurrence.

## How it behaves

**Your chat-window model is the ceiling.** The policy never changes the main thread's model — only you can, via `/model`. It governs what happens *below* the ceiling:

- Start a session on **Fable** → Fable plans and reviews, everything mechanical routes down to Haiku/Sonnet/Opus.
- Start a session on **Opus** → Opus plans and reviews, the same down-tier routing still saves you money identically. The table degrades gracefully.
- The one exception — reaching **up** to a pricier model from a cheaper session for a hard, self-contained problem — always passes through you first.

## Install

```bash
git clone https://github.com/Adam-Duchemann/claude-code-model-routing.git
cd claude-code-model-routing
./install.sh                        # appends the policy to ~/.claude/CLAUDE.md (global, all projects)
./install.sh path/to/your/CLAUDE.md # or install into a single project instead
```

The script is idempotent — it refuses to append twice. Or skip the script and paste [`rules/model-routing.md`](rules/model-routing.md) into your `CLAUDE.md` by hand.

> `~/.claude/CLAUDE.md` is per-machine. If you work across several machines, install on each.

## Pin models in your custom agents

Prose rules can be missed; frontmatter can't. If you define custom agents in `.claude/agents/`, pin the model there so routing is structural:

```markdown
---
name: implementer
description: Implements a planned change end to end.
model: opus
---
```

This repo ships three ready-to-use examples in [`agents/`](agents/) — copy them into `~/.claude/agents/` (global) or `<project>/.claude/agents/`:

- [`explore-fast`](agents/explore-fast.md) (haiku) — mechanical locate/enumerate lookups with a strict `file:line` output contract
- [`explore-deep`](agents/explore-deep.md) (sonnet) — interpretive "how/why does X work" exploration
- [`implementer`](agents/implementer.md) (opus) — implements a planned change, reports without self-certifying

## Adapting the tiers

The table names the current Claude lineup (Fable 5 / Opus / Sonnet / Haiku). If your plan doesn't include a top tier above Opus, shift everything up one notch: top tier → Opus, substantive implementation → Sonnet, and keep Haiku for mechanical exploration. The *shape* of the policy — cheapest capable model per task class, expensive model reserved for judgment — is what matters, not the specific names.

## FAQ

**Does this slow anything down?**
Usually the opposite — Haiku explorers respond faster than a top-tier model doing the same grep, and fan-outs run in parallel.

**What about reasoning effort?**
Model choice is the first knob; where your setup exposes reasoning-effort control (agent definitions, orchestration frameworks), the same logic applies: low effort for mechanical fan-outs, high effort only for planning and judging. The installed policy documents the recommended pairings.

**Why not route planning to a subagent too?**
A subagent starts cold, without the conversation. Planning is exactly the work that suffers most from that handoff — and it's low-token anyway, so there's little to save.

**What's the failure mode to watch for?**
A cheap explorer returning a shallow or wrong map that poisons the expensive plan built on top of it. That's why the policy escalates failed explorations to Sonnet instead of retrying, and why explorers must return verifiable `file:line` evidence.

## License

[MIT](LICENSE)
