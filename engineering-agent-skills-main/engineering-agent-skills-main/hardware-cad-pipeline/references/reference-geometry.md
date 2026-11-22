# Reference geometry — establishing dimension authority

Every dimension in a model comes from somewhere, and most fit failures trace back to trusting the wrong somewhere. This file covers ranking your sources, measuring real meshes without fooling yourself, catching contradictory numbers before they cost a build, and writing it all down so the next agent doesn't re-trust a placeholder.

## The authority ladder

Rank sources and record which one governs each feature:

1. **Measured reference geometry** — a scan/STEP/STL of the actual mating part, measured by you with `scripts/measure_mesh.py`.
2. **Published standards** — the actual standard document. A standardized conical connector may specify a 1:40 taper on diameter; that number is not guessable from "it's about 22 mm". Thread pitches, bearing fits, connector tapers: look them up.
3. **Physical measurement** with calipers on the real object.
4. **Your own concept values** — the weakest source. Fine as placeholders; never as authority.

Why the ladder matters: sources *look* equally authoritative once they're numbers in a file. A `.scad` concept value and a measured bore read identically as `30.0`. The only defence is labeling at the point of definition (see "Documenting dims" below).

**Community 3D models carry an asterisk.** A downloaded STL of a standard interface may be 0.2–0.4 mm off in every direction — the author baked in *their printer's* compensation. Use community models to understand the shape and topology; verify every critical fit on a printed test coupon before committing (see `prototyping.md`).

## Measuring meshes robustly

Two habits separate a real measurement from a plausible-looking guess:

**Sample densely with rays, not sparsely with polylines.** A cross-section of a mesh yields a polyline whose vertices land wherever the tessellation happened to put them; reading "the bore radius" off a handful of boundary vertices is noise. Instead, cast many rays (hundreds) outward from the part axis at a given height and record first-hit distances. Plateaus in the radius-vs-angle curve are real features; their angular extents give you lug/keyway widths and centers directly. `scripts/measure_mesh.py --profile <z>` does this (720 rays = 0.5° resolution by default) and reports contiguous inner runs (tabs/ribs/lugs) and outer runs (keyways/slots).

**Section at several heights, not one.** Features live at different Z: a twist-lock receptacle read at only one height shows either the retaining ledges or the clear entry channel, never both, and you'll misclassify the interface. A real measuring session looks like:

```bash
scripts/measure_mesh.py ref.stl                          # bbox, watertight, bodies
scripts/measure_mesh.py ref.stl --sections 0.5,2,5,8 --axis-center 0,0
scripts/measure_mesh.py ref.stl --profile 0.5,2,5,8 --axis-center 0,0
```

Pin `--axis-center` to the true part axis (not the bbox center) when the part has asymmetric flanges — a 0.3 mm off-axis center smears every radius by that much.

Worked example of what this finds (a real twist-lock receptacle STL): at z=5 the profile shows a Ø30.0 channel with three ~10°-wide ribs whose tips sit on Ø22.05, at 120° spacing; at z=0.5 it shows a Ø27.8 entry opening with three ~38° keyway gaps. Those five numbers — bore, tip circle, entry opening, feature widths, spacing — *are* the interface definition, extracted in two commands.

## The contradiction check

**Measurements that contradict each other are measurements you don't have.** Before building on a set of numbers, check them against each other and against the physics of the mechanism:

- A *male* feature's tip circle smaller than the bore it supposedly enters → at least one number (or the male/female interpretation) is wrong. In the real case behind this rule, "male lugs on Ø22.1 with a Ø30 bore" resolved, on re-measurement, into a *female* receptacle: a Ø30 bore with inward tabs stopping at Ø22.06. Same numbers, opposite part.
- Feature counts and spacings should close: three keyways at "123°/120°/117°" that re-measure as 119.9°/120.0°/120.1° means the asymmetry was measurement noise — and if the real part *is* keyed asymmetrically, your reference doesn't capture it. Note that as an open question for the coupon.
- Sums should close: bore + 2×wall should equal the measured OD; stack-ups should equal overall height.

When a contradiction appears, **re-measure before modeling** — at more heights, more angles, with the axis center verified. An hour of re-measurement is cheaper than a printed part that locks onto nothing.

## Documenting dims — the `dims.md` pattern

Keep a short markdown file next to the reference mesh recording what was measured, how, and what it does *not* establish. Skeleton that has worked:

```markdown
# <part> — measured mating dimensions (re-measured YYYY-MM-DD)

Measured from `<file>` using ray-cast angular profiles at z = ... about the
part axis. **These are dimensions of a community model, not an official
drawing** — verify on a printed coupon before committing geometry.

## Corrections vs earlier drafts
<what changed on re-measurement and why — keep the audit trail>

## The load-bearing numbers
| Feature | Value | Notes |
|---|---|---|
| Channel bore | Ø30.0 | clear rotation channel, z 1–8 |
| ...

## Verification required before use
1. Printed coupon must confirm <fit, engagement, seating depth>.
2. <open questions the reference cannot answer, e.g. asymmetric keying>
3. Treat every number as nominal ± model error; tune `clearance` per printer.
```

The three parts that earn their keep: the **provenance sentence** (what governs, what doesn't), the **corrections section** (so a future re-measurement knows what was already caught), and the **verification list** (so nobody mistakes "measured" for "confirmed"). The model file's parameter block should then cite this file by path — dimension, authority, and caveat all one hop apart.

## Feeding it into the model

In the parametric source, group constants by authority with the citation in the comment:

```python
# -- measured from cad/reference/<part>_dims.md (community mesh; coupon-verify) --
BAY_BORE_D = 30.00
BAY_TIP_D  = 22.06
# -- from the governing standard --
CONE_D_LARGE = 22.10
CONE_D_SMALL = CONE_D_LARGE - 16.0 / 40.0
```

And when a measured value is corrected, change it in exactly one place and regenerate — which is the whole argument for keeping the model in code (`build123d.md`).
