# Fusion 360 via its local MCP server

Fusion 360 ships a local MCP (Model Context Protocol) server that lets an agent drive the full Fusion API over HTTP. It turns Fusion from a GUI-only tool into a scriptable stage of the pipeline — but it has a hard license gate and a rendering API with real gaps, so know what it's for before reaching for it.

## Enabling the server

In Fusion: **Preferences → General → API → check "Fusion MCP Server (runs locally on this device)"**. The port is configurable there; the default endpoint is:

```
http://127.0.0.1:27182/mcp
```

Fusion must be *running* for the server to answer — it lives inside the desktop app, not as a daemon.

## The license gate

**Autodesk blocks third-party AI tool integration on a Personal Use license.** Education licenses and commercial subscriptions work. The symptom of the gate is confusing: the preference checkbox exists and the port may even answer, but requests are refused — which looks exactly like a bug in your client. If a probe fails despite Fusion running and the box checked, suspect the license before your code. (Students: an institutional education license clears it.)

## Connecting — protocol details

Transport is **streamable HTTP with JSON-RPC 2.0**. Requirements that will bite if skipped:

- Send `Accept: application/json, text/event-stream` — the server may answer either as plain JSON or as an SSE stream, and rejects clients that don't advertise both.
- If the server returns an `Mcp-Session-Id` header on `initialize`, echo it on every subsequent request.
- Handshake order: `initialize` → `notifications/initialized` → then real calls.

A raw curl handshake (useful for debugging before any client code exists):

```bash
curl -s http://127.0.0.1:27182/mcp \
  -H 'Content-Type: application/json' \
  -H 'Accept: application/json, text/event-stream' \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{
        "protocolVersion":"2025-03-26","capabilities":{},
        "clientInfo":{"name":"curl-probe","version":"0"}}}' -i
# note the Mcp-Session-Id response header, then:
curl -s http://127.0.0.1:27182/mcp \
  -H 'Content-Type: application/json' \
  -H 'Accept: application/json, text/event-stream' \
  -H 'Mcp-Session-Id: <id from above>' \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}'
```

`scripts/probe_fusion_mcp.py` does exactly this with friendly failure messages — run it first whenever Fusion integration misbehaves.

## What the API exposes

The server lists **4 tools**; the workhorse is **`fusion_mcp_execute`**, which runs arbitrary Fusion API Python inside the live application. In practice that one tool is the whole integration — anything the `adsk.core`/`adsk.fusion` API can do, you can do. Verified working:

- **STEP import** via `importManager.importToNewDocument(stepOptions)`. Note: `importToTarget` threw `InternalValidationError` on a nested (multi-component) STEP — import to a *new* document instead and work there.
- **Appearances**: 6 material libraries scriptable — assign appearances to bodies/faces programmatically.
- **Full camera control**: eye, target, up-vector, extents — repeatable framed shots.
- **Local rendering**: `startLocalRender` is a real ray tracer (~5.5 s at 960×540), with resolution, quality and **transparent background** exposed. No cloud-render dependency.

## What it can't do

- **No HDRI or light-rig control.** The Rendering API exposes render settings but not the environment/lighting rig — you get Fusion's stock studio environment and that's that. This is the single reason **Blender wins for final renders**: art-directed lighting (rim-light sweeps, keyframed transitions, custom HDRIs) is simply not reachable through the Fusion API. Use Fusion renders for fast, accurate draft shots of the true CAD; go to `blender-render.md` for anything a customer sees.
- **A STEP imported into Fusion arrives as dumb solids — no feature timeline.** You can move faces, section, measure, mate into assemblies and render it, but you cannot edit the parametric features that created it; those live only in the build123d source. Consequence for the pipeline: keep dimension-critical parts code-first (the STEP is an interchange artifact — see `assemblies-and-exports.md`), and if a *human* needs GUI-editable features on a part, model that part natively in Fusion instead.
- Sessions die with the app; anything long-running must tolerate Fusion restarts.

## When Fusion is the right choice

| Need | Right tool |
|---|---|
| Dimension-critical parametric part, STEP for manufacture | build123d (code-first, versionable) |
| Human designer keeps editing the model in a GUI | **Fusion**, modeled natively |
| Organic surfacing / T-spline forms beyond loft territory | **Fusion** (or Blender if it's render-only) |
| Assembly mates + interference checks on real CAD | **Fusion** |
| Fast draft render of the true geometry, scripted camera | **Fusion** `startLocalRender` |
| Final product imagery, lighting design, animation, frame sequences | Blender |
| Ten-second concept iteration | OpenSCAD |

The pattern that works: **build123d as the source of truth → STEP → Fusion for assembly/inspection/draft renders and any human-in-the-loop surfacing → Blender for the shots.**
