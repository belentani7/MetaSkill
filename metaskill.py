#!/usr/bin/env python3
"""MetaSkill zero-token router driven by the version in index.json.

Clasifica una peticion localmente, sin gastar tokens de LLM, contra index.json.
Solo usa stdlib. Uso:
    python metaskill.py "texto de la peticion" [--json]
"""

import argparse
import json
import re
import sys
import unicodedata
from pathlib import Path

INDEX_PATH = Path(__file__).resolve().parent / "index.json"
UNCLASSIFIED_TIER = "premium_reasoning"
DEFAULT_ENGINE = "jaccard-zero-token-v3"


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
    """Match whole words or adjacent keyword tokens, never arbitrary substrings.

    A phrase like "rate limit" matches "rate-limit" and "rate limit", but
    does not match "corporate limitations". Punctuation is a separator rather
    than a source of false positives.
    """
    words = re.findall(r"[a-z0-9]+", normalize(keyword))
    if not words:
        return False
    if len(words) == 1:
        return words[0] in tokens
    pattern = r"(?<![a-z0-9])" + r"[^a-z0-9]+".join(map(re.escape, words)) + r"(?![a-z0-9])"
    return re.search(pattern, norm_text) is not None


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
        key=lambda s: (
            1 if s["task"].get("archetype") == "security_critical" else 0,
            len(s["matched"]),
            s["coverage"],
            s["task"].get("complexity", 0),
        ),
        reverse=True,
    )
    return {"scored": scored, "tokens": sorted(tokens)}


def build_result(request: str, index: dict) -> dict:
    engine = index.get("engine", DEFAULT_ENGINE)
    aliases = index.get("model_aliases", {})
    fallback_policy = index.get("fallback_policy", {})
    cls = classify(request, index)
    scored = cls["scored"]

    if not scored:
        quick_fix = next(
            (task for task in index.get("tasks", []) if task.get("id") == "arch_quick_fix"),
            None,
        )
        if quick_fix:
            scored = [
                {
                    "task": quick_fix,
                    "matched": [],
                    "coverage": 0,
                }
            ]
        else:
            return {
                "engine": engine,
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
        "engine": engine,
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
        "instructions": best.get("instructions", best.get("instructions_for_claude", "")),
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


def _load_batch(path: str) -> list[str]:
    """Load up to 500 locally supplied requests, with bounded memory."""
    location = Path(path)
    if not location.is_file():
        raise ValueError("Batch file does not exist")
    with location.open("rb") as handle:
        data = handle.read(1_000_001)
    if len(data) > 1_000_000:
        raise ValueError("Batch file exceeds 1 MB")
    try:
        requests = json.loads(data.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError("Batch must be a UTF-8 JSON array") from exc
    if not isinstance(requests, list) or not 1 <= len(requests) <= 500:
        raise ValueError("Batch must have between 1 and 500 requests")
    for entry in requests:
        if not isinstance(entry, str) or not entry.strip() or len(entry) > 10_000:
            raise ValueError("Each batch request must be nonempty text of <=10000 characters")
    return requests


def main(argv: list) -> int:
    parser = argparse.ArgumentParser(
        prog="metaskill.py",
        description="Zero-token classification using the local, versioned skill index.",
    )
    parser.add_argument("--json", action="store_true", help="Print structured JSON")
    parser.add_argument("--batch", metavar="INPUT.json", help="Classify up to 500 local prompts")
    parser.add_argument("request", nargs="*", help="One request to classify")
    try:
        opts = parser.parse_args(argv[1:])
    except SystemExit as exc:
        return int(exc.code)

    if bool(opts.batch) == bool(opts.request):
        print("Provide a request OR --batch INPUT.json.", file=sys.stderr)
        return 2

    try:
        index = load_index()
        if opts.batch:
            requests = _load_batch(opts.batch)
            # Batch always emits JSON; same classification policy as single mode.
            print(json.dumps([build_result(req, index) for req in requests], ensure_ascii=False))
            return 0
        request = " ".join(opts.request)
        if len(request) > 10_000:
            raise ValueError("Request exceeds 10000 characters")
        result = build_result(request, index)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    if opts.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print_human(result)
    return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv))
