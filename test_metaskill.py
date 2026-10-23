import unittest
import metaskill


class BuildResultContractTests(unittest.TestCase):
    def test_multiword_keywords_match_tokens_not_infixes(self):
        phrase = "rate limit"
        self.assertTrue(metaskill.keyword_matches(phrase, "rate limit exceeded", {"rate", "limit", "exceeded"}))
        self.assertTrue(metaskill.keyword_matches(phrase, "rate-limit exceeded", {"rate", "limit", "exceeded"}))
        self.assertFalse(metaskill.keyword_matches(phrase, "corporate limitations", {"corporate", "limitations"}))
        self.assertFalse(metaskill.keyword_matches(phrase, "separate limited", {"separate", "limited"}))

    def test_punctuation_and_accents_in_phrase_keywords(self):
        self.assertTrue(metaskill.keyword_matches("interfaz gráfica", "interfaz-grafica",
                        {"interfaz", "grafica"}))
        self.assertTrue(metaskill.keyword_matches("three.js", "three.js application",
                        {"three", "js", "application"}))
        self.assertFalse(metaskill.keyword_matches("three.js", "threes.js", {"threes", "js"}))

    def test_engine_id_matches_loaded_index(self):
        index = metaskill.load_index()

        result = metaskill.build_result("an unmatchable request", index)

        self.assertEqual(result["engine"], "jaccard-zero-token-v3")

    def test_unmatched_request_falls_back_to_quick_fix(self):
        quick_fix = {
            "id": "arch_quick_fix",
            "archetype": "simple_maintenance",
            "label": "Quick fix / maintenance",
            "complexity": 1,
            "keywords": [],
            "routing": {
                "tier": "local_zero_token",
                "fallback": ["budget_fast"],
                "tools": [],
            },
            "instructions": "Apply the smallest safe fix.",
        }
        index = {
            "engine": "jaccard-zero-token-v3",
            "tasks": [quick_fix],
            "model_aliases": {"local_zero_token": "local-model"},
            "fallback_policy": {"note": "Use the quick-fix default."},
        }

        result = metaskill.build_result("an unmatchable request", index)

        self.assertEqual(result["status"], "classified")
        self.assertEqual(result["task_id"], "arch_quick_fix")
        self.assertEqual(result["tier"], "local_zero_token")
        self.assertEqual(result["instructions"], "Apply the smallest safe fix.")

    def test_no_quick_fix_task_keeps_request_unclassified(self):
        index = {
            "engine": "jaccard-zero-token-v3",
            "tasks": [],
            "model_aliases": {"premium_reasoning": "premium-model"},
            "fallback_policy": {"note": "Escalate ambiguous requests."},
        }

        result = metaskill.build_result("an unmatchable request", index)

        self.assertEqual(result["status"], "unclassified")
        self.assertEqual(result["tier"], "premium_reasoning")

    def test_default_unclassified_alias_uses_premium_reasoning(self):
        index = {
            "engine": "jaccard-zero-token-v3",
            "tasks": [],
            "model_aliases": {"premium_reasoning": "premium-model"},
            "fallback_policy": {},
        }

        result = metaskill.build_result("an unmatchable request", index)

        self.assertEqual(result["model_alias"], "premium-model")
        self.assertEqual(result["engine"], "jaccard-zero-token-v3")

    def test_security_critical_supersedes_many_frontend_keywords(self):
        index = metaskill.load_index()
        result = metaskill.build_result(
            "create UI css component dashboard to fix JWT vulnerability",
            index,
        )
        self.assertEqual(result["archetype"], "security_critical")
        self.assertEqual(result["tier"], "premium_reasoning")
        self.assertIn("jwt", result["score"]["matched_keywords"])

    def test_non_security_frontend_still_uses_ui_route(self):
        index = metaskill.load_index()
        result = metaskill.build_result(
            "create UI css dashboard component",
            index,
        )
        self.assertEqual(result["archetype"], "ui_creative")


if __name__ == "__main__":
    unittest.main()
