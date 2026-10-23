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
import autonomy  # noqa: E402  (imported by orchestrate from the template's .claude/hooks)

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
    (Path(os.environ["FAKE_STATE_DIR"]) / f"{role}.argv").write_text(json.dumps(sys.argv[1:]))
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
        elif action == "protected":
            Path(".claude/hooks/secrets-allowlist.txt").write_text("* GENERIC_SECRET\n")
            subprocess.run(["git", "add", "-A"], check=True)
            subprocess.run(["git", "commit", "-qm", f"chore: widen allowlist {n}"], check=True)
            res = {"status": "DONE", "summary": "done"}
        elif action == "escalate":
            Path(".ai/autonomy.yaml").write_text("version: 1\nlevel: trusted\n")
            subprocess.run(["git", "commit", "-qam", f"chore: raise autonomy {n}"], check=True)
            res = {"status": "DONE", "summary": "done"}
        elif action == "restore":
            subprocess.run(["git", "checkout", "HEAD~1", "--", ".claude/hooks/secrets-allowlist.txt"], check=True)
            subprocess.run(["git", "commit", "-qam", f"fix: restore protected file {n}"], check=True)
            res = {"status": "DONE", "summary": "restored"}
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
        # Keep the template's arguments: the fake agent records them (see test_role_flags_*).
        cfg["runner"]["command"] = [sys.executable, str(fake)] + cfg["runner"]["command"][1:]
        cfg["validation"]["commands"] = [{"name": "unit", "run": "test ! -f FAIL_MARKER"}]
        cfg_path.write_text(yaml.safe_dump(cfg))

        state_dir = self.tmp / "fake_state"
        state_dir.mkdir()
        self.state_dir = state_dir
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

    def argv(self, role):
        return json.loads((self.state_dir / f"{role}.argv").read_text())

    def test_role_flags_dev_keeps_hooks_review_and_test_are_bare(self):
        # --bare skips hooks: DEV must never get it, or tool_guardian/secrets_scanner do not run.
        self.assertEqual(self.run_task(), 0)
        dev = self.argv("dev")
        self.assertNotIn("--bare", dev)
        self.assertIn("--setting-sources", dev)
        self.assertEqual(dev[dev.index("--setting-sources") + 1], "project")
        for role in ("review", "test"):
            args = self.argv(role)
            self.assertIn("--bare", args, role)
            self.assertIn("--settings", args, role)

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

    def test_protected_paths_are_sent_back_to_dev(self):
        os.environ["FAKE_DEV"] = "protected,restore"
        self.assertEqual(self.run_task(), 0)
        st = self.state()
        reasons = [h["reason"] for h in st["history"]]
        self.assertTrue(any(r.startswith("protected paths modified: .claude/hooks/secrets-allowlist.txt") for r in reasons), reasons)
        order = (self.repo / ".ai/runs/TASK-0001/dev-work-order.md").read_text()
        self.assertIn("git checkout", order)
        self.assertEqual(st["state"], orchestrate.READY)

    def test_protected_paths_unfixed_end_blocked(self):
        os.environ["FAKE_DEV"] = "protected,nocommit"
        self.assertEqual(self.run_task(), 2)
        self.assertEqual(self.state()["state"], orchestrate.BLOCKED)

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


FAKE_GH = textwrap.dedent(
    r'''
    #!/usr/bin/env python3
    import json, os, sys
    from pathlib import Path
    with Path(os.environ["FAKE_GH_LOG"]).open("a") as fh:
        fh.write(json.dumps(sys.argv[1:]) + "\n")
    if sys.argv[1:3] == ["pr", "create"]:
        print("https://github.com/o/r/pull/7")
    if sys.argv[1:3] == ["pr", "checks"]:
        sys.exit(int(os.environ.get("FAKE_GH_CHECKS_RC", "0")))
    sys.exit(0)
    '''
).lstrip()


class AutonomyOrchestrateTest(OrchestrateTest):
    """Orchestrator behaviour per autonomy level (ADR-0008)."""

    def setUp(self):
        super().setUp()
        bin_dir = self.tmp / "bin"
        bin_dir.mkdir()
        (bin_dir / "gh").write_text(FAKE_GH)
        (bin_dir / "gh").chmod(0o755)
        self.gh_log = self.tmp / "gh.log"
        os.environ["PATH"] = f"{bin_dir}{os.pathsep}{os.environ['PATH']}"
        os.environ["FAKE_GH_LOG"] = str(self.gh_log)
        os.environ.pop("FAKE_GH_CHECKS_RC", None)

    def set_level(self, level, origin=True):
        autonomy.render(self.repo, level)
        if origin:
            remote = self.tmp / "origin.git"
            sh(["git", "init", "-q", "--bare", "-b", "main", str(remote)], self.tmp)
            sh(["git", "remote", "add", "origin", str(remote)], self.repo)
        sh(["git", "add", "-A"], self.repo)
        sh(["git", "commit", "-qm", f"autonomy {level}"], self.repo)

    def gh_calls(self):
        return [json.loads(line) for line in self.gh_log.read_text().splitlines()] if self.gh_log.exists() else []

    def disallowed(self, role="dev"):
        args = self.argv(role)
        return args[args.index("--disallowedTools") + 1].split(",")

    def test_supervised_publishes_nothing(self):
        self.assertEqual(self.run_task(), 0)
        st = self.state()
        self.assertEqual(st["state"], orchestrate.READY)
        self.assertNotIn("publish", st)
        self.assertEqual(self.gh_calls(), [])
        self.assertIn("WebFetch", self.disallowed())
        self.assertIn("autonomy supervised", (self.repo / ".ai/runs/TASK-0001/timeline.log").read_text())

    def test_branch_pushes_task_branch_and_opens_draft_pr_but_never_merges(self):
        self.set_level("branch")
        self.assertEqual(self.run_task(), 0)
        st = self.state()
        self.assertEqual(st["state"], orchestrate.READY)
        self.assertTrue(st["publish"]["pushed"], st["publish"])
        self.assertEqual(st["publish"]["pr_url"], "https://github.com/o/r/pull/7")
        heads = subprocess.run(["git", "ls-remote", "--heads", "origin"], cwd=self.repo, capture_output=True, text=True).stdout
        self.assertIn("refs/heads/agent/TASK-0001", heads)
        self.assertNotIn("refs/heads/main", heads)
        create = [c for c in self.gh_calls() if c[:2] == ["pr", "create"]]
        self.assertEqual(len(create), 1)
        self.assertIn("--draft", create[0])
        self.assertEqual(create[0][create[0].index("--base") + 1], "main")
        self.assertNotIn("WebFetch", self.disallowed())
        self.assertIn("Task", self.disallowed())
        self.assertEqual(orchestrate.main(["--repo", str(self.repo), "approve", "TASK-0001", "--by", "me"]), 0)
        self.assertEqual(self.state()["state"], orchestrate.APPROVED)
        self.assertNotIn("merge", self.state())
        self.assertFalse([c for c in self.gh_calls() if c[:2] == ["pr", "merge"]])

    def test_branch_push_failure_keeps_task_ready(self):
        self.set_level("branch", origin=False)
        self.assertEqual(self.run_task(), 0)
        st = self.state()
        self.assertEqual(st["state"], orchestrate.READY)
        self.assertFalse(st["publish"]["pushed"])
        self.assertIn("git push failed", st["publish"]["error"])

    def test_trusted_merges_after_human_approval_only_when_checks_are_green(self):
        self.set_level("trusted")
        self.assertEqual(self.run_task(), 0)
        self.assertFalse([c for c in self.gh_calls() if c[:2] == ["pr", "merge"]])   # never before approval
        self.assertEqual(orchestrate.main(["--repo", str(self.repo), "approve", "TASK-0001", "--by", "me"]), 0)
        st = self.state()
        self.assertEqual(st["state"], orchestrate.APPROVED)
        self.assertTrue(st["merge"]["merged"], st["merge"])
        calls = self.gh_calls()
        url = "https://github.com/o/r/pull/7"
        self.assertIn(["pr", "ready", url], calls)
        self.assertIn(["pr", "checks", url], calls)
        self.assertIn(["pr", "merge", url, "--squash"], calls)

    def test_trusted_red_checks_leave_merge_to_a_human(self):
        self.set_level("trusted")
        self.assertEqual(self.run_task(), 0)
        os.environ["FAKE_GH_CHECKS_RC"] = "1"
        self.assertEqual(orchestrate.main(["--repo", str(self.repo), "approve", "TASK-0001", "--by", "me"]), 0)
        st = self.state()
        self.assertEqual(st["state"], orchestrate.APPROVED)
        self.assertFalse(st["merge"]["merged"])
        self.assertIn("checks not all green", st["merge"]["error"])
        self.assertFalse([c for c in self.gh_calls() if c[:2] == ["pr", "merge"]])

    def test_dev_raising_the_level_is_sent_back_even_if_config_forgets_the_path(self):
        cfg_path = self.repo / ".ai" / "orchestration.yaml"
        cfg = yaml.safe_load(cfg_path.read_text())
        cfg["git"]["protected_paths"] = [".claude/"]           # an old, tuned config
        cfg_path.write_text(yaml.safe_dump(cfg))
        sh(["git", "commit", "-qam", "old config"], self.repo)
        os.environ["FAKE_DEV"] = "escalate,ok"   # later runs keep the escalation in the diff
        self.assertEqual(self.run_task(), 2)
        reasons = [h["reason"] for h in self.state()["history"]]
        self.assertTrue(any(r.startswith("protected paths modified: .ai/autonomy.yaml") for r in reasons), reasons)

    def test_autonomy_check_validation_catches_hand_edited_settings(self):
        settings = json.loads((self.repo / ".claude/settings.json").read_text())
        settings["permissions"]["deny"].remove("Bash(curl:*)")
        (self.repo / ".claude/settings.json").write_text(json.dumps(settings, indent=2))
        sh(["git", "commit", "-qam", "hand edit"], self.repo)
        orch = orchestrate.Orchestrator(self.repo, "TASK-0001")
        st = orch.init_state()
        orch.step(st)
        results = orch.run_validations(Path(st["worktree"]), st["base_sha"])
        check = next(r for r in results if r["name"] == "autonomy-check")
        self.assertEqual(results[0]["name"], "autonomy-check")
        self.assertEqual(check["exit_code"], 1)
        self.assertIn("settings.json", check["log_tail"])

    def test_dev_preflight_requires_the_autonomy_module(self):
        sh(["git", "rm", "-q", ".claude/hooks/autonomy.py"], self.repo)
        sh(["git", "commit", "-qm", "drop policy"], self.repo)
        self.assertEqual(self.run_task(), 2)
        self.assertIn("autonomy.py", self.state()["history"][-1]["reason"])
