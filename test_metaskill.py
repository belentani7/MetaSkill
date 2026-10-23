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

    def test_unmatched_request_abstains_even_if_quick_fix_exists(self):
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

        self.assertEqual(result["status"], "unclassified")
        self.assertTrue(result["requires_human_review"])
        self.assertIsNone(result["tier"])
        self.assertIsNone(result["model_alias"])
        self.assertNotIn("task_id", result)
        self.assertNotIn("request", result)

    def test_no_quick_fix_task_keeps_request_unclassified(self):
        index = {
            "engine": "jaccard-zero-token-v3",
            "tasks": [],
            "model_aliases": {"premium_reasoning": "premium-model"},
            "fallback_policy": {"note": "Escalate ambiguous requests."},
        }

        result = metaskill.build_result("an unmatchable request", index)

        self.assertEqual(result["status"], "unclassified")
        self.assertIsNone(result["tier"])

    def test_default_unclassified_alias_uses_premium_reasoning(self):
        index = {
            "engine": "jaccard-zero-token-v3",
            "tasks": [],
            "model_aliases": {"premium_reasoning": "premium-model"},
            "fallback_policy": {},
        }

        result = metaskill.build_result("an unmatchable request", index)

        self.assertIsNone(result["model_alias"])
        self.assertEqual(result["engine"], "jaccard-zero-token-v3")


    def test_classified_result_does_not_echo_private_prompt(self):
        index = {
            "engine": "jaccard-zero-token-v3",
            "tasks": [{
                "id": "arch_security", "archetype": "security", "label": "Security",
                "complexity": 4, "keywords": ["security"],
                "routing": {"tier": "premium_reasoning", "fallback": [], "tools": []},
                "instructions": "Review carefully.",
            }],
            "model_aliases": {"premium_reasoning": "premium-model"},
        }
        secret = "security audit private-access-token-12345"
        result = metaskill.build_result(secret, index)
        self.assertEqual(result["status"], "classified")
        self.assertNotIn(secret, __import__("json").dumps(result))
        self.assertNotIn("request", result)

    def test_unclassified_output_has_no_automatic_model_selection(self):
        result = metaskill.build_result("unrecognized xyzxyz", {
            "engine": "jaccard-zero-token-v3", "tasks": [],
            "model_aliases": {"premium_reasoning": "paid-model"},
        })
        self.assertEqual(result["status"], "unclassified")
        self.assertTrue(result["requires_human_review"])
        self.assertIsNone(result["model_alias"])


    def test_single_weak_keyword_abstains_without_selecting_paid_model(self):
        index = {
            "engine": "jaccard-zero-token-v3",
            "tasks": [{
                "id": "arch_security", "archetype": "security", "label": "Security",
                "complexity": 5,
                "keywords": ["security", "owasp", "xss", "csrf", "jwt", "crypto"],
                "routing": {"tier": "premium_reasoning", "fallback": [], "tools": []},
            }],
            "model_aliases": {"premium_reasoning": "paid-model"},
        }
        result = metaskill.build_result("security", index)
        self.assertEqual(result["status"], "unclassified")
        self.assertTrue(result["requires_human_review"])
        self.assertIsNone(result["model_alias"])

    def test_single_strong_keyword_classifies_when_coverage_exceeds_twenty_percent(self):
        index = {
            "tasks": [{
                "id": "arch_docs", "archetype": "docs", "label": "Docs",
                "complexity": 2, "keywords": ["readme", "guide", "wiki", "manual"],
                "routing": {"tier": "budget_fast", "fallback": [], "tools": []},
            }],
            "model_aliases": {"budget_fast": "fast-model"},
        }
        result = metaskill.build_result("readme", index)
        self.assertEqual(result["status"], "classified")
        self.assertEqual(result["task_id"], "arch_docs")

    def test_two_matches_classify_even_with_low_coverage(self):
        index = {
            "tasks": [{
                "id": "arch_backend", "archetype": "backend", "label": "Backend",
                "complexity": 4,
                "keywords": ["api", "backend"] + ["unused" + str(i) for i in range(20)],
                "routing": {"tier": "standard_coding", "fallback": [], "tools": []},
            }],
            "model_aliases": {"standard_coding": "code-model"},
        }
        result = metaskill.build_result("api backend", index)
        self.assertEqual(result["status"], "classified")
        self.assertEqual(result["task_id"], "arch_backend")
        self.assertEqual(len(result["score"]["matched_keywords"]), 2)


if __name__ == "__main__":
    unittest.main()
