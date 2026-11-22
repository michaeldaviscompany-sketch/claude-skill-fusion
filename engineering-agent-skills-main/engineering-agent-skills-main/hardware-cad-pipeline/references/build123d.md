# build123d — parametric B-rep in plain Python

build123d (and its sibling CadQuery) drives the OCCT B-rep kernel from ordinary Python. Solids have exact analytic surfaces — a cone is a cone, not a prism — so exports are true STEP, fillets are real, and a manufacturer can quote from the file. It is pip-installable with no license, which makes it the right default for dimension-critical parts.

```bash
python3 -m venv .venv     # system pip is often externally-managed on macOS
.venv/bin/pip install build123d trimesh
```

Verified working stack: build123d 0.11.0 (OCCT kernel), trimesh for mesh conversion/GLB.

## Named constants + `clearance` at the top of the file

Structure every part file the same way: a docstring stating the **dimension authority** for each group of numbers, then a parameter block, then geometry that uses only those names. This is what makes a correction cheap — when the printed coupon says the fit is tight, you change one number and re-run.

```python
# ---------------------------------------------------------------- parameters
CLEARANCE = 0.25        # mm print-fit clearance — tune on a printed coupon

# -- measured from reference mesh (see cad/reference/*.md) --
BAY_BORE_D   = 30.00    # lug rotation channel bore
BAY_TIP_D    = 22.06    # tab tip circle
BAY_COLLAR_H = 8.00

# -- standardized 22 mm male conical connector (1:40 taper) --
CONE_LEN     = 16.0
CONE_D_LARGE = 22.10
CONE_D_SMALL = CONE_D_LARGE - CONE_LEN / 40.0   # 1:40 taper ON DIAMETER

# ---------------------------------------------------------------- derived
r_tip = BAY_TIP_D / 2 + CLEARANCE   # as-printed radius, not nominal
```

Three habits worth copying:

- **Derive, don't repeat.** `CONE_D_SMALL` is computed from the taper, so correcting `CONE_D_LARGE` cannot desynchronize the small end.
- **Apply `CLEARANCE` in the derived block**, once, with a comment saying which side of the fit it opens. Scattering `+ 0.25` through the geometry makes the tuning loop unauditable.
- **State the authority per group.** "measured from reference mesh" and "read from the governing standard" are different confidence levels; the next agent must be able to see which numbers may be wrong (see `reference-geometry.md`).

## Building solids — algebra mode

The algebra API composes solids with `+` / `-` and locates them with `Pos`/`Rot`. It reads like the part drawing:

```python
from build123d import (Align, Circle, Cone, Cylinder, Polygon, Pos,
                       export_step, export_stl, extrude, fillet, loft)

body = Cylinder(radius=18, height=20, align=(Align.CENTER, Align.CENTER, Align.MIN))
body -= Cylinder(radius=12.5, height=22,                       # through-bore:
                 align=(Align.CENTER, Align.CENTER, Align.MIN),
                 ) .moved(Pos(0, 0, -1))                       # overshoot 1 mm

# select edges and fillet them — a real fillet, exact in the STEP
top_edges = body.edges().filter_by_position(lambda e: e.center().Z > 19)
body = fillet(top_edges, radius=2.0)
```

Two B-rep-specific habits:

- **Overshoot subtractions** (start 1 mm below, end 1 mm above). Coincident faces make booleans fragile and can leave zero-thickness junk.
- **Fillets last.** They attach to edges of the unfilleted topology; adding features after a fillet often fails or fillets the wrong edge after a parameter change.

For angular features (twist-lock tabs, lugs, keyways), sketch a 2-D wedge polygon and `extrude` it, then pattern by rotation — the same measurement frame (degrees CCW about +Z) you used on the reference mesh, so measured angles drop straight in.

## Worked example: a standardized 22 mm male cone (1:40 taper)

Standardized conical connectors are defined by a taper ratio, not a single diameter. A **1:40 taper on diameter**, for instance, means that over 16 mm of engagement the diameter shrinks by 16/40 = 0.4 mm. Look the governing standard up rather than eyeballing "roughly 22 mm": the taper is what makes the joint seal and hold.

```python
CONE_LEN     = 16.0                              # engagement length
CONE_D_LARGE = 22.10                             # proximal diameter
CONE_D_SMALL = CONE_D_LARGE - CONE_LEN / 40.0    # = 21.70 at the tip
CONE_BORE_D  = 18.0                              # gas bore through it

cone = Cone(bottom_radius=CONE_D_LARGE / 2,
            top_radius=CONE_D_SMALL / 2,
            height=CONE_LEN,
            align=(Align.CENTER, Align.CENTER, Align.MIN))
cone -= Pos(0, 0, -1) * Cylinder(radius=CONE_BORE_D / 2, height=CONE_LEN + 2,
                                 align=(Align.CENTER, Align.CENTER, Align.MIN))
```

In the exported STEP this is an exact conical surface a hose cuff will actually seat on. The same "find the standard, encode the defining relation" move applies to threads (pitch), bearing seats (fit class), and every other commodity interface.

## Export: STEP, STL, and GLB via trimesh

```python
export_step(part, "out/part.step")                      # exact B-rep — the
                                                        # manufacturing artifact
export_stl(part, "out/part.stl",
           tolerance=0.02, angular_tolerance=0.08)      # mm / RADIANS
```

Tessellation tolerances control mesh quality: 0.02 mm linear / 0.08 rad angular is website-render grade; coarser shows facets on camera-close curves, finer bloats files. (More in `assemblies-and-exports.md`.)

**GLB for Blender** goes via trimesh, and the point is to *preserve node names* — the render stage keys materials off them:

```python
import trimesh

def to_mesh(part, name, lin=0.02, ang=0.08):
    tmp = f"out/.{name}.tmp.stl"
    export_stl(part, tmp, tolerance=lin, angular_tolerance=ang)
    m = trimesh.load_mesh(tmp); os.remove(tmp)
    m.process(validate=True); m.merge_vertices()
    return m

scene = trimesh.Scene()
scene.add_geometry(to_mesh(part, "pod_chassis"),
                   node_name="pod_chassis", geom_name="pod_chassis")
scene.export("out/pod_chassis.glb")
```

Set `node_name` *and* `geom_name` explicitly — default names like `geometry_0` destroy the material-assignment contract downstream.

## Common pitfalls

- **GLB units/axes**: glTF is Y-up metres by convention, but this pipeline writes raw Z-up millimetre coordinates; the Blender importer then lays parts on their side at 1000× scale. Either bake a conversion transform into the scene or document the fix the importer applies (`blender-render.md` has the recipe). Don't leave it ambiguous — half the traps in this pipeline are unit/axis traps.
- **Verify the export, not the run.** A script that exits 0 can still write a mirrored, mis-scaled or hollow part. Run `scripts/verify_export.py` with the source constants as the expected values — it cross-sections the actual file (see `verification.md`).
- **Multiple `Solid`s exported as one STL** silently become a multi-body mesh; downstream watertight checks then report per-body results confusingly. Export one part per file, or use a `Compound` deliberately and say so.
- **Boolean failures can be silent** — a subtraction that misses (wrong axis, wrong side of a plane) just leaves the stock material. The cross-section check catches these; eyes on a render catch the rest.
- **Don't fillet across a parameter sweep blindly**: a radius that fits at nominal may exceed a wall at the tolerance extreme. Recompute or guard (`assert fillet_r < wall`).
- **Keep Python as the single source.** If someone "fixes" the STEP in a GUI, the fix evaporates on the next regeneration. The repo's rule: exports are artifacts; only the `.py` is the model.
