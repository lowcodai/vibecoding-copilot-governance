"""Tests for dev-factory/project-template/scripts/orchestrate.py.

Runs the real state machine against a throw-away git repo, with a fake agent CLI in place of
Claude Code. The fake agent's behaviour is scripted per role through FAKE_* env vars.

    python3 -m unittest discover -s dev-factory/tests -v
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
TEMPLATE = HERE.parent / "project-template"
sys.path.insert(0, str(TEMPLATE / "scripts"))
import orchestrate  # noqa: E402

FAKE_AGENT = textwrap.dedent(
    r'''
    #!/usr/bin/env python3
    """Fake agent: behaviour driven by FAKE_<ROLE> (comma-separated, one entry per call)."""
    import json, os, subprocess, sys
    from pathlib import Path
    role = os.environ["ORCHESTRATE_ROLE"]
    sys.stdin.read()
    counter = Path(os.environ["FAKE_STATE_DIR"]) / f"{role}.count"
    n = int(counter.read_text()) if counter.exists() else 0
    counter.write_text(str(n + 1))
    script = os.environ.get(f"FAKE_{role.upper()}", "").split(",")
    action = script[min(n, len(script) - 1)] if script and script[0] else "ok"
    if action == "garbage":
        print("no json here")
        sys.exit(0)
    if role == "dev":
        if action == "nocommit":
            res = {"status": "DONE", "summary": "forgot to commit"}
        elif action == "blocked":
            res = {"status": "BLOCKED", "reason": "ADR gap"}
        elif action == "leak":
            Path(f"cfg_{n}.py").write_text("K = '" + "AKIA" + "Q7W3E5R8T1Y4U6I9" + "'\n")
            subprocess.run(["git", "add", "-A"], check=True)
            subprocess.run(["git", "commit", "-qm", f"feat: leak {n}"], check=True)
            res = {"status": "DONE", "summary": "done"}
        else:
            Path(f"feature_{n}.txt").write_text("x\n")
            subprocess.run(["git", "add", "-A"], check=True)
            subprocess.run(["git", "commit", "-qm", f"feat: step {n}"], check=True)
            res = {"status": "DONE", "summary": "done", "commits": []}
    elif role == "review":
        res = {"verdict": {"ok": "ACCEPTED", "changes": "CHANGES_REQUESTED", "blocked": "BLOCKED"}[action],
               "summary": "s", "findings": [{"severity": "blocker", "issue": "fix it"}] if action == "changes" else []}
    else:
        res = {"verdict": {"ok": "PASS", "fail": "FAIL"}[action], "summary": "s", "failures": []}
    # Mimic `claude -p --output-format json` envelope
    print(json.dumps({"type": "result", "result": "Done.\n```json\n" + json.dumps(res) + "\n```",
                      "usage": {"input_tokens": 1234, "output_tokens": 56}}))
    '''
).lstrip()


def sh(args, cwd):
    subprocess.run(args, cwd=cwd, check=True, capture_output=True, text=True)


class OrchestrateTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.repo = self.tmp / "proj"
        shutil.copytree(TEMPLATE, self.repo)
        sh(["git", "init", "-q", "-b", "main"], self.repo)
        sh(["git", "config", "user.email", "t@example.com"], self.repo)
        sh(["git", "config", "user.name", "t"], self.repo)
        sh(["git", "add", "-A"], self.repo)
        sh(["git", "commit", "-qm", "init"], self.repo)

        fake = self.tmp / "fake_agent.py"
        fake.write_text(FAKE_AGENT)
        fake.chmod(0o755)
        cfg_path = self.repo / ".ai" / "orchestration.yaml"
        cfg = yaml.safe_load(cfg_path.read_text())
        cfg["runner"]["command"] = [sys.executable, str(fake)]
        cfg["validation"]["commands"] = [{"name": "unit", "run": "test ! -f FAIL_MARKER"}]
        cfg_path.write_text(yaml.safe_dump(cfg))

        state_dir = self.tmp / "fake_state"
        state_dir.mkdir()
        self.env_backup = dict(os.environ)
        os.environ["FAKE_STATE_DIR"] = str(state_dir)
        for k in ("FAKE_DEV", "FAKE_REVIEW", "FAKE_TEST"):
            os.environ.pop(k, None)
        self.assertEqual(orchestrate.main(["--repo", str(self.repo), "new", "TASK-0001", "--title", "demo"]), 0)

    def tearDown(self):
        os.environ.clear()
        os.environ.update(self.env_backup)
        shutil.rmtree(self.tmp, ignore_errors=True)

    def run_task(self):
        return orchestrate.main(["--repo", str(self.repo), "run", "TASK-0001"])

    def state(self):
        return json.loads((self.repo / ".ai/runs/TASK-0001/state.json").read_text())

    def test_happy_path_reaches_ready_for_approval(self):
        self.assertEqual(self.run_task(), 0)
        st = self.state()
        self.assertEqual(st["state"], orchestrate.READY)
        self.assertEqual([h["to"] for h in st["history"]], ["DEV", "REVIEW", "TEST", "READY_FOR_APPROVAL"])
        self.assertTrue(Path(st["worktree"]).is_dir())
        self.assertIn("usage", (self.repo / ".ai/runs/TASK-0001/timeline.log").read_text())
        for f in ("dev-result.json", "review-result.json", "test-result.json", "validations.json"):
            self.assertTrue((self.repo / ".ai/runs/TASK-0001" / f).exists(), f)
        # human approval
        self.assertEqual(orchestrate.main(["--repo", str(self.repo), "approve", "TASK-0001", "--by", "me"]), 0)
        self.assertEqual(self.state()["state"], orchestrate.APPROVED)

    def test_review_changes_loop_back_to_dev_with_feedback(self):
        os.environ["FAKE_REVIEW"] = "changes,ok"
        self.assertEqual(self.run_task(), 0)
        st = self.state()
        self.assertEqual([h["to"] for h in st["history"]],
                         ["DEV", "REVIEW", "DEV", "REVIEW", "TEST", "READY_FOR_APPROVAL"])
        self.assertEqual(st["counters"]["review_cycles"], 1)
        order = (self.repo / ".ai/runs/TASK-0001/dev-work-order.md").read_text()
        self.assertIn("fix it", order)

    def test_review_loop_is_bounded(self):
        os.environ["FAKE_REVIEW"] = "changes"
        self.assertEqual(self.run_task(), 2)
        self.assertEqual(self.state()["state"], orchestrate.BLOCKED)

    def test_red_validation_overrides_llm_pass(self):
        # DEV commits a FAIL_MARKER on first run -> validation fails although TEST says PASS
        os.environ["FAKE_TEST"] = "ok"
        orch = orchestrate.Orchestrator(self.repo, "TASK-0001")
        st = orch.init_state()
        orch.step(st)  # PLANNED -> DEV
        Path(st["worktree"], "FAIL_MARKER").write_text("boom")
        sh(["git", "add", "-A"], st["worktree"])
        sh(["git", "commit", "-qm", "chore: marker"], st["worktree"])
        st["state"] = orchestrate.TEST
        orch.step(st)
        self.assertEqual(st["state"], orchestrate.DEV)
        self.assertEqual(st["feedback"]["source"], "test")
        self.assertEqual(st["feedback"]["failures"][0]["validation"], "unit")

    def test_dev_without_commit_is_sent_back(self):
        os.environ["FAKE_DEV"] = "nocommit,ok"
        self.assertEqual(self.run_task(), 0)
        reasons = [h["reason"] for h in self.state()["history"]]
        self.assertIn("no commit produced", reasons)

    def test_dev_blocked_stops_run(self):
        os.environ["FAKE_DEV"] = "blocked"
        self.assertEqual(self.run_task(), 2)
        self.assertIn("ADR gap", self.state()["history"][-1]["reason"])

    def test_unparseable_result_retries_then_blocks(self):
        os.environ["FAKE_REVIEW"] = "garbage"
        self.assertEqual(self.run_task(), 2)
        self.assertIn("no parseable JSON", self.state()["history"][-1]["reason"])

    def test_lock_prevents_concurrent_runs(self):
        with orchestrate.RepoLock(self.repo):
            self.assertEqual(self.run_task(), 1)

    def test_dev_preflight_blocks_when_hooks_are_not_committed(self):
        sh(["git", "rm", "-q", ".claude/hooks/tool_guardian.py"], self.repo)
        sh(["git", "commit", "-qm", "drop hook"], self.repo)
        self.assertEqual(self.run_task(), 2)
        self.assertIn("tool_guardian.py", self.state()["history"][-1]["reason"])

    def test_secrets_scan_validation_sends_leak_back_to_dev(self):
        cfg_path = self.repo / ".ai" / "orchestration.yaml"
        cfg = yaml.safe_load(cfg_path.read_text())
        template_cfg = yaml.safe_load((TEMPLATE / ".ai" / "orchestration.yaml").read_text())
        cfg["validation"]["commands"] = [c for c in template_cfg["validation"]["commands"] if c["name"] == "secrets-scan"]
        cfg_path.write_text(yaml.safe_dump(cfg))
        sh(["git", "commit", "-qam", "cfg"], self.repo)
        os.environ["FAKE_DEV"] = "leak"
        self.assertEqual(self.run_task(), 2)
        st = self.state()
        self.assertEqual(st["state"], orchestrate.BLOCKED)
        self.assertIn("tests failed (cycle 1)", [h["reason"] for h in st["history"]])
        self.assertIn("AWS_ACCESS_KEY", (self.repo / ".ai/runs/TASK-0001/logs/secrets-scan.log").read_text())

    def test_resume_continues_from_persisted_state(self):
        orch = orchestrate.Orchestrator(self.repo, "TASK-0001")
        st = orch.init_state()
        orch.step(st)
        orch.step(st)  # DEV done -> REVIEW, then "crash"
        self.assertEqual(self.state()["state"], orchestrate.REVIEW)
        self.assertEqual(self.run_task(), 0)
        self.assertEqual(self.state()["counters"]["dev_runs"], 1)


class HelpersTest(unittest.TestCase):
    def test_extract_last_fenced_json(self):
        text = 'x ```json\n{"a": 1}\n``` then ```json\n{"verdict": "PASS"}\n```'
        self.assertEqual(orchestrate.extract_result_json(text), {"verdict": "PASS"})

    def test_extract_bare_json(self):
        self.assertEqual(orchestrate.extract_result_json('blah {"status": "DONE"} '), {"status": "DONE"})

    def test_section_prefix_matches_adr_generator_headings(self):
        body = "## Decision\nD\n## Implementation Notes\nI\n## References\nR\n"
        self.assertEqual(orchestrate.section(body, "Implementation"), "I")
        self.assertEqual(orchestrate.section(body, "Decision"), "D")

    def test_truncate_keeps_head_and_tail(self):
        out = orchestrate.truncate("A" * 100 + "B" * 100, 60, "diff")
        self.assertTrue(out.startswith("A"))
        self.assertTrue(out.endswith("B"))
        self.assertIn("truncated", out)


if __name__ == "__main__":
    unittest.main()
