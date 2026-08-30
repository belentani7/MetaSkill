#!/usr/bin/env python3
"""MetaSkill zero-token router (engine: jaccard-zero-token-v2).

Clasifica una peticion localmente, sin gastar tokens de LLM, contra index.json.
Solo usa stdlib. Uso:
    python metaskill.py "texto de la peticion" [--json]
"""

import json
import re
import sys
import unicodedata
from pathlib import Path

INDEX_PATH = Path(__file__).resolve().parent / "index.json"
UNCLASSIFIED_TIER = "premium_reasoning"


def normalize(text: str) -> str:
    text = unicodedata.normalize("NFD", text.lower())
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")
    return text


def tokenize(text: str) -> set:
    return set(re.split(r"[^a-z0-9]+", normalize(text))) - {""}


def load_index() -> dict:
    with open(INDEX_PATH, encoding="utf-8") as fh:
        return json.load(fh)


def keyword_matches(keyword: str, norm_text: str, tokens: set) -> bool:
    kw = normalize(keyword)
    if " " in kw:
        return kw in norm_text
    return kw in tokens


def classify(request: str, index: dict) -> dict:
    norm_text = normalize(request)
    tokens = tokenize(request)
    scored = []
    for task in index.get("tasks", []):
        keywords = task.get("keywords", [])
        if not keywords:
            continue
        matched = [kw for kw in keywords if keyword_matches(kw, norm_text, tokens)]
        if matched:
            scored.append(
                {
                    "task": task,
                    "matched": matched,
                    "coverage": len(matched) / len(keywords),
                }
            )
    scored.sort(
        key=lambda s: (len(s["matched"]), s["coverage"], s["task"].get("complexity", 0)),
        reverse=True,
    )
    return {"scored": scored, "tokens": sorted(tokens)}


def build_result(request: str, index: dict) -> dict:
    index_meta = index.get("meta", {})
    aliases = index.get("model_aliases", {})
    fallback_policy = index.get("fallback_policy", {})
    cls = classify(request, index)
    scored = cls["scored"]

    if not scored:
        return {
            "engine": index_meta.get("engine", "jaccard-zero-token-v2"),
            "status": "unclassified",
            "request": request,
            "tier": UNCLASSIFIED_TIER,
            "model_alias": aliases.get(UNCLASSIFIED_TIER),
            "reason": "Sin coincidencias de keywords: tarea nueva o ambigua; la politica de fallbacks recomienda premium_reasoning.",
            "fallback_policy": fallback_policy.get("note", ""),
        }

    best = scored[0]["task"]
    routing = best.get("routing", {})
    tier = routing.get("tier")
    return {
        "engine": index_meta.get("engine", "jaccard-zero-token-v2"),
        "status": "classified",
        "request": request,
        "task_id": best.get("id"),
        "archetype": best.get("archetype"),
        "label": best.get("label"),
        "complexity": best.get("complexity"),
        "tier": tier,
        "model_alias": aliases.get(tier),
        "fallback": routing.get("fallback", []),
        "fallback_aliases": [aliases.get(f) for f in routing.get("fallback", [])],
        "tools": routing.get("tools", []),
        "instructions": best.get("instructions_for_claude", ""),
        "score": {
            "matched_keywords": scored[0]["matched"],
            "keywords_total": len(best.get("keywords", [])),
            "coverage": round(scored[0]["coverage"], 3),
        },
        "runners_up": [
            {"task_id": s["task"].get("id"), "matched": len(s["matched"]), "coverage": round(s["coverage"], 3)}
            for s in scored[1:4]
        ],
    }


def print_human(result: dict) -> None:
    if result["status"] == "unclassified":
        print(f"[sin clasificar] {result['reason']}")
        print(f"  tier sugerido : {result['tier']} ({result.get('model_alias')})")
        return
    print(f"arquetipo : {result['label']}  ({result['task_id']}, complejidad {result['complexity']})")
    print(f"tier      : {result['tier']}  -> {result.get('model_alias')}")
    if result["fallback"]:
        fb = ", ".join(f"{t} ({a})" for t, a in zip(result["fallback"], result["fallback_aliases"]))
        print(f"fallback  : {fb}")
    if result["tools"]:
        print(f"herramientas: {', '.join(result['tools'])}")
    score = result["score"]
    print(f"keywords  : {len(score['matched_keywords'])}/{score['keywords_total']} (cobertura {score['coverage']}) -> {', '.join(score['matched_keywords'])}")
    if result["runners_up"]:
        alt = " | ".join(f"{r['task_id']} ({r['matched']})" for r in result["runners_up"])
        print(f"alternativas: {alt}")
    print(f"instrucciones: {result['instructions']}")


def main(argv: list) -> int:
    args = [a for a in argv[1:] if not a.startswith("--")]
    as_json = "--json" in argv[1:]
    if not args:
        print(__doc__)
        print("Falta el texto de la peticion.", file=sys.stderr)
        return 1
    request = " ".join(args)
    try:
        index = load_index()
    except (OSError, json.JSONDecodeError) as exc:
        print(f"Error leyendo {INDEX_PATH}: {exc}", file=sys.stderr)
        return 1
    result = build_result(request, index)
    if as_json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print_human(result)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
