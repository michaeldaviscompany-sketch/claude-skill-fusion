# Tool selection — which CAD/render tool for which job

The four tools in this pipeline are not interchangeable. Each has a kernel (or lack of one) that makes it excellent at one class of geometry and actively hostile to another. Pick per part, not per project.

## The comparison

| | OpenSCAD | build123d / CadQuery | Fusion 360 (local MCP) | Blender (headless) |
|---|---|---|---|---|
| Kernel | CSG on meshes | OCCT B-rep (true curves/surfaces) | Autodesk B-rep | Polygon mesh |
| Dimensional truth | Parametric but mesh output | Exact — a Ø22.10 cone is Ø22.10 | Exact | None — verts are wherever they are |
| STEP export | No (mesh only) | Yes, true STEP | Yes | No |
| Fillets | No real fillets (hull/minkowski workarounds, slow) | Real edge fillets/chamfers | Real, plus GUI repair | Bevel modifier (cosmetic only) |
| Organic surfaces | Painful | Possible (lofts) but not its strength | Good (T-splines, forms) | Its home turf |
| Rendering | Flat-shaded preview PNGs | None (export and render elsewhere) | Built-in ray tracer (~5.5 s at 960×540) but no HDRI/light-rig control | Full control: Cycles/EEVEE, lights, materials, animation |
| Automation | Full CLI | Plain Python, pip-installable | Python via the MCP's `fusion_mcp_execute` | Full: `blender -b -P script.py` |
| Cost / license | Free | Free | Free for education; **Personal Use license blocks AI/MCP integration** | Free |
| Human GUI editing | Text only | Text only | Yes — the point of it | Yes |

Two failure patterns account for most wasted time in this domain:

- **Engineering geometry in a mesh tool.** Blender will happily let you model a 22 mm connector, but there is no dimension anywhere in the file — only vertices that approximate one. The first time a fit fails you have nothing to adjust but pushed points.
- **Organic surfacing in a CSG kernel.** OpenSCAD can loft a face-seal shape out of hulled ellipsoids, but every iteration is slower and uglier than the last, and it still can't fillet the result.

Split the work instead: dimension-critical parts in a B-rep kernel, cosmetic and soft geometry in Blender, and *import* the engineering parts into the render scene rather than re-modeling them there. See `assemblies-and-exports.md` for the handoff format.

## Install notes (macOS)

```bash
# OpenSCAD — the snapshot build has the faster manifold backend
brew install --cask openscad@snapshot

# Blender — notarized cask, do not bypass Gatekeeper with random builds
brew install --cask blender          # gives `blender` CLI (v5.x)

# build123d + the mesh toolchain
python3 -m venv .venv                # system pip on macOS is often
.venv/bin/pip install build123d trimesh numpy scipy shapely rtree
```

The venv matters: Homebrew/macOS Python is usually *externally managed*, so bare `pip install` fails with `error: externally-managed-environment`. Create a venv once per project and use its interpreter explicitly (`.venv/bin/python script.py`) — that also pins the CAD stack so a system upgrade doesn't silently change your tessellation.

Fusion 360 installs from Autodesk directly; enabling its MCP server is covered in `fusion-mcp.md`.

## Worked examples — "which tool for this part?"

### 1. Tolerance-critical connector (e.g. a twist-lock adapter mating a commercial port)

**build123d.** The part is defined by numbers that must be exact: a Ø30.00 bore, tab tips on a Ø22.06 circle, a standardized cone with a 1:40 taper. You need a real STEP for any manufacturer, a `clearance` parameter to tune from a printed coupon, and geometry that regenerates when a measured dimension is corrected. A mesh kernel can't represent the cone exactly and OpenSCAD can't export STEP. Sketch it first in OpenSCAD if you want a same-hour visual, but treat those dims as placeholders (see `openscad.md`).

### 2. Organic or soft-goods form (a moulded seal, a fabric cover, a strap)

**Blender** for the render-grade version; build123d lofts for a "close-enough" engineering placeholder. Organic and textile forms have no dimensioned features — they have *character*, which comes from sculpting, subdivision surfaces and cloth simulation, none of which exist in a B-rep kernel. Keep one engineering anchor (the sealing footprint, e.g. 105×95 mm) as a hard constraint from the B-rep world and sculpt around it.

### 3. Quick concept enclosure ("roughly 130×86×196, ports on top, does the proportion read right?")

**OpenSCAD.** Ten-second preview loop, one `parameters.scad`, `difference()` of two rounded boxes, done in an afternoon including preview PNGs for a slide. Do the packing arithmetic *before* modeling — add up the component diameters and walls and confirm they fit the envelope (a real project specced a 60 mm-deep enclosure around a Ø76 mm component; one line of arithmetic would have caught it). Graduate to build123d the moment anyone will print or quote the part.

### 4. Photoreal product render / scroll-site frame sequence

**Blender**, importing the engineering parts. Fusion's `startLocalRender` is genuinely useful for fast draft renders of the real CAD (transparent background, scriptable camera), but its Rendering API exposes no HDRI or light-rig control, so you cannot art-direct the shot. Blender gives you three-point rigs, keyframed lights, emission planes, and WebP frame-sequence output. Pipeline: build123d → GLB with named nodes → Blender materials keyed off node names → EEVEE for iteration, Cycles for the finals. See `blender-render.md`.

## Rule of thumb

Ask two questions about the part:

1. **Will a fit fail if a number is wrong?** → B-rep (build123d by default; Fusion if a human needs to keep editing it in a GUI).
2. **Is its job to look right rather than measure right?** → Blender (or OpenSCAD if it just needs to exist by lunchtime).

Keep the parametric source in code with named constants, and treat every exported file as a disposable artifact you can regenerate with one command.
