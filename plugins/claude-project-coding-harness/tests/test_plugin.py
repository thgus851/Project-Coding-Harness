"""Port-specific integration checks; only temporary projects are written."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from urllib.error import HTTPError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from harness import Dashboard
from store import Store


class PluginTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="claude-harness-test-")
        self.addCleanup(self.temp.cleanup)
        self.project = Path(self.temp.name)
        (self.project / "main.py").write_text("print('example')\n", encoding="utf-8")

    def test_manifest_paths_and_stdio_mcp(self):
        config = json.loads((ROOT / ".mcp.json").read_text(encoding="utf-8"))
        server = config["mcpServers"]["harness"]
        args = [value.replace("${CLAUDE_PLUGIN_ROOT}", str(ROOT)) for value in server["args"]]
        self.assertTrue(Path(args[0]).is_file())
        requests = [
            {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2025-03-26"}},
            {"jsonrpc": "2.0", "method": "notifications/initialized"},
            {"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
            {"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {"name": "harness_preferences", "arguments": {"project_root": str(self.project)}}},
            {"jsonrpc": "2.0", "id": 4, "method": "tools/call", "params": {"name": "harness_status", "arguments": {"project_root": str(self.project)}}},
            {"jsonrpc": "2.0", "id": 5, "method": "tools/call", "params": {"name": "harness_status", "arguments": {"project_root": "relative/path"}}},
        ]
        env = {**os.environ, **server.get("env", {})}
        completed = subprocess.run([sys.executable, *args], input="\n".join(map(json.dumps, requests)) + "\n", text=True, encoding="utf-8", capture_output=True, env=env, timeout=15)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        responses = [json.loads(line) for line in completed.stdout.splitlines()]
        self.assertEqual([r["id"] for r in responses], [1, 2, 3, 4, 5])
        self.assertEqual(responses[0]["result"]["protocolVersion"], "2025-03-26")
        self.assertEqual(responses[0]["result"]["capabilities"], {"tools": {}})
        names = {tool["name"] for tool in responses[1]["result"]["tools"]}
        self.assertIn("harness_dashboard", names)
        self.assertIn("harness_save_analysis", names)
        self.assertEqual(responses[3]["result"]["structuredContent"]["analysis_status"], "not_analyzed")
        self.assertTrue(responses[4]["result"]["isError"])
        self.assertFalse((self.project / ".coding-harness").exists())

    def test_claude_analysis_handoff_and_memory_consent(self):
        store = Store(str(self.project))
        req = store.request_analysis({"mode": "analyze"})
        self.assertTrue(req["prompt"].startswith("/project-coding-harness:project-coding-harness "))
        self.assertNotIn("$project-coding-harness", req["prompt"])
        self.assertIn("does not authorize a Git commit", req["prompt"])
        self.assertFalse((store.base / "memory.md").exists())
        store.save_analysis({"request_id": req["id"], "name": "Temporary project", "project": "# Project\nExample", "architecture": "# Architecture\nSingle Python entry point", "verification": "# Verification\nSource inspected only", "evidence": ["main.py"], "note_decisions": {}})
        proposal = store.propose({"title": "Entry point", "body": "# Entry point\nmain.py owns startup.", "evidence": ["main.py"]})
        before = (store.base / "memory.md").read_bytes()
        with self.assertRaisesRegex(ValueError, "Explicit user consent"):
            store.decide_proposal({"proposal_id": proposal["id"], "decision": "accept"})
        self.assertEqual((store.base / "memory.md").read_bytes(), before)
        store.decide_proposal({"proposal_id": proposal["id"], "decision": "accept", "user_confirmed": True})
        self.assertIn("main.py owns startup", (store.base / "memory.md").read_text(encoding="utf-8"))

    def test_browser_loopback_and_write_boundary(self):
        dashboard = Dashboard(str(self.project))
        self.addCleanup(dashboard.close)
        with urlopen(dashboard.url, timeout=5) as response:
            html = response.read().decode("utf-8")
            self.assertIn("Claude Code", html)
            self.assertNotIn("window.openai", html)
        with urlopen(dashboard.url + "preferences", timeout=5) as response:
            self.assertIn("settings", json.load(response))
        self.assertFalse((self.project / ".coding-harness").exists())
        origin = dashboard.url.rsplit("/", 2)[0]
        payload = b'{"usage_mode":"on_request"}'
        no_origin = Request(dashboard.url + "configure", data=payload, headers={"Content-Type": "application/json"})
        with self.assertRaises(HTTPError) as caught:
            urlopen(no_origin, timeout=5)
        self.assertEqual(caught.exception.code, 403)
        forbidden = Request(dashboard.url + "save_analysis", data=b"{}", headers={"Content-Type": "application/json", "Origin": origin})
        with self.assertRaises(HTTPError) as caught:
            urlopen(forbidden, timeout=5)
        self.assertEqual(caught.exception.code, 403)
        valid = Request(dashboard.url + "configure", data=payload, headers={"Content-Type": "application/json", "Origin": origin})
        with urlopen(valid, timeout=5) as response:
            self.assertEqual(json.load(response)["settings"]["usage_mode"], "on_request")
        self.assertFalse((self.project / ".coding-harness" / "memory.md").exists())


if __name__ == "__main__":
    unittest.main()
