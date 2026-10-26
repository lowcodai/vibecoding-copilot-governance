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


class RepoCase(unittest.TestCase):
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



class OrchestrateTest(RepoCase):
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


FAKE_OPENHANDS = textwrap.dedent(
    r"""
    #!/usr/bin/env python3
    # Fake `openhands --headless --json ... -f FILE`: status lines + JSONL events, scripted by FAKE_OH.
    import json, os, subprocess, sys
    from pathlib import Path
    state = Path(os.environ["FAKE_STATE_DIR"])
    counter = state / "oh.count"
    n = int(counter.read_text()) if counter.exists() else 0
    counter.write_text(str(n + 1))
    order = Path(sys.argv[sys.argv.index("-f") + 1]).read_text()
    (state / "oh.order").write_text(order)
    (state / "oh.env").write_text(json.dumps({k: os.environ.get(k) for k in ("LLM_MODEL", "LLM_BASE_URL", "LLM_API_KEY")}))
    (state / "oh.argv").write_text(json.dumps(sys.argv[1:]))
    script = os.environ.get("FAKE_OH", "ok").split(",")
    action = script[min(n, len(script) - 1)]
    print("Initializing agent...")
    print(json.dumps({"kind": "SystemPromptEvent", "source": "agent"}))
    if action == "crash":
        sys.exit(3)
    steps = int(action[5:]) if action.startswith("steps") else 1
    for i in range(steps):
        Path(f"oh_{n}_{i}.txt").write_text(("line\n" * 40) + str(i))
        subprocess.run(["git", "add", "-A"], check=True)
        subprocess.run(["git", "commit", "-qm", f"feat: oh step {n}.{i}"], check=True)
        print(json.dumps({"kind": "ActionEvent", "source": "agent", "action": {"kind": "TerminalAction", "command": "git commit"}}))
    res = {"status": "BLOCKED", "reason": "need an ADR"} if action == "blocked" else {"status": "DONE", "summary": "done"}
    block = "Done.\n```json\n" + json.dumps(res) + "\n```"
    if action == "finish":
        print(json.dumps({"kind": "ActionEvent", "source": "agent", "action": {"kind": "FinishAction", "message": block}}))
    elif action != "silent":
        print(json.dumps({"kind": "MessageEvent", "source": "agent",
                          "llm_message": {"role": "assistant", "content": [{"type": "text", "text": block}]}}))
    print("Agent finished")
    print("Conversation ID: 0123")
    """
).lstrip()


class ExecutorTest(RepoCase):
    """ADR-0010: DEV on OpenHands where the repo allows it; chunked review; shared lock."""

    def setUp(self):
        super().setUp()
        fake = self.tmp / "fake_openhands.py"
        fake.write_text(FAKE_OPENHANDS)
        fake.chmod(0o755)
        cfg_path = self.repo / ".ai" / "orchestration.yaml"
        cfg = yaml.safe_load(cfg_path.read_text())
        oh = cfg["agents"]["dev"]["executors"]["openhands"]
        oh["command"] = [sys.executable, str(fake)] + oh["command"][1:]
        cfg_path.write_text(yaml.safe_dump(cfg))
        sh(["git", "commit", "-qam", "cfg: fake openhands"], self.repo)
        os.environ.pop("FAKE_OH", None)

    def set_task(self, **fields):
        path = self.repo / ".ai/tasks/TASK-0001.md"
        text = path.read_text()
        for k, v in fields.items():
            text = text.replace(f"\n{k}: ", f"\n{k}: {v}  # was: ", 1) if f"\n{k}: " in text else text.replace("\n---\n", f"\n{k}: {v}\n---\n", 1)
        path.write_text(text)

    def allow(self, executors):
        path = self.repo / ".ai/autonomy.yaml"
        path.write_text(path.read_text().replace("executors: [claude-code]", f"executors: [{executors}]"))
        sh(["git", "commit", "-qam", "allow executors"], self.repo)

    def test_default_executor_is_claude_code(self):
        self.assertEqual(self.run_task(), 0)
        self.assertEqual(self.state()["executor"], "claude-code")
        self.assertFalse((self.state_dir / "oh.count").exists())

    def test_openhands_refused_when_the_repo_does_not_allow_it(self):
        self.set_task(executor="openhands")
        self.assertEqual(self.run_task(), 2)
        self.assertIn("not allowed", self.state()["history"][-1]["reason"])
        self.assertFalse((self.state_dir / "oh.count").exists())

    def test_openhands_allowed_only_once_merged_on_base(self):
        self.set_task(executor="openhands")
        path = self.repo / ".ai/autonomy.yaml"
        path.write_text(path.read_text().replace("executors: [claude-code]", "executors: [claude-code, openhands]"))
        self.assertEqual(self.run_task(), 2)                    # working tree only: intersection refuses
        self.assertIn("not allowed", self.state()["history"][-1]["reason"])

    def test_unknown_executor_blocks(self):
        self.set_task(executor="codex")
        self.assertEqual(self.run_task(), 2)
        self.assertIn("unknown executor", self.state()["history"][-1]["reason"])

    def test_openhands_dev_reaches_ready_with_review_and_test_on_claude_code(self):
        self.allow("claude-code, openhands")
        self.set_task(executor="openhands")
        self.assertEqual(self.run_task(), 0)
        st = self.state()
        self.assertEqual(st["state"], orchestrate.READY)
        self.assertEqual(st["executor"], "openhands")
        self.assertFalse((self.state_dir / "dev.count").exists())   # Claude Code DEV never ran
        self.assertTrue((self.state_dir / "review.count").exists())
        order = (self.state_dir / "oh.order").read_text()
        self.assertIn("Role: DEV — build (OpenHands", order)
        self.assertIn("Work order — DEV — TASK-0001", order)
        env = json.loads((self.state_dir / "oh.env").read_text())
        self.assertEqual(env["LLM_MODEL"], "openai/qwen3.8-27b-nvfp4")
        self.assertTrue(env["LLM_BASE_URL"].endswith("/v1"))
        self.assertEqual(env["LLM_API_KEY"], "local")

    def test_openhands_finish_action_is_parsed(self):
        self.allow("claude-code, openhands")
        self.set_task(executor="openhands")
        os.environ["FAKE_OH"] = "finish"
        self.assertEqual(self.run_task(), 0)

    def test_openhands_blocked_question_stops_the_run(self):
        self.allow("openhands")
        self.set_task(executor="openhands")
        os.environ["FAKE_OH"] = "blocked"
        self.assertEqual(self.run_task(), 2)
        self.assertIn("need an ADR", self.state()["history"][-1]["reason"])

    def test_openhands_crash_and_silence_block(self):
        self.allow("openhands")
        self.set_task(executor="openhands")
        os.environ["FAKE_OH"] = "crash"
        self.assertEqual(self.run_task(), 2)
        self.assertIn("exited 3", self.state()["history"][-1]["reason"])

    def test_openhands_without_result_blocks(self):
        self.allow("openhands")
        self.set_task(executor="openhands")
        os.environ["FAKE_OH"] = "silent"
        self.assertEqual(self.run_task(), 2)
        self.assertIn("no parseable JSON", self.state()["history"][-1]["reason"])

    def test_runner_prefix_wraps_every_agent(self):
        wrapper = self.tmp / "run-as-agent"
        wrapper.write_text(f"#!/bin/sh\necho \"$@\" >> {self.state_dir}/prefix.log\nexec \"$@\"\n")
        wrapper.chmod(0o755)
        cfg_path = self.repo / ".ai" / "orchestration.yaml"
        cfg = yaml.safe_load(cfg_path.read_text())
        cfg["runner"]["prefix"] = [str(wrapper)]
        cfg_path.write_text(yaml.safe_dump(cfg))
        sh(["git", "commit", "-qam", "prefix"], self.repo)
        self.allow("claude-code, openhands")
        self.set_task(executor="openhands")
        self.assertEqual(self.run_task(), 0)
        log = (self.state_dir / "prefix.log").read_text().splitlines()
        self.assertEqual(len(log), 4)                           # DEV (openhands), REVIEW, validation, TEST
        self.assertIn("fake_openhands.py", log[0])

    def test_runner_prefix_from_environment_also_wraps_validations(self):
        wrapper = self.tmp / "run-as-agent"
        wrapper.write_text(f"#!/bin/sh\necho \"$@\" >> {self.state_dir}/prefix.log\nexec \"$@\"\n")
        wrapper.chmod(0o755)
        os.environ["ORCHESTRATE_RUNNER_PREFIX"] = str(wrapper)
        self.assertEqual(self.run_task(), 0)
        log = (self.state_dir / "prefix.log").read_text().splitlines()
        self.assertEqual(len(log), 4)                           # DEV, REVIEW, validation `unit`, TEST
        self.assertTrue(log[2].startswith("sh -c test ! -f FAIL_MARKER"), log[2])

    def shrink_review_budget(self):
        cfg_path = self.repo / ".ai" / "orchestration.yaml"
        cfg = yaml.safe_load(cfg_path.read_text())
        cfg["gateways"]["cc-review"]["context_tokens"] = 1300
        cfg["gateways"]["cc-review"]["max_output_tokens"] = 100
        cfg["agents"]["review"]["overhead_tokens"] = 100
        cfg_path.write_text(yaml.safe_dump(cfg))
        sh(["git", "commit", "-qam", "small review budget"], self.repo)

    def test_large_diff_is_reviewed_in_commit_chunks(self):
        self.shrink_review_budget()
        self.allow("openhands")
        self.set_task(executor="openhands")
        os.environ["FAKE_OH"] = "steps8"
        self.assertEqual(self.run_task(), 0)
        run = self.repo / ".ai/runs/TASK-0001"
        chunks = sorted(run.glob("review-*-result.json"))
        self.assertGreater(len(chunks), 1)
        self.assertIn("REVIEW in", (run / "timeline.log").read_text())
        self.assertEqual(json.loads((run / "review-result.json").read_text())["verdict"], "ACCEPTED")
        self.assertIn(f"Chunk {len(chunks)}/{len(chunks)}", (run / "review-work-order.md").read_text())

    def test_one_chunk_requesting_changes_sends_the_task_back(self):
        self.shrink_review_budget()
        self.allow("openhands")
        self.set_task(executor="openhands")
        os.environ["FAKE_OH"] = "steps8,ok"
        os.environ["FAKE_REVIEW"] = "ok,changes,ok"
        self.assertEqual(self.run_task(), 0)
        st = self.state()
        self.assertIn("review requested changes (cycle 1)", [h["reason"] for h in st["history"]])
        order = (self.state_dir / "oh.order").read_text()
        self.assertIn('"chunk": 2', order)

    def test_shared_lock_serialises_repos(self):
        lock = self.tmp / "model.lock"
        cfg_path = self.repo / ".ai" / "orchestration.yaml"
        cfg = yaml.safe_load(cfg_path.read_text())
        cfg["execution"]["shared_lock"] = str(lock)
        cfg_path.write_text(yaml.safe_dump(cfg))
        other = self.tmp / "other"
        other.mkdir()
        with orchestrate.RepoLock(other, str(lock)):
            self.assertEqual(self.run_task(), 1)
        self.assertEqual(self.run_task(), 0)


class HelpersTest(unittest.TestCase):
    def test_extract_last_fenced_json(self):
        text = 'x ```json\n{"a": 1}\n``` then ```json\n{"verdict": "PASS"}\n```'
        self.assertEqual(orchestrate.extract_result_json(text), {"verdict": "PASS"})

    def test_openhands_final_text_prefers_the_last_agent_message(self):
        out = "\n".join([
            "Initializing agent...",
            json.dumps({"kind": "MessageEvent", "source": "user", "llm_message": {"content": [{"type": "text", "text": "task"}]}}),
            json.dumps({"kind": "MessageEvent", "source": "agent", "llm_message": {"content": [{"type": "text", "text": "first"}]}}),
            "{not json",
            json.dumps({"kind": "ActionEvent", "source": "agent", "action": {"kind": "FinishAction", "message": "final"}}),
            "Goodbye!",
        ])
        self.assertEqual(orchestrate.openhands_final_text(out), "final")
        self.assertEqual(orchestrate.openhands_final_text("nothing"), "")

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
        seq = os.environ.get("FAKE_GH_CHECKS")          # e.g. "pending,fail,pass" — one entry per call
        if not seq:
            sys.exit(int(os.environ.get("FAKE_GH_CHECKS_RC", "0")))
        counter = Path(os.environ["FAKE_GH_LOG"] + ".checks")
        n = int(counter.read_text()) if counter.exists() else 0
        counter.write_text(str(n + 1))
        items = seq.split(",")
        state = items[min(n, len(items) - 1)]
        out, rc = {"pass": ("ci\tpass\t1m\thttps://github.com/o/r/actions/runs/41/job/1", 0),
                   "fail": ("ci\tfail\t1m\thttps://github.com/o/r/actions/runs/42/job/7", 1),
                   "pending": ("ci\tpending\t0\thttps://github.com/o/r/actions/runs/43/job/9", 8),
                   "none": ("no checks reported on the 'agent/TASK-0001' branch", 1)}[state]
        print(out)
        sys.exit(rc)
    if sys.argv[1:3] == ["run", "view"]:
        print("ci / test\tFAILED tests/test_x.py::test_y - AssertionError")
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
        os.environ.pop("FAKE_GH_CHECKS", None)

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


class YoloOrchestrateTest(AutonomyOrchestrateTest):
    """Autonomy `yolo` (ADR-0009): no human approval, merge on green CI, red CI goes back to DEV."""

    def setUp(self):
        super().setUp()
        cfg_path = self.repo / ".ai" / "orchestration.yaml"
        cfg = yaml.safe_load(cfg_path.read_text())
        cfg["limits"].update({"ci_poll_sec": 0, "ci_no_checks_grace_sec": 0, "max_ci_cycles": 2})
        cfg_path.write_text(yaml.safe_dump(cfg))
        self.set_level("yolo")

    def merges(self):
        return [c for c in self.gh_calls() if c[:2] == ["pr", "merge"]]

    def test_green_ci_is_merged_without_approval(self):
        os.environ["FAKE_GH_CHECKS"] = "pending,pass"
        self.assertEqual(self.run_task(), 0)
        st = self.state()
        self.assertEqual(st["state"], orchestrate.APPROVED)
        self.assertTrue(st["merge"]["merged"])
        self.assertEqual(st["merge"]["checks"], "green")
        create = [c for c in self.gh_calls() if c[:2] == ["pr", "create"]]
        self.assertEqual(len(create), 1)
        self.assertNotIn("--draft", create[0])                      # ready PR, nobody has to undraft it
        self.assertEqual(self.merges(), [["pr", "merge", "https://github.com/o/r/pull/7", "--squash"]])
        self.assertEqual([h["to"] for h in st["history"]][-2:], ["READY_FOR_APPROVAL", "APPROVED"])

    def test_red_ci_goes_back_to_dev_with_the_logs_then_merges(self):
        os.environ["FAKE_GH_CHECKS"] = "fail,pass"
        self.assertEqual(self.run_task(), 0)
        st = self.state()
        self.assertEqual(st["state"], orchestrate.APPROVED)
        self.assertEqual(st["counters"]["ci_cycles"], 1)
        order = (self.repo / ".ai/runs/TASK-0001/dev-work-order.md").read_text()
        self.assertIn("CI is red", order)
        self.assertIn("FAILED tests/test_x.py::test_y", order)        # failing logs reach DEV
        self.assertEqual(len([c for c in self.gh_calls() if c[:2] == ["pr", "create"]]), 1)   # PR reused
        self.assertEqual(self.argv("dev").count("--bare"), 0)
        heads = subprocess.run(["git", "ls-remote", "--heads", "origin"], cwd=self.repo, capture_output=True, text=True).stdout
        self.assertNotIn("refs/heads/main", heads)                    # never pushed main
        self.assertEqual(len(self.merges()), 1)

    def test_ci_still_red_after_max_cycles_blocks_without_merging(self):
        os.environ["FAKE_GH_CHECKS"] = "fail"
        self.assertEqual(self.run_task(), 2)
        st = self.state()
        self.assertEqual(st["state"], orchestrate.BLOCKED)
        self.assertIn("max_ci_cycles=2", st["history"][-1]["reason"])
        self.assertEqual(self.merges(), [])

    def test_repo_without_ci_is_merged(self):
        os.environ["FAKE_GH_CHECKS"] = "none"
        self.assertEqual(self.run_task(), 0)
        self.assertEqual(self.state()["merge"]["checks"], "none")

    def test_no_pull_request_blocks(self):
        sh(["git", "remote", "remove", "origin"], self.repo)
        self.assertEqual(self.run_task(), 2)
        self.assertIn("no pull request", self.state()["history"][-1]["reason"])


# The level-specific classes reuse the fixtures of their parent, not its test methods (each level
# has its own expectations; the parent's tests already ran at their own level).
for _cls, _parent in ((AutonomyOrchestrateTest, OrchestrateTest), (YoloOrchestrateTest, AutonomyOrchestrateTest)):
    for _name in dir(_parent):
        if _name.startswith("test_") and _name not in _cls.__dict__:
            setattr(_cls, _name, None)
