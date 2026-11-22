#!/usr/bin/env python3
"""
probe_fusion_mcp.py — probe a local Fusion 360 MCP server over JSON-RPC.

Runs the MCP handshake (initialize -> notifications/initialized -> tools/list)
against Fusion's streamable-HTTP endpoint and prints the tools it exposes.
Stdlib only — no pip installs needed.

Default endpoint: http://127.0.0.1:27182/mcp

If it can't connect:
  - Fusion 360 must be RUNNING, with the server enabled:
    Preferences -> General -> API -> check "Fusion MCP Server (runs locally on
    this device)". The port is configurable there.
  - LICENSE GATE: Autodesk blocks third-party AI tool integration on a
    Personal Use license. Education and commercial subscriptions work.

Examples:
  probe_fusion_mcp.py
  probe_fusion_mcp.py --url http://127.0.0.1:9000/mcp --verbose
"""

import argparse
import json
import sys
import urllib.error
import urllib.request

DEFAULT_URL = "http://127.0.0.1:27182/mcp"

HELP_NOT_RUNNING = """\
Could not connect to {url}
  ({err})

Checklist:
  1. Is Fusion 360 running?
  2. Is the MCP server enabled?  Preferences -> General -> API ->
     "Fusion MCP Server (runs locally on this device)" (note the port shown).
  3. License gate: Autodesk blocks AI tool integration on a Personal Use
     license. An Education or commercial subscription is required — a
     connection that refuses or 403s despite the box being checked is
     usually this."""


def rpc(url, session, payload, verbose=False, expect_response=True):
    """POST one JSON-RPC message; return (parsed_result_or_None, session_id)."""
    headers = {
        "Content-Type": "application/json",
        # Streamable HTTP servers may answer as plain JSON or as an SSE
        # stream; advertise both or the server may reject the request.
        "Accept": "application/json, text/event-stream",
    }
    if session:
        headers["Mcp-Session-Id"] = session
    req = urllib.request.Request(url, data=json.dumps(payload).encode(),
                                 headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=10) as resp:
        session = resp.headers.get("Mcp-Session-Id", session)
        body = resp.read().decode("utf-8", "replace")
    if verbose:
        print(f"--> {payload.get('method')}\n<-- {body[:500]}\n", file=sys.stderr)
    if not expect_response or not body.strip():
        return None, session
    # SSE framing: pull the last 'data:' line; else treat as raw JSON.
    if "data:" in body and body.lstrip().startswith(("event:", "data:", ":")):
        data_lines = [l[5:].strip() for l in body.splitlines()
                      if l.startswith("data:")]
        body = data_lines[-1] if data_lines else body
    msg = json.loads(body)
    if "error" in msg:
        raise RuntimeError(f"JSON-RPC error {msg['error'].get('code')}: "
                           f"{msg['error'].get('message')}")
    return msg.get("result"), session


def main():
    ap = argparse.ArgumentParser(
        description="Probe a local Fusion 360 MCP server: initialize + "
                    "tools/list.")
    ap.add_argument("--url", default=DEFAULT_URL,
                    help=f"MCP endpoint (default {DEFAULT_URL})")
    ap.add_argument("--verbose", action="store_true",
                    help="print raw request/response traffic to stderr")
    args = ap.parse_args()

    init = {
        "jsonrpc": "2.0", "id": 1, "method": "initialize",
        "params": {
            "protocolVersion": "2025-03-26",
            "capabilities": {},
            "clientInfo": {"name": "probe_fusion_mcp", "version": "1.0"},
        },
    }
    try:
        result, session = rpc(args.url, None, init, args.verbose)
        rpc(args.url, session,
            {"jsonrpc": "2.0", "method": "notifications/initialized"},
            args.verbose, expect_response=False)
        tools, session = rpc(args.url, session,
                             {"jsonrpc": "2.0", "id": 2,
                              "method": "tools/list", "params": {}},
                             args.verbose)
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", "replace")[:300]
        if e.code in (401, 403):
            print(f"HTTP {e.code} from {args.url} — the server answered but "
                  "refused the request.\nThis is the usual signature of the "
                  "LICENSE GATE: Personal Use licenses block AI tool "
                  "integration; Education/commercial work.", file=sys.stderr)
        else:
            print(f"HTTP {e.code} from {args.url}: {detail}", file=sys.stderr)
        sys.exit(2)
    except (urllib.error.URLError, ConnectionError, TimeoutError, OSError) as e:
        print(HELP_NOT_RUNNING.format(url=args.url, err=e), file=sys.stderr)
        sys.exit(2)
    except (json.JSONDecodeError, RuntimeError) as e:
        print(f"Connected to {args.url} but the reply was not a valid MCP "
              f"response: {e}\nIs something else listening on this port?",
              file=sys.stderr)
        sys.exit(2)

    info = (result or {}).get("serverInfo", {})
    print(f"Connected: {info.get('name', '?')} {info.get('version', '')} "
          f"(protocol {(result or {}).get('protocolVersion', '?')})")
    if session:
        print(f"Session: {session}")
    tool_list = (tools or {}).get("tools", [])
    print(f"\n{len(tool_list)} tool(s) exposed:")
    for t in tool_list:
        desc = (t.get("description") or "").strip().split("\n")[0]
        print(f"  - {t['name']}: {desc[:100]}")
    if any(t["name"] == "fusion_mcp_execute" for t in tool_list):
        print("\nfusion_mcp_execute is available — it runs arbitrary Fusion "
              "API Python and is the workhorse tool.")


if __name__ == "__main__":
    main()
