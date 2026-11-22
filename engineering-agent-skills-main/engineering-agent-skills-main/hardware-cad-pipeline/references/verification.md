# Verification — check the artifact, not the claim

The recurring failure in CAD pipelines is not "the script crashed"; it is "the script exited 0 and the file is wrong." Exporters don't validate intent: a mirrored part, a boolean that silently missed, a unit mix-up — all export cleanly. So after every export, and before anything downstream consumes it, verify the *file*. A previous step's success report is not evidence; the report is not the artifact.

## The checklist

Run this on every exported mesh (in order — later checks assume earlier ones):

1. **It loads, and contains geometry.** Zero-byte and empty-scene exports happen.
2. **Watertight / manifold, consistent winding, no self-intersections.** Non-watertight meshes break slicers, boolean ops, and volume math downstream. `scripts/verify_export.py` checks this first.
3. **Body count is what you intended.** One part = one body. Extra bodies mean stray construction geometry or a boolean that split; the count is one line (`trimesh.load(f).body_count`) and stray bodies are invisible in most viewers.
4. **Dimensions match the source constants.** Cross-section the *exported* mesh and confirm named features measure what the parameter block says — bounding box, bore radii, feature circles. This is the check that catches unit errors, mirrored parts and silent boolean failures. Encode it as a spec file so it reruns for free:

   ```json
   { "watertight": true,
     "checks": {
       "collar OD":  {"kind": "bbox_x", "expect": 36.0, "tol": 0.3},
       "bore r":     {"kind": "profile_rmedian", "z": 5.0, "expect": 15.0, "tol": 0.15},
       "tab tips r": {"kind": "profile_rmin",    "z": 5.0, "expect": 11.03, "tol": 0.15}
     } }
   ```

   `scripts/verify_export.py mesh.stl spec.json` → per-check PASS/FAIL, exit code 1 on any failure — CI-able.
5. **Scale and orientation**, especially across format boundaries (STEP→STL→GLB→Blender). Extents of ~0.08 m where you expected 80 mm, or a Z height where you expected Y, is the glTF units/axes trap (`blender-render.md`).
6. **Count and place the objects.** For assemblies: number of nodes, node *names* (the material contract), and rough positions — a bounding-box dump per node is enough.
7. **Look at it.** One render or viewer screenshot catches the class of error no numeric check anticipates: features on the wrong side, a part inside another, an obviously wrong proportion. Thirty seconds of eyes is the cheapest check on this list.

For assemblies, keep a generated `MANIFEST.md` (part → dims → triangle count → watertight flag) as a standing diffable record — a part whose dims change unexpectedly between runs is a regression you can see in review.

## Failure-mode catalogue

Symptom → likely cause → the check that catches it:

| Symptom | Likely cause | Caught by |
|---|---|---|
| Part is 1000× too big/small downstream | mm vs m across a format boundary | #5, or the first import into Blender |
| Part lies on its side | Z-up data in a Y-up format (glTF) | #5 |
| Fit fails although dims "were right" | clearance never applied, or applied twice; or community-reference offsets | #4 with *as-printed* expectations; printed coupon (`prototyping.md`) |
| Feature missing but export "worked" | boolean silently missed (wrong axis/side) | #4 cross-section; #7 |
| Feature on the wrong side / part mirrored | sign error in a transform | #4 (asymmetric feature check) + #7 |
| Slicer/boolean chokes on the mesh | not watertight, degenerate faces | #2 |
| Two overlapping copies of geometry | duplicated export call; Blender append pulling parent dependencies | #3, #6 |
| Volume/mass wildly off | internal void, or multi-body counted as one | #2 + #3 (volume needs watertight) |
| Renders show flickering surfaces | coincident faces z-fighting | #7 (visible in any render) |
| Blank/black renders | camera below the floor plane | check camera vs scene bounds *before* debugging materials |
| Materials all default grey | node names lost in export | #6 name check |
| STEP opens as one dumb lump | multi-solid exported without structure; or that's just what STEP import is (no feature tree) | #6; expectation-setting in `fusion-mcp.md` |
| Model "fixed" yesterday is broken today | someone edited an export instead of the source | regenerate-from-source rule (`engineering-practice.md`) |

## The discipline

Three rules that make verification stick rather than being skipped under deadline:

- **Verify at the boundary.** Each pipeline stage (model → export → import → render) verifies its *input* cheaply and its *output* thoroughly. Errors caught one stage late cost 10× to localize.
- **Automate the numeric checks; reserve human attention for the visual one.** A spec JSON per part costs five minutes once and runs forever; use the human minutes for check #7.
- **When a check fails, distrust the measurement second.** First rerun with a verified axis center / height; *then* suspect the geometry. But when two measurements disagree with each other, you have zero measurements — re-measure (see the contradiction check in `reference-geometry.md`).
