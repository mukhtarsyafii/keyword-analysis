#!/usr/bin/env python3
"""OAuth loopback flow with a real local callback server.

setup.py uses redirect_uri=http://localhost:1 (nothing listens there), so the
browser hangs after approval. This runs a real server on a free port and
captures the code automatically — no copy-paste, no hang.

Writes the auth URL to /tmp/gsc_auth_url.txt as soon as it is ready.
"""
import http.server, json, os, socketserver, sys, threading, urllib.parse

PORT = 8765
HERMES = os.path.expanduser("~/.hermes")
CLIENT_SECRET = os.path.join(HERMES, "google_client_secret.json")
TOKEN = os.path.join(HERMES, "google_token.json")
URL_FILE = "/tmp/gsc_auth_url.txt"
REDIRECT = f"http://localhost:{PORT}"

SCOPES = [
    "https://www.googleapis.com/auth/webmasters.readonly",
    "https://www.googleapis.com/auth/spreadsheets",
]

result = {}


class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        q = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
        result["code"] = (q.get("code") or [None])[0]
        result["error"] = (q.get("error") or [None])[0]
        body = (b"<html><body style='font-family:sans-serif;padding:40px'>"
                b"<h2>Berhasil.</h2><p>Kembali ke Telegram, tutup tab ini.</p>"
                b"</body></html>")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *a):
        pass


def main():
    from google_auth_oauthlib.flow import Flow

    flow = Flow.from_client_secrets_file(
        CLIENT_SECRET, scopes=SCOPES, redirect_uri=REDIRECT,
        autogenerate_code_verifier=True)
    auth_url, state = flow.authorization_url(access_type="offline", prompt="consent")

    with open(URL_FILE, "w") as f:
        f.write(auth_url)
    print("AUTH_URL_READY", flush=True)

    with socketserver.TCPServer(("127.0.0.1", PORT), Handler) as httpd:
        httpd.timeout = 600
        httpd.handle_request()

    if result.get("error"):
        sys.exit(f"OAuth error: {result['error']}")
    if not result.get("code"):
        sys.exit("No code received (timeout).")

    flow.fetch_token(code=result["code"])
    creds = flow.credentials
    with open(TOKEN, "w") as f:
        f.write(creds.to_json())
    os.chmod(TOKEN, 0o600)
    print("TOKEN_SAVED", TOKEN)
    print("scopes:", " ".join(sorted(creds.scopes or [])))


if __name__ == "__main__":
    main()
