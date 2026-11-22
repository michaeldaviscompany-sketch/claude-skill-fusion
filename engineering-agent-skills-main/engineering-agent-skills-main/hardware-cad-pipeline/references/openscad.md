# OpenSCAD — fast parametric concepts, honestly scoped

OpenSCAD is code-driven CSG: you write modules, it booleans primitives into a mesh. Its edit-preview loop is under ten seconds, it is free, fully scriptable, and ideal for the stage where the question is "what should this thing roughly be?" rather than "what exactly is this thing?". Know its limits and hand off before they hurt.

## Install and headless use

```bash
brew install --cask openscad@snapshot   # notarized; snapshot has the fast
                                        # manifold geometry backend
```

Headless CLI:

```bash
openscad -o part.stl part.scad                       # render to mesh
openscad -o preview.png --imgsize=1000,650 \
         --camera=0,0,0,62,0,22,340 \
         --colorscheme=Tomorrow part.scad            # preview PNG
```

`--camera` is either `translate_x,y,z,rot_x,y,z,distance` or `eye_x,y,z,center_x,y,z`; add `--autocenter --viewall` when you'd rather not hand-tune it, and `--preview` to use the fast OpenCSG preview instead of a full render (fine for concept images).

A batch script keeps everything regenerable with one command. Real working pattern:

```bash
#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p stl renders
for f in housing lid bracket coupler; do
  echo "rendering $f ..."
  openscad -o "stl/$f.stl" "$f.scad"
done
openscad --preview --viewall --imgsize=800,900 \
  --camera=-330,410,120,0,20,-35 --colorscheme=Tomorrow \
  -o renders/assembly.png assembly.scad
```

## The central-parameters pattern

Put every dimension in one `parameters.scad` that every part file `include`s. This is what makes the model *parametric* rather than merely scripted — change a tube diameter once and every port, collar and boss follows.

```scad
// parameters.scad — units: millimetres. Edit here; every part includes this.
$fn       = 96;    // curve resolution: drop to ~32 while iterating,
                   // raise to 160 for final renders
wall      = 2.4;   // default wall (FDM 3-4 perimeters)
clearance = 0.25;  // press-fit clearance — tune on a printed coupon,
                   // never by reprinting the whole part

tube_id   = 22;               // ID of the standard tube this port must fit
port_od   = tube_id - 1.0;    // derived, not repeated: taper-fit spigot
port_len  = 18;
```

Derive dimensions from each other (`port_od = tube_id - 1.0`) instead of writing 21 twice — repeated magic numbers are how a parameter change silently breaks a fit. A small worked module:

```scad
include <parameters.scad>

// tube spigot: a wall-thick sleeve with a barb ridge
module tube_spigot() {
    difference() {
        union() {
            cylinder(h = port_len, d = port_od);
            translate([0, 0, port_len - 4])            // barb near the tip
                cylinder(h = 2, d1 = port_od, d2 = port_od + 2*1.2);
        }
        translate([0, 0, -0.5])                        // through-bore; the
            cylinder(h = port_len + 1,                 // 0.5 overshoot avoids
                     d = port_od - 2*wall);            // coincident-face
    }                                                  // z-fighting artifacts
}
```

Note the `-0.5`/`+1` overshoot on the subtracted cylinder: coincident boolean faces produce zero-thickness skins and preview artifacts, so always cut *through* a surface, never exactly *to* it.

## Where OpenSCAD genuinely wins

- **Concept iteration**: a parametric idea on screen in minutes, re-rendered in seconds.
- **Simple mechanical parts and enclosures**: boxes, tubes, flanges, brackets, hole patterns.
- **Batch/CI friendliness**: pure text in, STL/PNG out; trivially diffable and scriptable.
- **Zero cost, zero license friction.**

## Its real limits

- **Mesh-only output.** No STEP, no B-rep. A manufacturer quoting from your STL is quoting a faceted approximation; a Ø22.10 cone is a polygon prism whose "diameter" depends on `$fn`.
- **No proper fillets.** `hull()` and `minkowski()` fake rounding but scale terribly and cannot do a selective edge fillet.
- **Flat-shaded previews only** — fine for engineering communication, unusable as product imagery.
- **No assemblies or mates**; you position parts by hand-maintained transforms.
- **CSG slows down hard** as boolean trees deepen (the snapshot's manifold backend helps but doesn't change the shape of the curve).

## The lesson that cost real time: concept dims are not authority

In real use, dimensions typed into `.scad` files as *rough placeholders* were later read back as engineering values — and one enclosure was specified too small to physically contain its own components (a 60 mm-deep case around a Ø76 mm part). The `.scad` file looked authoritative because it was numeric, parametric and checked in. It wasn't; it was a sketch.

Treat OpenSCAD values as **fallback defaults, not dimension authority**. Measured reference geometry and published standards govern (see `reference-geometry.md`); carry a concept dim forward only where nothing better exists, and label it as such in the file header:

```scad
// bore_d = 70;   // CONCEPT VALUE — real component measures Ø76 OD;
                  // superseded by the measured value in the B-rep source
```

And before detailing any enclosure, do the packing arithmetic in comments right next to the parameters — `case_w = wall + 84 component lane + 40 electronics lane + wall` is one line, and it catches impossible envelopes at typing speed.

## When to graduate to build123d / CadQuery

Move the part to a B-rep kernel (see `build123d.md`) the moment you need any of:

- a **STEP file** — i.e. anything a manufacturer, machinist or another CAD system will consume;
- **real fillets or chamfers** on selected edges;
- **standards-conformant features** — conical connectors (a 1:40 taper on diameter, say), threads, bearing seats;
- dimensions that must survive into **tolerance and fit** work.

Keep the OpenSCAD file around as the fast visual sketchpad; just make sure the header says which file is now the source of truth.
