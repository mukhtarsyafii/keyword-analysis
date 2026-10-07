#!/usr/bin/env python3
"""Re-auth: Google Sheets (read/write) + Search Console readonly, one consent.

Loopback :8765, prints the URL to /tmp/gsc_auth_url.txt, blocks until approved,
overwrites ~/.hermes/google_token.json. Needed so the LP ITGID tab can be
written directly (Sheets API) while fetch_gsc.py keeps working.
"""
import http.server, json, os, socketserver, sys, urllib.parse

PORT = 8765
HERMES = os.path.expanduser("~/.hermes")
CLIENT_SECRET = os.path.join(HERMES, "google_client_secret.json")
TOKEN = os.path.join(HERMES, "google_token.json")
URL_FILE = "/tmp/gsc_auth_url.txt"
REDIRECT = f"http://localhost:{PORT}"
SCOPES = ["https://www.googleapis.com/auth/spreadsheets",
          "https://www.googleapis.com/auth/webmasters.readonly"]

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
        httpd.timeout = 900
        httpd.handle_request()

    if result.get("error"):
        sys.exit(f"OAuth error: {result['error']}")
    if not result.get("code"):
        sys.exit("no code received (timeout)")
    flow.fetch_token(code=result["code"])
    creds = flow.credentials
    with open(TOKEN, "w") as f:
        f.write(creds.to_json())
    print("TOKEN_SAVED", creds.scopes)


main()
