import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path
import metaskill


class BatchRoutingTests(unittest.TestCase):
    def run_main(self, *args):
        stdout, stderr = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            code = metaskill.main(["metaskill.py", *args])
        return code, stdout.getvalue(), stderr.getvalue()

    def test_batch_routes_multiple_requests_with_same_engine(self):
        with tempfile.TemporaryDirectory() as root:
            file = Path(root) / "batch.json"
            requests = ["build a UI", "rate-limit the API", "unmatchable request"]
            file.write_text(json.dumps(requests), encoding="utf-8")
            rc, stdout, _ = self.run_main("--batch", str(file))
            self.assertEqual(rc, 0)
            got = json.loads(stdout)
            self.assertEqual(len(got), 3)
            for idx, req in enumerate(requests):
                self.assertEqual(got[idx], metaskill.build_result(req, metaskill.load_index()))

    def test_refuses_malformed_or_oversize_batches_without_partial_results(self):
        with tempfile.TemporaryDirectory() as root:
            path = Path(root) / "batch.json"
            for value in ("{}", '[""]', "[]", '["a",23]', "x" * 1_000_001):
                path.write_text(value, encoding="utf-8")
                code, stdout, err = self.run_main("--batch", str(path))
                self.assertNotEqual(code, 0)
                self.assertEqual(stdout, "")
                self.assertIn("Error", err)

    def test_full_five_hundred_tasks_are_supported(self):
        with tempfile.TemporaryDirectory() as root:
            path = Path(root) / "batch.json"
            path.write_text(json.dumps(["design landing page"] * 500), encoding="utf-8")
            code, stdout, _ = self.run_main("--batch", str(path))
            self.assertEqual(code, 0)
            self.assertEqual(len(json.loads(stdout)), 500)

    def test_unknown_flags_fail_instead_of_silently_misrouting(self):
        code, stdout, _ = self.run_main("--unexpected", "create a website")
        self.assertEqual(code, 2)
        self.assertEqual(stdout, "")

    def test_single_request_json_contract_is_preserved(self):
        code, stdout, _ = self.run_main("--json", "build a website")
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(stdout), metaskill.build_result("build a website", metaskill.load_index()))


if __name__ == "__main__":
    unittest.main()
