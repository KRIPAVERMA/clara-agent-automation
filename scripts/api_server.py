"""
api_server.py
Local HTTP API server for the Clara Agent Automation pipeline.
n8n's HTTP Request nodes call this server to run each pipeline step.

Usage:
    py -3.10 scripts/api_server.py

Then run your n8n workflow at http://localhost:5678
"""

import sys
import os
import subprocess
import json
from http.server import HTTPServer, BaseHTTPRequestHandler

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PYTHON = sys.executable

STEPS = {
    "/run/step1": "scripts/transcribe_onboarding.py",
    "/run/step2": "scripts/extract_account_data.py",
    "/run/step3": "scripts/generate_agent_spec.py",
    "/run/step4": "scripts/apply_onboarding_update.py",
    "/run/step5": "scripts/generate_agent_v2.py",
}


class PipelineHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        path = self.path.split("?")[0]

        if path == "/health":
            self._respond(200, {"status": "ok", "message": "Clara API server is running"})
            return

        if path not in STEPS:
            self._respond(404, {"error": f"Unknown endpoint: {path}"})
            return

        script_rel = STEPS[path]
        script_path = os.path.join(PROJECT_ROOT, script_rel)
        step_num = int(path.split("step")[1])

        print(f"\n[Clara API] Step {step_num}: {script_rel}")

        try:
            result = subprocess.run(
                [PYTHON, script_path],
                capture_output=True,
                text=True,
                cwd=PROJECT_ROOT,
                timeout=300,
            )
            ok = result.returncode == 0
            # Step 1 (Whisper) is optional — transcripts may already exist
            if step_num == 1 and not ok:
                combined = result.stdout + result.stderr
                if any(w in combined for w in ("Missing Python", "whisper", "ffmpeg", "No .mp4", "No .m4a")):
                    ok = True
            self._respond(200 if ok else 500, {
                "step": step_num,
                "script": script_rel,
                "status": "ok" if ok else "error",
                "exit_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
            })
        except subprocess.TimeoutExpired:
            self._respond(500, {"step": step_num, "status": "error", "error": "Timed out after 5 minutes"})
        except Exception as exc:
            self._respond(500, {"step": step_num, "status": "error", "error": str(exc)})

    def _respond(self, code, data):
        body = json.dumps(data, indent=2).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt, *args):
        print(f"[Clara API] {fmt % args}")


if __name__ == "__main__":
    port = 5000
    server = HTTPServer(("localhost", port), PipelineHandler)
    print("=" * 55)
    print("  Clara Agent Automation — API Server")
    print(f"  http://localhost:{port}")
    print(f"  Python: {PYTHON}")
    print(f"  Project root: {PROJECT_ROOT}")
    print("=" * 55)
    for ep, script in STEPS.items():
        print(f"  GET http://localhost:{port}{ep}  ->  {script}")
    print()
    print("  Now run your n8n workflow at http://localhost:5678")
    print()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[Clara API] Stopped.")
