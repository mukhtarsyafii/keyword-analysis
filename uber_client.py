#!/usr/bin/env python3
"""Minimal MCP client for the Ubersuggest server (uses Hermes' stored OAuth token).

Usage:
  python3 uber_client.py <tool_name> '<json args>'
  python3 uber_client.py --list

Prints the tool result as JSON on stdout.
"""
import json, os, sys, urllib.request

TOKEN_FILE = os.path.expanduser("~/.hermes/mcp-tokens/ubersuggest.json")
URL = "https://ubersuggest-mcp.neilpatelapi.com/mcp"


def _token():
    d = json.load(open(TOKEN_FILE))
    return d["access_token"]


def _post(payload, session_id=None):
    req = urllib.request.Request(URL, data=json.dumps(payload).encode(), headers={
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
        "Authorization": f"Bearer {_token()}",
        **({"mcp-session-id": session_id} if session_id else {}),
    })
    with urllib.request.urlopen(req, timeout=180) as r:
        sid = r.headers.get("mcp-session-id")
        body = r.read().decode()
    # SSE or plain JSON
    if body.startswith("event:") or "\ndata: " in body or body.startswith("data:"):
        for line in body.splitlines():
            if line.startswith("data: "):
                return json.loads(line[6:]), sid
        raise RuntimeError("no data line in SSE: " + body[:200])
    return (json.loads(body) if body.strip() else None), sid


def _notify(payload, sid):
    try:
        _post(payload, sid)
    except Exception:
        pass


def main():
    init, sid = _post({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {
        "protocolVersion": "2024-11-05", "capabilities": {},
        "clientInfo": {"name": "kw-dash", "version": "1"}}})
    _notify({"jsonrpc": "2.0", "method": "notifications/initialized"}, sid)

    if "--list" in sys.argv:
        res, _ = _post({"jsonrpc": "2.0", "id": 2, "method": "tools/list"}, sid)
        for t in res["result"]["tools"]:
            print(t["name"], "|", t.get("description", "")[:70])
        return

    name = sys.argv[1]
    args = json.loads(sys.argv[2]) if len(sys.argv) > 2 else {}
    res, _ = _post({"jsonrpc": "2.0", "id": 3, "method": "tools/call",
                    "params": {"name": name, "arguments": args}}, sid)
    if "error" in res:
        print(json.dumps(res["error"]), file=sys.stderr); sys.exit(1)
    r = res["result"]
    if r.get("isError"):
        print(json.dumps({"isError": True, "content": r.get("content")}), file=sys.stderr); sys.exit(1)
    out = []
    for c in r.get("content", []):
        if c.get("type") == "text":
            try:
                out.append(json.loads(c["text"]))
            except json.JSONDecodeError:
                out.append(c["text"])
    print(json.dumps(out[0] if len(out) == 1 else out, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
