---
name: metaskill
description: Clasifica y enruta tareas sin gastar tokens de LLM. Usar ANTES de empezar cualquier tarea no trivial para decidir tier de modelo, arquetipo e instrucciones de trabajo. También cuando el usuario pregunta qué modelo usar, dice "routea esto", "qué modelo para esto", o hay que elegir entre modelo barato y premium. (user)
---

# MetaSkill — router zero-token

Clasificar primero, trabajar después. La elección de modelo es una decisión determinista y local, no una corazonada que quema tokens.

## Protocolo

1. Ejecuta el router con la petición del usuario (el script `metaskill.py` vive en la carpeta de este skill):
   ```
   python metaskill.py "<petición del usuario>" --json
   ```
2. Lee el resultado:
   - `tier` + `model_alias`: el tier de modelo que debe ejecutar la tarea.
   - `fallback` / `fallback_aliases`: alternativa si ese tier no está disponible.
   - `instructions`: instrucciones de trabajo del arquetipo — síguelas.
   - `tools`: herramientas sugeridas.
3. Si `status` es `unclassified`: la tarea es nueva o ambigua → aplica `premium_reasoning` según la política de fallbacks de `index.json`.
4. Ejecuta la tarea siguiendo las `instructions` del arquetipo ganador.

## Reglas

- El routing es local y de coste cero: no gastar tokens de LLM en decidir el modelo.
- Si el usuario nombra un modelo explícitamente, su decisión manda sobre el router.
- Peticiones con varias partes independientes: clasificar cada parte por separado.
- El índice es `index.json` (arquetipos, tiers, alias y política de fallbacks); para añadir arquetipos se edita ese archivo, no este skill.

## Sin Python

Si `python` no está disponible, clasifica manualmente: compara las palabras de la petición con los `keywords` de cada arquetipo en `index.json` y aplica la misma política (mejor cobertura de keywords; sin matches → `premium_reasoning`).
