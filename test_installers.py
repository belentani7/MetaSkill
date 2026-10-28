"""Run the documented installers without touching the user's skill folders."""

import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent
EXPECTED = {"SKILL.md", "index.json"}


class InstallerTests(unittest.TestCase):
    def exercise(self, command):
        with tempfile.TemporaryDirectory() as temporary:
            test_root = Path(temporary)
            destination = test_root / "new-profile"
            destination.mkdir()
            env = os.environ.copy()
            env["METASKILL_INSTALL_ROOT"] = destination.as_posix()

            first = subprocess.run(command, cwd=ROOT, env=env, text=True, capture_output=True)
            self.assertEqual(first.returncode, 0, first.stdout + first.stderr)
            for agent in (".qwen", ".claude"):
                installed = destination / agent / "skills" / "metaskill"
                self.assertEqual({p.name for p in installed.iterdir()}, EXPECTED)
                for name in EXPECTED:
                    self.assertEqual((installed / name).read_bytes(), (ROOT / name).read_bytes())

            second = subprocess.run(command, cwd=ROOT, env=env, text=True, capture_output=True)
            self.assertNotEqual(second.returncode, 0)
            self.assertIn("Already installed", second.stdout + second.stderr)

            blocked = test_root / "blocked-profile"
            existing = blocked / ".claude" / "skills" / "metaskill"
            existing.mkdir(parents=True)
            (existing / "personal.txt").write_text("keep", encoding="utf-8")
            env["METASKILL_INSTALL_ROOT"] = blocked.as_posix()
            rejected = subprocess.run(command, cwd=ROOT, env=env, text=True, capture_output=True)
            self.assertNotEqual(rejected.returncode, 0)
            self.assertFalse((blocked / ".qwen").exists())
            self.assertEqual((existing / "personal.txt").read_text(encoding="utf-8"), "keep")

    def test_bash_installer(self):
        bash = os.environ.get("METASKILL_TEST_BASH") or shutil.which("bash")
        if not bash:
            self.fail("Bash is required for installer verification")
        self.exercise([bash, str(ROOT / "scripts" / "install.sh")])

    def test_powershell_installer(self):
        powershell = (
            os.environ.get("METASKILL_TEST_POWERSHELL")
            or shutil.which("pwsh")
            or shutil.which("powershell.exe")
        )
        if not powershell:
            if os.name == "nt":
                self.fail("PowerShell is required on Windows for installer verification")
            self.skipTest("PowerShell is not installed on this OS")
        self.exercise([powershell, "-NoProfile", "-NonInteractive", "-File", str(ROOT / "scripts" / "install.ps1")])


    def exercise_linked_parent(self, command):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            profile = root / "profile"
            outside = root / "external-skills"
            (profile / ".qwen").mkdir(parents=True)
            outside.mkdir()
            link = profile / ".qwen" / "skills"
            try:
                link.symlink_to(outside, target_is_directory=True)
            except (OSError, NotImplementedError):
                if os.name != "nt":
                    self.skipTest("Directory symlinks unavailable")
                junction = subprocess.run(
                    ["cmd", "/c", "mklink", "/J", str(link), str(outside)],
                    text=True, capture_output=True,
                )
                if junction.returncode != 0:
                    self.skipTest("Directory symlinks and junctions unavailable")
            env = os.environ.copy()
            env["METASKILL_INSTALL_ROOT"] = str(profile)
            result = subprocess.run(command, cwd=ROOT, env=env, text=True, capture_output=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Unsafe linked install path", result.stdout + result.stderr)
            self.assertFalse((outside / "metaskill").exists())
            self.assertFalse((profile / ".claude").exists())

    def test_bash_installer_refuses_linked_parent(self):
        bash = os.environ.get("METASKILL_TEST_BASH") or shutil.which("bash")
        if not bash:
            self.fail("Bash is required for installer verification")
        self.exercise_linked_parent([bash, str(ROOT / "scripts" / "install.sh")])

    def test_powershell_installer_refuses_linked_parent(self):
        powershell = (
            os.environ.get("METASKILL_TEST_POWERSHELL")
            or shutil.which("pwsh")
            or shutil.which("powershell.exe")
        )
        if not powershell:
            if os.name == "nt":
                self.fail("PowerShell is required on Windows for installer verification")
            self.skipTest("PowerShell is not installed on this OS")
        self.exercise_linked_parent([powershell, "-NoProfile", "-NonInteractive", "-File", str(ROOT / "scripts" / "install.ps1")])

if __name__ == "__main__":
    unittest.main()
