---
name: hardware-cad-pipeline
description: Takes a physical part from concept to dimensionally-correct parametric CAD, verified exports (STEP/STL/GLB), and photoreal renders. Covers tool selection (OpenSCAD for concept CSG, build123d/CadQuery for precise B-rep, Fusion 360 via its local MCP, Blender headless for organic forms, materials, and animation), dimensioning from measured reference geometry and published standards, print-fit tolerances and test coupons, and artifact verification (watertight meshes, dimensions matching their parameters). Use this skill whenever the user wants to model, design, or dimension a physical part; produce an STL, STEP, or GLB; render or animate a product; connect to Fusion 360; write OpenSCAD, build123d, or CadQuery code; measure a reference mesh; or prepare something for 3D printing or prototyping — even if they never name a CAD tool. Do NOT use for 2D graphics, game-asset sculpting, or data visualization.
license: PolyForm-Noncommercial-1.0.0
---

# Hardware CAD & Render Pipeline

Take a physical part from idea → dimensionally-correct parametric CAD → verified exports → photoreal renders, choosing the right tool at each stage instead of forcing one tool to do everything.

The failures in this domain are rarely "the code didn't run." They're "the code ran, produced a beautiful file, and the part doesn't fit / the mesh has three copies of the body / the dimensions were invented." So the through-line of this skill is: **establish what governs your dimensions, then verify the artifact you actually produced.**

## Where to look

| If you're… | Read |
|---|---|
| Choosing a tool for a part | `references/tool-selection.md` |
| Writing parametric CAD code | `references/build123d.md`, `references/openscad.md` |
| Deciding tolerances, fits, failure modes | `references/engineering-practice.md` |
| Making sure it can actually be manufactured | `references/dfm.md` |
| Measuring a real part or reference model | `references/reference-geometry.md` |
| Exporting an assembly for downstream use | `references/assemblies-and-exports.md` |
| Rendering, materials, or frame sequences | `references/blender-render.md` |
| Driving Fusion 360 programmatically | `references/fusion-mcp.md` |
| Printing, coupons, materials, sourcing | `references/prototyping.md` |
| Checking your output is actually correct | `references/verification.md` |

## Establish dimension authority before modeling

Every dimension in a model comes from somewhere. Rank the sources, record which one governs each feature, and never let a lower source silently override a higher one:

1. **Physical measurement of the real part** — calipers, pin gauges, thread gauges, on the actual object the design must mate with. Nothing outranks reality. Take three readings, not one.
2. **Published standards** — look up the actual standard (ISO cone tapers, thread pitches, bearing seats, fit classes) rather than eyeballing a diameter. Standards are what the manufacturer built to.
3. **Vendor CAD** — a STEP file from the part's manufacturer. Authoritative for shape, still worth spot-checking against the datasheet.
4. **Community reference models** — a downloaded STL/STEP from a sharing site. Useful for understanding *shape and topology*, unreliable for dimensions (below). Measure with `scripts/measure_mesh.py`, then treat the numbers as hypotheses.
5. **Your own concept values** — the weakest source. Fine as placeholders, never as authority.

Two things that will bite you if you skip this:

- **Community 3D models bake in the author's print compensation.** A downloaded STL of a standard interface may be 0.3 mm off in every direction because it was tuned for one person's printer. Use it to understand the *shape*, then confirm critical fits against a standard, a real part, or a printed test coupon before committing.
- **Measurements that contradict each other are measurements you don't have.** If a "male" feature's tip circle is smaller than the bore it supposedly enters, one of the numbers is wrong — re-measure before building on it. Cross-check by taking cross-sections at several heights, not one.

Record the authority for each dimension in a short dimensions document in the *project* (e.g. `docs/dimensions.md`), noting for each value: where it came from, its rank above, and whether it still needs physical verification. Six weeks later, nobody — human or agent — can tell a measured value from an invented one by looking at the code.

## Model only what's yours

Before modeling a part, check whether a standard one already exists. Hoses, fasteners, valves, bearings, and connectors are solved problems with published dimensions, certified materials, and supply chains. Modeling them yourself costs time and buys nothing. Spend the effort on the part that is genuinely your design — usually the adapter or interface between commodity parts — and let standards define where they meet.

When you do pull in reference geometry, **check its licence before it touches your design**. Community models are frequently CC BY-NC (non-commercial): you may study and measure such a model, but a part derived from its geometry cannot ship commercially. Measure it, record the dimensions and their provenance, then model your part clean from those dimensions and the published standard.

## Choose the tool, don't default to one

| Tool | Strongest at | Reach for it when |
|---|---|---|
| **OpenSCAD** | Fast parametric CSG, flat concept renders | Sketching a concept, simple mechanical parts, when a preview PNG in 10 seconds beats a perfect surface |
| **build123d / CadQuery** | Precise parametric B-rep (OCCT kernel) | Real STEP export, true conical/filleted surfaces, dimension-critical parts, anything you'll manufacture. Pip-installable, no license, fully scriptable — usually the right default for engineering parts |
| **Fusion 360** (via local MCP) | Surfacing, assemblies, native rendering, GUI editing | Organic/cosmetic surfaces, assembly mates, when a human wants to keep editing it. See `references/fusion-mcp.md` — note the license gate |
| **Blender** (headless) | Organic forms, soft goods, materials, lighting, animation, photoreal | Fabric, skin, characters, product renders, frame sequences for the web. Terrible for engineering dimensions — never model a tolerance-critical fit here |

The common mistake is doing engineering geometry in a mesh tool (no real dimensions) or organic surfacing in a CSG kernel (fights you the whole way). Split the work: **engineering parts in a B-rep kernel, cosmetic and soft geometry in Blender, and import the engineering parts into the render scene** rather than re-modeling them.

Keep the parametric source as the source of truth, in code, with named constants at the top and a `clearance` parameter for print fits. Regenerating everything should be one command. A STEP file is an output, not a source.

## Engineering practice that prevents rework

**Start from requirements and constraints, not geometry.** Write down what the part must do, what it mates with, what loads and environment it sees, and how it will be made — before opening a modeler. Geometry drawn before the constraints are known is usually geometry drawn twice.

**Pick the manufacturing process early, because the process constrains the shape.** A part designed without a process in mind is rarely makeable by any of them. Draft angles and uniform walls for moulding; internal corner radii no smaller than the cutter for machining; overhang limits and layer-direction weakness for FDM; drain holes and post-cure shrinkage for resin. See `references/dfm.md`.

**Model for design intent.** The test of a parametric model is whether it survives a parameter change. Derive dimensions from each other rather than repeating magic numbers (`bore = shaft + clearance`, not two independent constants that silently drift apart). Build from a coherent origin and datum planes rather than off arbitrary faces. Add fillets last — they are the first thing to break a boolean, and the first thing to make a change fail.

**Think in tolerance chains, not nominal dimensions.** Parts are never nominal. Sum the worst-case tolerances along any chain that controls a critical fit, and design so that a *single* dimension governs each fit rather than a stack of five. Tighten only what function demands — every extra tolerance band costs real money at manufacture, and most dimensions do not need one.

**Design the failure mode deliberately.** Ask how the part or system fails, and arrange for the failure to be the safe one. Something will eventually break, jam, drift, or lose power; whether that is an inconvenience or a disaster is a design decision made now, not an accident discovered later. Record the failure modes you considered alongside the model.

**Sanity-check magnitudes and units.** Before trusting a number, check it against a rough independent estimate — order-of-magnitude errors and millimetre-versus-metre confusion are the most common serious mistakes in this domain, and both are invisible in a render. Cross-check any measurement that a design depends on.

## Workflow

1. **Establish dimension authority** (above). If a mating part exists, measure it first with `scripts/measure_mesh.py`.
2. **Sanity-check the packing before detailing.** Do the contents fit inside the enclosure? Add up the diameters and wall thicknesses. It is genuinely common for a specified envelope to be physically unable to contain the components it specifies — catch that in arithmetic, not after a day of modeling.
3. **Model parametrically** with named constants; build the engineering parts in build123d/CadQuery.
4. **Verify the exports** (below) before anything downstream consumes them.
5. **Render** — import engineering parts into Blender, build cosmetic/soft geometry there, apply materials by node-name role so colorways swap cleanly. See `references/blender-render.md`.
6. **Prototype the risk, not the product** — build the smallest thing that answers the biggest unknown. Print a test coupon of the critical fit before printing the whole part; tune `clearance` from the coupon. Change one variable at a time and keep a short test log, or you will learn nothing from three simultaneous changes.

When renders feed something downstream (a website, a deck), agree an **asset contract** first: fixed output directories and zero-padded filenames (`turntable/frame_0001.webp` … plus a `poster.webp`). Build the consumer against watermarked placeholders, and the real renders drop in later with no code changes. This decouples slow rendering from fast iteration on everything else.

If one process is regenerating exports while another reads them, don't overwrite in place — leave a re-export flag file and let the reader finish. Silent partial writes are miserable to debug.

## Verify the artifact, not the claim

A model that exports without error can still be wrong in ways that only show up later — or in front of a customer. After every export, check:

- **Watertight / manifold**, no self-intersections (`scripts/verify_export.py`).
- **Dimensions match parameters.** Take cross-sections of the *exported* mesh and confirm the features measure what the constants say. This catches unit errors, mirrored parts, and silent boolean failures.
- **Component count and placement.** Look at a render or a bounding-box dump. Stray or duplicated geometry is common and invisible in code.
- **Scale and orientation.** Especially across format boundaries.

Do this even when a previous step reported success — the report is not the artifact. Open the file, measure it, look at it.

## Traps that cost real time

These are specific, recurring, and hard to diagnose from the symptom:

- **glTF/GLB orientation and units.** Exporters may write raw Z-up millimetre data; Blender's importer then lays the model on its side at 1000× scale. Either export properly Y-up/metres, or apply a documented fix — but don't leave it ambiguous.
- **Appending an object in Blender drags its dependencies.** Appending, say, two eye meshes can pull their parent body in with them. Symptom: mysterious duplicated geometry poking through the model. Always dedupe and count objects after an append.
- **A camera below the floor plane renders empty frames.** If a render comes back black or blank, check the camera's position relative to scene geometry before debugging materials.
- **Coincident faces z-fight.** Offset by a hair, or boolean them properly.
- **Mesh cross-sections from sparse polylines are noisy.** Sample many angles and use proximity/ray queries rather than trusting a handful of boundary vertices.

## A minimal end-to-end

Enough to see the shape of it. Model in a B-rep kernel, export, then verify the export rather than trusting it:

```python
# part.py — one source of truth; every dimension named, fits derived not repeated
from build123d import *

SHAFT_D   = 12.0          # measured on the real shaft (calipers, 3 readings)
CLEARANCE = 0.25          # tuned on a printed coupon, not guessed
BORE_D    = SHAFT_D + CLEARANCE   # derived — cannot silently drift
WALL      = 2.4

with BuildPart() as bushing:
    Cylinder(radius=(BORE_D + 2 * WALL) / 2, height=20)
    Cylinder(radius=BORE_D / 2, height=20, mode=Mode.SUBTRACT)
    fillet(bushing.edges().filter_by(GeomType.CIRCLE), radius=0.8)  # fillets last

export_step(bushing.part, "out/bushing.step")
export_stl(bushing.part,  "out/bushing.stl")
```

```bash
# Verify the artifact you produced, not the code that produced it
python scripts/verify_export.py out/bushing.stl --expect bore_d=12.25 --tol 0.05
```

If the bore measures 12.0 rather than 12.25, a boolean silently failed or a unit slipped — and no amount of reading the source would have told you.

## Templates

Copy these into the project and fill them in — they exist so the discipline survives contact with a deadline:

- `assets/requirements.md` — requirements capture + the critical-dimension provenance table (fill before opening a modeler)
- `assets/test-log.md` — one-variable-at-a-time iteration log + coupon record
- `assets/fmea.md` — lightweight failure-mode table + fail-safe review questions

## Scripts

**Execute these; don't read them into context.** They need `trimesh` and `numpy`
(`pip install trimesh numpy`, inside a venv if system pip is externally managed).
Each takes `--help`.

- `scripts/measure_mesh.py` — bounding box, watertight check, cross-sections at chosen heights, angular feature extraction (lugs, keyways, bores)
- `scripts/verify_export.py` — confirms an exported mesh is watertight and that named features measure what the source constants claim
- `scripts/probe_fusion_mcp.py` — JSON-RPC probe of a local Fusion 360 MCP server; reports the tools it exposes

## License

Free for individuals and noncommercial use under PolyForm Noncommercial 1.0.0.
Commercial use requires a paid license — see the repository's `LICENSE.md` and `COMMERCIAL.md`.
