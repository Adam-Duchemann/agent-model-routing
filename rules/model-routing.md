## Model Routing (all projects)

Route delegated work to the cheapest model that does it well. The main thread
stays on the user-selected model — routing applies to **delegated** work only,
via the Agent tool's `model` param or agent-definition frontmatter.

| Task class | Model | Effort | How |
|---|---|---|---|
| Planning, architecture, hard algorithms, adjudication | Top tier (main thread) | high; `max` only for genuinely hard problems | never delegated — it holds the conversation context |
| Locate / enumerate / grep-sweep exploration | Haiku | low | `Explore` agent + `model: haiku` |
| Interpretive exploration ("how/why does X work") | Sonnet | default | `Explore` agent + `model: sonnet` |
| Routine implementation (boilerplate, test scaffolding, mechanical refactors) | Sonnet | default | subagent + `model: sonnet` |
| Substantive implementation of a planned change | Opus | default; high for gnarly debugging | subagent + `model: opus` |
| Verify / review the implemented diff | Top tier (main thread) | high | review where the conversation context lives |
| Genuinely hard, self-contained problem while the main thread is below the top tier (algorithm design, complex calculation, adjudicating written-up options) | Top-tier subagent — user-approved only | high/max | ask the user to validate the bump first, then spawn with a complete written brief |

**Guardrails:**

- **Size gate** — trivial work (single-file edit, rename, typo) stays inline on
  the main thread; delegation's cold-start handoff tax exceeds the savings.
- **Escalate, don't retry** — if a Haiku explorer returns a shallow or wrong map,
  re-run at Sonnet; don't redo the search on the main thread (that pays twice).
  When unsure which exploration class a question is, pick Sonnet.
- **Explorer output contract** — exploration results must include `file:line` +
  a short excerpt per hit, so the main thread can verify without re-searching.
- **No self-certification** — implementation subagents don't declare their own
  work verified; the diff comes back to the main thread for review.
- **Keep dumps off the main thread** — raw grep/file output read on the main
  thread is the most expensive token in the system; that is what delegation is for.
- **Upward bump is opt-in, per occurrence** — never spawn a subagent on a more
  expensive model than the session without asking the user first (state the
  problem and why it merits the bump). Only for self-contained problems where the
  full brief fits in one prompt — conversational, context-heavy planning stays on
  the main thread whatever its model (a cold-start subagent loses the conversation).

Custom agents in `.claude/agents/` pin their model in frontmatter — keep new
agent definitions consistent with this table.
