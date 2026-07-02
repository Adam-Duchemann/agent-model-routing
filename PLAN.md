# Plan: expand to a multi-tool routing repo (Claude Code · OpenAI Codex CLI · Google Antigravity)

**Status**: plan only — lives on the `dev` branch; nothing on `master` changes until this is built and reviewed.
**Date**: 2026-07-02
**Research state**: Codex CLI facts verified against official docs (2026-07-02). Antigravity research is **pending** — the research pass was interrupted; every Antigravity item below is marked TBV (to be verified) and must be confirmed before anything is published.

---

## Goal

One repo, three tools, one philosophy: *route work to the cheapest capable model per task class; reserve the top tier for planning and judgment; upward bumps are opt-in.* Each tool expresses that philosophy through its own native mechanism — no copy-pasted Claude Code prose pretending to work elsewhere.

## Target structure

```
claude-code-model-routing/
├── README.md                    # tool-agnostic concept + mechanism comparison + per-tool quickstarts
├── LICENSE
├── claude-code/                 # existing content, moved (git mv), paths fixed
│   ├── rules/model-routing.md
│   ├── agents/{explore-fast,explore-deep,implementer}.md
│   └── install.sh
├── codex/
│   ├── README.md                # mechanism notes + caveats
│   ├── AGENTS-model-routing.md  # section to append to ~/.codex/AGENTS.md
│   ├── agents/explorer-fast.toml
│   ├── agents/implementer.toml
│   ├── profiles/deep-plan.config.toml
│   └── install.sh
└── antigravity/                 # BLOCKED on research — shape TBD
    └── README.md
```

Repo name stays `claude-code-model-routing` for now; renaming to something tool-neutral (e.g. `agent-model-routing`) is a one-command option later (GitHub redirects old URLs) — user's call.

## Mechanism comparison (what drives each per-tool design)

| | Claude Code | Codex CLI (verified) | Antigravity (TBV) |
|---|---|---|---|
| Instructions file | `CLAUDE.md` (global `~/.claude/` or per-project) | `AGENTS.md` — global `~/.codex/AGENTS.md` (or `AGENTS.override.md`); project files concatenated root→cwd, 32 KiB cap | AGENTS.md support? global rules file? TBV |
| Down-tier delegation | Agent tool `model` param; agent frontmatter `model:` | **Native subagents**: built-in `default`/`worker`/`explorer` + custom agents in `~/.codex/agents/*.toml` or `.codex/agents/*.toml` with per-agent `model` + `model_reasoning_effort`. Spawning is **explicit-ask only** (the model never auto-spawns) | likely manual per-agent model choice in the Agent Manager — TBV |
| Effort control | agent frontmatter / session default | `model_reasoning_effort`: `minimal\|low\|medium\|high\|xhigh`; `/model` changes model+effort mid-session; `plan_mode_reasoning_effort` gives Plan Mode its own effort | thinking-budget setting? TBV |
| Profiles | n/a | `~/.codex/<name>.config.toml` overlay files via `--profile <name>` (**0.134.0+ — the old `[profiles.x]` tables in config.toml are GONE**; no default-profile key; no mid-session profile switch) | TBV |
| Ceiling semantics | chat-window model is the ceiling; upward bump = user-approved top-tier subagent | session model via `/model`; **Plan Mode cannot use a different model** — only different effort (`plan_mode_model` does not exist; open feature request, issue #19343) | TBV |

## Codex CLI design (verified 2026-07-02 against developers.openai.com/codex)

**Tier mapping** (from the official Models page + pricing, ~7× input-cost spread bottom to top):

| Tier | Model | Role in the policy |
|---|---|---|
| Top | `gpt-5.5` | planning, adjudication, diff review (main session, `xhigh` for hard problems) |
| Workhorse | `gpt-5.4` | substantive implementation |
| Cheap/fast | `gpt-5.4-mini` | exploration + parallel subagent work (the docs explicitly position it "for subagents") |

Deprecated, do not reference: `gpt-5.2`, `gpt-5.3-codex` (and `gpt-5.1-codex-mini` is gone from the lineup entirely).

**Deliverables:**

1. `AGENTS-model-routing.md` — the routing table adapted to Codex reality: the main session plans and reviews; because Codex only spawns subagents on an explicit user ask, the snippet instructs the agent to **propose the spawn** ("this is a locate/enumerate sweep — want me to hand it to `explorer-fast`?") rather than claim it can auto-route. Guardrails carry over unchanged: size gate, escalate-don't-retry, explorer output contract (`file:line` + excerpt), no self-certification, upward bumps opt-in.
2. `agents/explorer-fast.toml` — `name`/`description`/`developer_instructions` + `model = "gpt-5.4-mini"`, `model_reasoning_effort = "low"`; developer_instructions carry the output contract and the "stop if interpretive" escape hatch.
3. `agents/implementer.toml` — `model = "gpt-5.4"`, `model_reasoning_effort = "medium"`; developer_instructions forbid self-certification.
4. `profiles/deep-plan.config.toml` — `model = "gpt-5.5"`, `model_reasoning_effort = "xhigh"`; launched as `codex --profile deep-plan` for planning-heavy sessions.
5. Recommended base-config keys documented in `codex/README.md`: `plan_mode_reasoning_effort = "high"` (Plan Mode reasons harder than the default session automatically), optional `review_model` to pin `/review` to a chosen tier.
6. `install.sh` — `mkdir -p ~/.codex/agents`, copy the agent TOMLs (refuse to overwrite existing files), append the AGENTS section to `~/.codex/AGENTS.md` idempotently (same `grep "^## Model Routing"` gate as the Claude Code installer).

**Caveats to document honestly in `codex/README.md`:**
- Subagent spawning is explicit-ask; the policy makes the agent *suggest* spawns, the user says yes. Not automatic.
- Known regression: custom `.codex/agents` not selectable in CLI v0.137.0 (subagents spawned generic and inherited the parent model — GitHub issue #26363). Tell readers to verify on their installed version.
- No mid-session profile switching; `/model` is the in-session lever (changes model + effort, not the rest of a profile).
- Subagent workflows consume more total tokens than single-agent runs (official docs note) — the win is unit price, not volume.

## Antigravity design (BLOCKED — do not write until research lands)

The research pass died on a session limit before returning anything. **To verify before writing a single line:**

1. Rules/instructions file locations — global and per-workspace; whether AGENTS.md is supported; exact paths and filenames.
2. Current model lineup selectable in Antigravity (Gemini 3 Pro / Flash tiers? Claude? others?) and how a model is chosen — per agent/conversation in the Agent Manager? a default-model setting?
3. Whether any subagent/delegation mechanism with a model override exists, or whether model assignment is purely manual per agent surface.
4. Any planner-vs-executor model split, and any thinking/effort control.
5. Whether parallel agents in the Agent Manager can run different models simultaneously.

**Working hypothesis (UNVERIFIED — for planning shape only, not for publication):** Antigravity's parallelism is user-driven through the Agent Manager, with the model chosen per agent — no agent-initiated down-tier delegation. If that holds, the Antigravity version is a *surface-split convention* (which model to assign to which kind of agent, encoded as rules text + a README how-to) rather than an automatic routing policy. Honesty about that mechanism difference is part of the value of the repo.

## Rollout

- [x] Plan on `dev` (this document)
- [ ] Restructure: `git mv` existing Claude Code files into `claude-code/`, fix paths in README + installer
- [ ] Build `codex/` per the verified design above
- [ ] Re-run the Antigravity research (after the session-limit reset); build `antigravity/` only from verified facts
- [ ] Rewrite root README: tool-agnostic concept, mechanism-comparison table, three quickstarts
- [ ] Test both installers against scratch targets (append-once + refuse-second-run)
- [ ] Review on `dev`, then merge to `master` and push (PLAN.md does not ship to master)

## Open questions

1. Repo rename to a tool-neutral name — yes/no (redirects make it safe).
2. Codex: one explorer agent (mini/low) or also a mid-tier interpretive explorer on `gpt-5.4`, mirroring Claude Code's explore-fast/explore-deep pair? Leaning pair, decide during build.
3. Antigravity: depends entirely on research outcome.
