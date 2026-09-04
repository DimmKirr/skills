"""genimage.py adapter tests (KUT-215) — mocked HTTP only, no real providers."""
import base64
import json
import subprocess
import sys
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
GENIMAGE = SKILL_DIR / "scripts" / "genimage.py"

PNG_1PX = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR4nGNgYGBgAAAABQAB"
    "h6FO1AAAAABJRU5ErkJggg=="
)


def run(args, env):
    return subprocess.run([sys.executable, str(GENIMAGE), *args],
                          capture_output=True, text=True, env=env)


def base_env():
    import os
    env = dict(os.environ)
    for k in ("KIT_IMAGE_PROVIDER", "KIT_IMAGE_ENDPOINT", "OPENAI_API_KEY"):
        env.pop(k, None)
    return env


class TestProviderUnavailable:
    def test_no_provider_is_structured_error(self, tmp_path):
        out = run(["--prompt", "a carrot", "--out", str(tmp_path / "x.png")], base_env())
        assert out.returncode == 3
        err = json.loads(out.stdout or out.stderr)
        assert "provider unavailable" in err["error"]
        assert not (tmp_path / "x.png").exists()

    def test_provider_none_same(self, tmp_path):
        env = base_env()
        env["KIT_IMAGE_PROVIDER"] = "none"
        out = run(["--prompt", "a carrot", "--out", str(tmp_path / "x.png")], env)
        assert out.returncode == 3


class _FakeAPI(BaseHTTPRequestHandler):
    def do_POST(self):
        body = json.dumps({"data": [{"b64_json": base64.b64encode(PNG_1PX).decode()}]})
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(body.encode())

    def log_message(self, *a):
        pass


class TestMockedProvider:
    def test_openai_provider_writes_png(self, tmp_path):
        srv = HTTPServer(("127.0.0.1", 0), _FakeAPI)
        t = threading.Thread(target=srv.serve_forever, daemon=True)
        t.start()
        try:
            env = base_env()
            env.update(KIT_IMAGE_PROVIDER="openai",
                       KIT_IMAGE_ENDPOINT=f"http://127.0.0.1:{srv.server_port}/v1/images",
                       OPENAI_API_KEY="test-key")
            out_file = tmp_path / "carrot.png"
            out = run(["--prompt", "a carrot", "--out", str(out_file)], env)
            assert out.returncode == 0, out.stderr
            assert out_file.read_bytes().startswith(b"\x89PNG")
            meta = json.loads(out.stdout)
            assert meta["out"] == str(out_file)
        finally:
            srv.shutdown()

    def test_missing_key_is_error(self, tmp_path):
        env = base_env()
        env["KIT_IMAGE_PROVIDER"] = "openai"
        out = run(["--prompt", "x", "--out", str(tmp_path / "x.png")], env)
        assert out.returncode != 0


class _FakeGemini(BaseHTTPRequestHandler):
    def do_POST(self):
        body = json.dumps({"candidates": [{"content": {"parts": [
            {"text": "here is your image"},
            {"inlineData": {"mimeType": "image/png",
                            "data": base64.b64encode(PNG_1PX).decode()}},
        ]}}]})
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(body.encode())

    def log_message(self, *a):
        pass


class TestGeminiProvider:
    def test_gemini_provider_writes_png(self, tmp_path):
        srv = HTTPServer(("127.0.0.1", 0), _FakeGemini)
        t = threading.Thread(target=srv.serve_forever, daemon=True)
        t.start()
        try:
            env = base_env()
            env.update(KIT_IMAGE_PROVIDER="gemini",
                       KIT_IMAGE_ENDPOINT=f"http://127.0.0.1:{srv.server_port}/v1beta",
                       GEMINI_API_KEY="test-key")
            out_file = tmp_path / "carrot.png"
            out = run(["--prompt", "a carrot", "--out", str(out_file)], env)
            assert out.returncode == 0, out.stderr or out.stdout
            assert out_file.read_bytes().startswith(b"\x89PNG")
            meta = json.loads(out.stdout)
            assert meta["provider"] == "gemini"
        finally:
            srv.shutdown()

    def test_gemini_missing_key_is_error(self, tmp_path):
        env = base_env()
        env["KIT_IMAGE_PROVIDER"] = "gemini"
        out = run(["--prompt", "x", "--out", str(tmp_path / "x.png")], env)
        assert out.returncode != 0
