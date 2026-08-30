# MetaSkill

**Router de tareas zero-token.** Clasifica cualquier petición *localmente* (sin gastar tokens de LLM) y decide qué arquetipo y qué tier de modelo debe ejecutarla, con instrucciones de trabajo incluidas.

```
petición del usuario ──▶ tokenización local ──▶ match contra index.json
                                                 ├─ arquetipo (ej. mobile, devops, quick_fix)
                                                 ├─ tier de modelo (local / budget / standard / premium)
                                                 ├─ fallbacks si ese modelo no está disponible
                                                 ├─ herramientas sugeridas
                                                 └─ instrucciones de trabajo para el agente
```

## Por qué existe

Elegir modelo a ojo quema tokens: tareas triviales acaban en modelos premium y tareas críticas en modelos débiles. MetaSkill convierte esa decisión en una clasificación determinista de coste cero basada en `index.json` (v8.0.0, 16 arquetipos).

## Uso

### CLI

```bash
python metaskill.py "quiero hacer una app móvil con flutter para android"
python metaskill.py "arreglar un bug en el log" --json
```

Salida: arquetipo ganador, tier, fallbacks, herramientas e instrucciones. Con `--json` para consumo por programas/agentes.

### Como skill (Claude Code y Qwen Code)

`SKILL.md` hace que el agente clasifique la tarea antes de trabajar. El formato es compatible con ambos agentes. Instalación:

```powershell
# Windows (PowerShell): copia la carpeta a ambos agentes
Copy-Item -Recurse . "$env:USERPROFILE\.claude\skills\metaskill"
Copy-Item -Recurse . "$env:USERPROFILE\.qwen\skills\metaskill"
```

```bash
# macOS / Linux
cp -r . ~/.claude/skills/metaskill
cp -r . ~/.qwen/skills/metaskill
```

## Los 4 tiers

| Tier | Alias | Para qué |
|---|---|---|
| `local_zero_token` | `ollama` | parches mínimos, typos, fixes triviales |
| `budget_fast` | `gpt-4o-mini` | scripts, docs, tareas simples |
| `standard_coding` | `gpt-4o` | desarrollo de producto |
| `premium_reasoning` | `gpt-4` | arquitectura, migraciones, investigación |

Cada tier tiene una cadena de fallback definida en `index.json` (`fallback_policy`); el último recurso es `premium_reasoning`.

## Cómo clasifica (engine `jaccard-zero-token-v2`)

1. Normaliza el texto (minúsculas, sin tildes).
2. Busca coincidencias con los `keywords` de cada arquetipo (tokens y frases multi-palabra).
3. Puntúa por cobertura (`coincidencias / keywords del arquetipo`) y desempata por nº de matches y complejidad.
4. Sin ningún match → tarea no clasificada: se recomienda `premium_reasoning` según la política de fallbacks.

## Añadir o editar arquetipos

Edita `index.json` → `tasks[]`. Cada arquetipo necesita: `id`, `archetype`, `label`, `keywords` (incluye variantes con typos comunes), `complexity` (1-5), `routing` (`tier`, `fallback`, `tools`) e `instructions_for_claude`. El router lo recoge automáticamente.

## Estructura

```
MetaSkill/
├── SKILL.md      # skill compatible con Claude Code y Qwen Code
├── metaskill.py  # router zero-token (solo stdlib de Python)
├── index.json    # índice de arquetipos, tiers y política de fallbacks
└── README.md
```

## Licencia

MIT — úsalo, modifícalo y distribúyelo manteniendo el aviso de licencia.
