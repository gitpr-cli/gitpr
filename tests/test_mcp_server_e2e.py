"""End-to-end tests for the GitPR MCP server.

These tests spawn the real server as a subprocess and speak JSON-RPC over
stdio, asserting that tool calls return promptly even when handlers do
blocking work (git subprocess, lazy imports, downloads).  They are the
regression net for the event-loop hang fixed by the ``_offload`` decorator:
sync handlers used to run inline on the asyncio loop and freeze the whole
stdio server.

Network independence: ``GITPR_SKIP_SMART_EXCLUDES=1`` disables the OTA
smart-excludes download in ``src.core`` so the tests never touch the network.
"""

import json
import os
import queue
import subprocess
import sys
import threading
import time
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

#: Generous per-response deadline; the regression being guarded against is
#: an *infinite* hang, so anything bounded is a pass.  Kept at 60s per the
#: fix plan so a genuinely stuck server fails the test instead of the CI.
RESPONSE_TIMEOUT = 60.0


class _StdioServer:
    """Handle to a running MCP server subprocess with a line reader thread.

    ``select`` does not work on Windows pipes, so stdout lines are pulled by
    a dedicated thread and pushed into a queue the test drains with a
    deadline.  stderr is drained the same way so the pipe buffer can never
    fill up and block the server.
    """

    def __init__(self):
        env = os.environ.copy()
        env["GITPR_SKIP_SMART_EXCLUDES"] = "1"
        self.proc = subprocess.Popen(
            [sys.executable, "-m", "src.mcp_server"],
            cwd=str(REPO_ROOT),
            env=env,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            encoding="utf-8",
            errors="replace",
        )
        self.out_q = queue.Queue()
        self.stderr_lines = []
        self._stdout_thread = threading.Thread(
            target=self._drain,
            args=(self.proc.stdout, self.out_q),
            daemon=True,
        )
        self._stderr_thread = threading.Thread(
            target=self._drain,
            args=(self.proc.stderr, self.stderr_lines),
            daemon=True,
        )
        self._stdout_thread.start()
        self._stderr_thread.start()

    @staticmethod
    def _drain(stream, sink):
        """Copy every line from *stream* into *sink* (Queue or list)."""
        try:
            for line in stream:
                if isinstance(sink, queue.Queue):
                    sink.put(line)
                else:
                    sink.append(line)
        except Exception:
            pass  # stream closed by shutdown; best-effort drain

    def send(self, payload):
        """Send one JSON-RPC message."""
        self.proc.stdin.write(json.dumps(payload) + "\n")
        self.proc.stdin.flush()

    def wait_for_id(self, request_id, timeout=RESPONSE_TIMEOUT):
        """Block until a JSON-RPC message with the given id arrives.

        Returns the parsed message; raises AssertionError on timeout or if
        the server process died while waiting.
        """
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if self.proc.poll() is not None:
                stderr = "".join(self.stderr_lines[-30:])
                raise AssertionError(
                    f"MCP server exited with code {self.proc.returncode}.\n"
                    f"stderr tail:\n{stderr}"
                )
            try:
                line = self.out_q.get(timeout=0.5)
            except queue.Empty:
                continue
            try:
                message = json.loads(line)
            except json.JSONDecodeError:
                continue  # not JSON (should not happen); keep waiting
            if message.get("id") == request_id:
                return message
        raise AssertionError(
            f"No JSON-RPC response for id {request_id} within {timeout}s "
            f"(server alive: {self.proc.poll() is None})."
        )

    def shutdown(self):
        """Terminate the server, escalating to kill if it lingers."""
        if self.proc.poll() is None:
            self.proc.terminate()
            try:
                self.proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self.proc.kill()
                self.proc.wait(timeout=10)
        for stream in (self.proc.stdin, self.proc.stdout, self.proc.stderr):
            if stream:
                try:
                    stream.close()
                except Exception:
                    pass


def _initialize(server):
    """Perform the JSON-RPC handshake; returns the initialize response."""
    server.send(
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "pytest", "version": "1.0"},
            },
        }
    )
    response = server.wait_for_id(1)
    server.send({"jsonrpc": "2.0", "method": "notifications/initialized"})
    return response


def _call_tool(server, request_id, name, arguments=None):
    """Send a tools/call request; returns the parsed tool result."""
    server.send(
        {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": "tools/call",
            "params": {"name": name, "arguments": arguments or {}},
        }
    )
    message = server.wait_for_id(request_id)
    return message.get("result", {})


class TestMcpServerStdio(unittest.TestCase):
    """JSON-RPC over stdio against the real server subprocess."""

    def setUp(self):
        self.server = _StdioServer()

    def tearDown(self):
        self.server.shutdown()

    def test_initialize_handshake(self):
        """initialize answers with the negotiated protocol version."""
        response = _initialize(self.server)
        self.assertIn("protocolVersion", response.get("result", {}))

    def test_run_linter_returns_promptly(self):
        """run_linter — the original hang repro — answers well under the deadline."""
        _initialize(self.server)
        result = _call_tool(self.server, 2, "run_linter")
        self.assertIn("content", result)
        self.assertFalse(result.get("isError", False))

        # The tool payload is a JSON string inside content[0].text.
        text = result["content"][0]["text"]
        payload = json.loads(text)
        self.assertIn("status", payload)

    def test_get_git_context_returns_promptly(self):
        """get_git_context answers with branch and repository fields."""
        _initialize(self.server)
        result = _call_tool(self.server, 2, "get_git_context")
        self.assertIn("content", result)
        self.assertFalse(result.get("isError", False))

        payload = json.loads(result["content"][0]["text"])
        self.assertIn("branch", payload)
        self.assertIn("repository", payload)

    def test_tools_respond_after_each_other(self):
        """Back-to-back tool calls each get their own response by id."""
        _initialize(self.server)
        first = _call_tool(self.server, 2, "get_git_context")
        self.assertIn("content", first)
        second = _call_tool(self.server, 3, "run_linter")
        self.assertIn("content", second)


class TestMcpToolCliMode(unittest.TestCase):
    """The --tool CLI path stays synchronous and prints clean JSON."""

    def _run_tool_cli(self, *args):
        env = os.environ.copy()
        env["GITPR_SKIP_SMART_EXCLUDES"] = "1"
        return subprocess.run(
            [sys.executable, "-m", "src.mcp_server", "--tool", *args],
            cwd=str(REPO_ROOT),
            env=env,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=120,
        )

    def test_run_linter_tool_returns_json(self):
        """--tool run_linter exits 0 and prints a JSON payload on stdout."""
        proc = self._run_tool_cli("run_linter")
        self.assertEqual(proc.returncode, 0, msg=f"stderr:\n{proc.stderr}")
        payload = json.loads(proc.stdout)
        self.assertIn("status", payload)

    def test_unknown_tool_exits_nonzero(self):
        """--tool with an unknown name exits 1 with an error payload."""
        proc = self._run_tool_cli("no_such_tool")
        self.assertEqual(proc.returncode, 1)
        # The error payload is the first stdout line; help text follows.
        payload = json.loads(proc.stdout.splitlines()[0])
        self.assertEqual(payload["status"], "error")


if __name__ == "__main__":
    unittest.main()
