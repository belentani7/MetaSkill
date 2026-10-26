# MetaSkill

**Local task router for AI coding agents.** The optional Python CLI classifies requests without calling an LLM. In-agent classification consumes context tokens. Uncertain requests remain unclassified instead of selecting a paid model automatically.

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

Choosing a model by gut feeling burns tokens: trivial tasks end up on premium models and critical tasks on weak ones. MetaSkill provides a deterministic local CLI recommendation without external model calls based on `index.json` (v9.0.0, 15 archetypes).

## Install (Qwen Code / Claude Code)

The skill only needs `SKILL.md` and `index.json`. **Do not copy the entire repository** into agent skill folders: that would also copy Git history, tests, and unrelated files. The installers check both destinations before copying and **refuse to overwrite** an existing installation. Review its contents and back it up before upgrading.

```powershell
# Windows PowerShell 5/7 — run from this repository's root
& ./scripts/install.ps1
```

```bash
# macOS / Linux — run from this repository's root
bash scripts/install.sh
```

For a disposable test, set `METASKILL_INSTALL_ROOT` to an empty directory before running either installer. The optional `metaskill.py` CLI remains in this repository. Uninstall only after reviewing the target directory; these commands never remove user data.

The agent will pick it up automatically on the next session via `SKILL.md`.

## How it works

The agent reads `index.json` and matches whole-word keywords. A classification requires at least two matched keywords or more than 20% coverage of a task's keyword list; otherwise it abstains and requests review. **In-agent reasoning consumes context tokens**; the optional Python CLI does not call any external model.

### 4 tiers

| Tier | Models | Use for |
|------|--------|---------|
| `local_zero_token` | ollama (if available) | typos, trivial patches |
| `budget_fast` | qwen-flash, deepseek-flash, glm-flash | docs, scripts, simple tasks |
| `standard_coding` | deepseek-pro, qwen-plus | product development |
| `premium_reasoning` | qwen-max, deepseek-pro-max | architecture, migrations, research |

### 15 archetypes

Security audit, Frontend/UI, Backend/API, DevOps/IaC, Data science, System architecture, Documentation, Quick fix, Testing/QA, Database, Mobile, Migration/Refactor, CLI/Automation, Game dev, Research.

### CLI (optional, for external integrations)

```bash
python metaskill.py "build a mobile app with flutter for android"
python metaskill.py "fix a bug in the log" --json
```

Returns archetype, tier, fallbacks, tools, and instructions. Use `--json` for programmatic consumption.

### Batch de hasta 500 tareas (sin API)

Crea un archivo `requests.json` con un array de textos, por ejemplo:

```json
["desarrollar portada accesible", "resolver errores de tests", "construir una API"]
```

Ejecuta `python metaskill.py --batch requests.json > routes.json`. Clasifica cada petición contra el mismo índice local y devuelve un array JSON ordenado, sin llamar a modelos ni ejecutar herramientas externas. Limita el archivo a **1 MB**, cada petición a **10.000 caracteres** y el lote a **500** solicitudes. Un archivo inválido falla antes de producir resultados parciales; las opciones desconocidas devuelven un error de CLI, no se agregan a la petición por accidente.


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
