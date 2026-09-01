---
name: metaskill
description: "Use when starting any non-trivial task, before writing code, to decide work approach and complexity tier. Also when user asks which model to use, says 'route this', 'qué modelo', or when choosing between cheap and premium model. Triggers on: task classification, model selection, cost optimization, routing."
---

# MetaSkill — zero-token task router

Before writing a single line of code, classify the task. Read `index.json` in this skill's directory, tokenize the user's request mentally, and match against archetype keywords.

## Protocol

1. **Read** `index.json` → scan `tasks[]` for keyword matches against the user's request
2. **Classify**: pick the archetype with ≥2 keyword matches OR >20% coverage. If none matches → `arch_quick_fix` with complexity 1
3. **Report** (briefly, 1-2 lines max):
   - `[archetype] complexity: N/5`
   - If complexity ≤ 2: "→ consider cheaper model (qwen-flash / deepseek-flash) to save tokens"
   - If complexity ≥ 4: "→ verify you're on a capable model (qwen-max / deepseek-pro)"
4. **Follow** the archetype's `instructions` field as your work protocol
5. **Use** suggested `tools` when applicable

## Rules

- Classification is in-context: read index.json, match keywords in your reasoning. Zero shell calls, zero latency.
- If user names a model explicitly, their choice overrides the router.
- Multi-part requests: classify each part independently.
- Never shell out to `python metaskill.py` — that's for external CI/agents, not for in-session use.
- The index has 16 archetypes covering: security, frontend, backend, devops, data, architecture, docs, quick-fix, testing, database, mobile, migration, CLI, game-dev, research, and more.

## Tier → Model mapping (Qwen Code / DashScope)

| Tier | Recommended models | Use for |
|------|-------------------|---------|
| `local_zero_token` | ollama (if available) | typos, trivial patches |
| `budget_fast` | qwen-flash, deepseek-flash, glm-flash | docs, scripts, simple tasks |
| `standard_coding` | deepseek-pro, qwen-plus | product development |
| `premium_reasoning` | qwen-max, deepseek-pro-max | architecture, migrations, research |

Since Qwen Code runs one model per session, the router **suggests** model changes — the user decides whether to restart with a different model.
