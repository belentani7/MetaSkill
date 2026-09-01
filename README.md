# MetaSkill

**Zero-token task router for AI coding agents.** Classifies any request *locally* (without burning LLM tokens) and decides which archetype and complexity tier should handle it, with embedded work instructions.

```
user request ──▶ in-context tokenization ──▶ match against index.json
                                               ├─ archetype (e.g. mobile, devops, quick_fix)
                                               ├─ complexity tier (1-5)
                                               ├─ model recommendation
                                               ├─ fallback chain
                                               ├─ suggested tools
                                               └─ work instructions for the agent
```

## Why it exists

Choosing a model by gut feeling burns tokens: trivial tasks end up on premium models and critical tasks on weak ones. MetaSkill makes that decision a zero-cost deterministic classification based on `index.json` (v9.0.0, 16 archetypes).

## Install (Qwen Code / Claude Code)

```powershell
# Windows
Copy-Item -Recurse . "$env:USERPROFILE\.qwen\skills\metaskill"
Copy-Item -Recurse . "$env:USERPROFILE\.claude\skills\metaskill"
```

```bash
# macOS / Linux
cp -r . ~/.qwen/skills/metaskill
cp -r . ~/.claude/skills/metaskill
```

The agent will pick it up automatically on the next session via `SKILL.md`.

## How it works

The agent reads `index.json` and classifies the request by keyword matching — **no Python subprocess, no shell calls, zero additional tokens**. The classification happens in the agent's own reasoning.

### 4 tiers

| Tier | Models | Use for |
|------|--------|---------|
| `local_zero_token` | ollama (if available) | typos, trivial patches |
| `budget_fast` | qwen-flash, deepseek-flash, glm-flash | docs, scripts, simple tasks |
| `standard_coding` | deepseek-pro, qwen-plus | product development |
| `premium_reasoning` | qwen-max, deepseek-pro-max | architecture, migrations, research |

### 16 archetypes

Security audit, Frontend/UI, Backend/API, DevOps/IaC, Data science, System architecture, Documentation, Quick fix, Testing/QA, Database, Mobile, Migration/Refactor, CLI/Automation, Game dev, Research.

### CLI (optional, for external integrations)

```bash
python metaskill.py "build a mobile app with flutter for android"
python metaskill.py "fix a bug in the log" --json
```

Returns archetype, tier, fallbacks, tools, and instructions. Use `--json` for programmatic consumption.

## Adding or editing archetypes

Edit `index.json` → `tasks[]`. Each archetype needs: `id`, `archetype`, `label`, `keywords` (include common typos/variants), `complexity` (1-5), `routing` (`tier`, `fallback`, `tools`) and `instructions`. The router picks it up automatically.

## Structure

```
metaskill/
├── SKILL.md      # skill definition (Qwen Code + Claude Code compatible)
├── metaskill.py  # optional CLI router (Python stdlib only)
├── index.json    # archetype index, tiers, and fallback policy
└── README.md
```

## Model aliases are the only thing that changes

When a model dies, update **ONLY** `model_aliases` in `index.json`. The routing logic never changes.

## License

MIT — use, modify, and distribute with attribution.
