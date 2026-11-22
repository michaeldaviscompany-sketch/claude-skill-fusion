# Assemblies and exports — one world frame, three formats, named nodes

Multi-part products die by transform bookkeeping: each part modeled in its own convenient frame, then a growing pile of hand-maintained offsets to place them together, which drift apart the first time a part changes. The pattern here avoids that, and defines what each export format is *for*.

## One world frame, parts built in place

Declare a single world frame in one shared module, and **build every part already positioned in it**:

```python
# common.py — the single source of truth for frames and shared dims
# WORLD FRAME: X = wearer's left->right, Y = forward, Z = up.
# Origin = geometric centre of the main body.
# All parts are BUILT in world position; per-part exports are re-centred
# on the part's bbox centre by the exporter.
POD_W, POD_D, POD_H = 130.0, 86.0, 196.0
PORT_X, PORT_Y = 26.0, -10.0
...
```

Why build-in-place instead of model-at-origin-then-place: mating features are shared *numbers*, not shared transforms. The tube cuff and the housing port both read `PORT_X` from `common.py`; there is no separate placement step to get stale. Direction helpers (`def port_dir(side): ...`) live in the same module so angled interfaces are computed once.

The exporter then produces both views cheaply:

- **Per-part files, re-centred** on each part's bounding-box centre — so a part opened alone sits at the origin (what a slicer or a part-level render wants).
- **Assembly files with the world placement restored** as each node's transform — so Blender receives per-part origins *and* correct relative placement.

## What each format is for

| Format | Role | Notes |
|---|---|---|
| **STEP** | The manufacturing/interchange artifact | Exact B-rep. What machinists, molders and other CAD systems consume. Not a source — regenerate it, never hand-edit it. |
| **STL** | Printing and mesh analysis | Tessellated once, at declared tolerances. Input to slicers and to `scripts/measure_mesh.py` / `verify_export.py`. |
| **GLB** | The render/web handoff | A *scene*: named nodes + transforms. The names are load-bearing (materials key off them downstream). |

Declare tessellation quality as named constants, once:

```python
LIN_TOL, ANG_TOL = 0.02, 0.08   # mm / RADIANS — website-render grade
export_stl(part, path, tolerance=LIN_TOL, angular_tolerance=ANG_TOL)
```

The angular tolerance is **radians** — a value that would be sensible in degrees (e.g. 0.5) silently produces a coarse, faceted mesh.

A B-rep and a mesh can also legitimately *differ*: a corrugated hose that would be thousands of B-rep surfaces can ship as a smooth swept tube in STEP (the engineering intent) and a full corrugated mesh in STL/GLB (the visual truth). That's a feature, not a fudge — but write it down in the manifest so nobody "fixes" the mismatch.

## Building the GLB with named nodes

Tessellate each part (via a temp STL round-trip — robust across build123d versions), then add it to a `trimesh.Scene` with explicit names:

```python
import trimesh

sc = trimesh.Scene()
for name, part in parts.items():          # e.g. "pod_chassis", "faceplate_sport"
    m = tessellate(part)                  # export_stl -> trimesh.load -> process
    m.apply_translation(-part_center)     # per-part origin at its own centre
    sc.add_geometry(m, node_name=name, geom_name=name,
                    transform=world_placement(name))   # assembly variant only
sc.export("out/assembly.glb")
```

Name nodes with **role prefixes** (`pod_`, `hose_`, `faceplate_`) — that's the contract the render stage's role→material map depends on (`blender-render.md`). Never let trimesh auto-name (`geometry_0`); an auto-named node renders default-grey and fails silently.

For product *variants* (colorways × configurations), export one assembly GLB per configuration from the same part set — six variant files from one build run costs seconds and saves the render stage from doing CAD-side logic.

**Units/axes:** glTF convention is Y-up metres; trimesh writes your coordinates raw (Z-up mm in this pipeline). Either bake the conversion into the scene transform at export, or document the importer-side fix — one of the two, explicitly (`blender-render.md` has the import recipe; the trap is in `verification.md`'s catalogue).

## The manifest

Have the exporter emit a `MANIFEST.md`: one row per part — dims, triangle count, files, watertight flag, and a **dimension-authority note** ("engineering: Ø76 canister" vs "render-only styling"). It costs ten lines of code and gives you:

- a diffable regression record (a part whose dims change unexpectedly is visible in review);
- the engineering/render-only distinction preserved *at the artifact*, where the next consumer will actually look;
- a checklist for `verify_export.py` specs.

## Regeneration is one command

The whole tree — parts, assemblies, manifest — regenerates from `python master_assembly.py`. If regenerating requires remembering a sequence of steps, steps get skipped and exports drift out of sync with the source. One command, idempotent, safe to run after every model change; then run the verification pass (`verification.md`) on what it produced.
