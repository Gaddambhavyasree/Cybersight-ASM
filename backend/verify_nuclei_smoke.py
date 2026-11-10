"""End-to-end Nuclei smoke test against a LOCAL throwaway HTTP server (no DB writes, no third-party targets).

Starts a tiny local web server exposing intentional misconfigurations
(.env, .git/config, openapi.json, actuator), then runs the executor's real
batched runner with the CyberSight custom templates and verifies findings
parse into the expected schema.
"""
import logging, os, socket, sys, threading
import http.server

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

PAGES = {
    "/": "CyberSight smoke target",
    "/.env": "SECRET_KEY=smoke-test-value\nDB_PASSWORD=smoke\n",
    "/.git/config": '[core]\n\trepositoryformatversion = 0\n\tbare = false\n',
    "/openapi.json": '{"openapi":"3.0.0","info":{"title":"Smoke API","version":"1.0"},"paths":{}}',
    "/actuator/health": '{"status":"UP"}',
    "/actuator/env": '{"propertySources":[]}',
}


class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        body = PAGES.get(self.path.split("?")[0])
        if body is None:
            self.send_response(404)
            self.end_headers()
            return
        data = body.encode()
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, *args):
        pass


s = socket.socket()
s.bind(("127.0.0.1", 0))
port = s.getsockname()[1]
s.close()
server = http.server.HTTPServer(("127.0.0.1", port), Handler)
threading.Thread(target=server.serve_forever, daemon=True).start()
print(f"Local smoke server on http://127.0.0.1:{port}/")

from app.services.scanEngine.executors import vulnerabilityAssessment as va

nuclei = va._find_nuclei()
assert nuclei, "nuclei not found"
custom = va._custom_template_dir()
assert custom, "custom template dir missing"
print("nuclei:", nuclei)
print("templates:", custom)

# Two batch URLs prove the -l list-file path dedupes/handles multiple entries.
urls = [f"http://127.0.0.1:{port}/", f"http://127.0.0.1:{port}/login", f"http://127.0.0.1:{port}/"]
rows = va._run(nuclei, urls, timeout=240, extra_args=["-t", custom])
print(f"\nParsed {len(rows)} findings:")
for r in rows:
    print(f"  [{r['severity']}] {r['template_id']} @ {r['url']}")

required = ("url", "template_id", "template_name", "severity", "tags", "references", "matched_at")
missing_schema = [r for r in rows if any(r.get(k) is None for k in ("url", "template_id", "severity"))]
if not rows:
    print("FAIL: no findings — templates did not fire")
    sys.exit(1)
if missing_schema:
    print("FAIL: schema fields missing\n", missing_schema[0])
    sys.exit(1)
ids = {r["template_id"] for r in rows}
sevs = {r["severity"] for r in rows}
print("template ids fired:", ids)
print("severities:", sevs)
if not any(s_ in ("medium", "high", "critical") for s_ in sevs):
    print("FAIL: expected at least one non-info severity (exposed .env/.git)")
    sys.exit(1)
print("\nSMOKE OK — batched Nuclei run parses into valid finding schema")
