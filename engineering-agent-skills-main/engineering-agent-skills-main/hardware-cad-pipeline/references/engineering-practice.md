# Engineering practice — the discipline that prevents rework

You already know the theory (fits, GD&T, FMEA — it's in your weights; look up *specific
standard values* rather than trusting recall of numbers). What follows is the discipline
that agents actually skip, why each practice exists, and what skipping it costs.

## Requirements before geometry

Geometry drawn before the constraints are known is usually geometry drawn twice. The
requirement is not "an enclosure"; it is "a housing that holds these five components,
mates with this hose standard, survives being sat on, and can be printed on the machine
you own." Write it down first — one screen is enough, zero screens is a guarantee of rework:

```
PART: <name>
FUNCTION:      what it must do (verbs, not shapes)
MATES WITH:    each interface + its dimension authority (measured / standard / vendor CAD)
LOADS:         forces, pressures, drop/crush cases — rough numbers, not adjectives
ENVIRONMENT:   temperature, moisture, skin/gas contact (→ prototyping.md constraints), UV
PROCESS:       how it will be made, now and at volume (→ dfm.md — process constrains shape)
LIFETIME:      cycles, hours, disposable vs serviceable
FAILURE MODE:  what happens when it breaks/jams/loses power — chosen, not discovered
DON'T-CARES:   what explicitly does NOT matter (frees the design as much as the rest constrains it)
```

Fill it in with real numbers where you have them and labeled placeholders where you don't.
A placeholder that says "GUESS — verify" is honest; a confident-looking invented number is
a trap for the next agent (see provenance, below).

## Design intent in parametric models

A parametric model is a claim about *which relationships matter*. The test is whether it
survives a parameter change — change a governing dimension by 20% and rebuild. If the
rebuild fails or produces nonsense, the model encodes accidents, not intent.

- **Derive, don't repeat.** `bore = shaft + clearance`, never two independent constants
  that agree today and drift apart at the first correction. Every repeated magic number is
  a latent contradiction waiting for an edit.
- **Fully constrain sketches.** An under-constrained sketch has degrees of freedom the
  solver will exercise at the worst moment — a parameter change "succeeds" and a line
  quietly swings to a new position. In GUI CAD, drag-test the sketch; in code CAD, the
  equivalent is deriving every coordinate from named parameters, never from a literal that
  "happened to line up."
- **A coherent datum scheme.** Build from a deliberate origin and reference planes — ideally
  the same features you'd measure from and manufacture from. Models built off whatever face
  was handy shatter on parameter changes, because the "reference" moves with the thing it
  was supposed to locate.
- **Fillets and chamfers last.** They are the most fragile features in any kernel: the first
  thing to break a boolean, and the first thing to fail when an edge they referenced
  disappears in a rebuild. Model the functional solid, verify it, then dress the edges.

## Tolerances and fits

Parts are never nominal. A drawing says 10.00 mm; the parts that arrive are 9.97, 10.02,
10.04. Design for the population, not the ideal.

### Worked worst-case stack-up

Three components stack inside a pocket; a lid must still close over them:

```
pocket depth      17.50 ± 0.15
component A       10.00 ± 0.20
component B        5.00 ± 0.10
component C        2.00 ± 0.10
--------------------------------
worst-case gap = (17.50 − 0.15) − (10.20 + 5.10 + 2.10)
              = 17.35 − 17.40 = −0.05 mm   ← interference: some assemblies won't close
best-case gap = (17.50 + 0.15) − (9.80 + 4.90 + 1.90) = +1.05 mm  ← rattle at the other end
```

Nominally there is 0.5 mm of room; at worst case the lid jams. This failure is invisible
in CAD, where every part is nominal — it is caught by summing the chain *now*, or by the
first production batch. If worst-case says interference, either open the nominal gap,
tighten the tolerances that dominate the sum (here the ±0.20), or add a compliant element
(foam, spring, gasket) that absorbs the whole band.

**Let a single dimension govern each critical fit.** A fit controlled by one dimension has
one tolerance band; a fit at the end of a five-part chain has the sum of five. Arrange
datums and mating features so critical clearances are set by one machined/printed surface
pair, and let the sloppy chain accumulate somewhere a gasket can absorb it.

### Fit classes (ISO 286)

Fits come in three families: **clearance** (always a gap — shafts turn or slide),
**transition** (may be slight gap or slight squeeze — locates accurately, light press),
**interference** (always a squeeze — transmits torque without a key, needs a press or heat).
The hole-basis shorthand (H-hole + lettered shaft) covers nearly everything:

| Fit | Type | Use it for |
|---|---|---|
| H11/c11 | loose clearance | dirty/thermal environments, non-critical pivots |
| H9/d9 | free running | high-speed or long bearings, generous film |
| H8/f7 | close running | ordinary rotating shafts in bushings |
| H7/g6 | sliding | precise slide/locate, spigots, moves without shake |
| H7/h6 | locational clearance | parts that assemble by hand and locate precisely |
| H7/k6 | transition | keyed pulleys/gears — accurate location, light tap to fit |
| H7/p6 | interference | press-fit bushings, bearing seats, torque without fasteners |

Worked example at Ø10: H7 hole = 10.000/+0.015 mm; g6 shaft = −0.005/−0.014 mm. Clearance
ranges from 5 µm (tightest) to 29 µm (loosest) — always positive, never rattly. Look up the
band for your actual diameter (deviations grow with size); do not reuse Ø10 numbers at Ø40.

**Every tightening costs real money.** ±0.1 mm is what processes give you for free;
±0.025 mm means better tooling, slower feeds, and inspection; ±0.01 mm means grinding and
gauges. Cost roughly doubles per band tightened. Tolerance only what function demands and
leave everything else at a stated general tolerance (e.g. ISO 2768-m). A drawing where
every dimension is tight is a drawing nobody costed. (FDM can't hold ISO fit bands at all —
there the "fit class" is a `clearance` parameter tuned on a coupon; see `prototyping.md`.)

## GD&T — the practical minimum

Full GD&T is a language; you need about four words of it. Its point: ± tolerances on
coordinates can't say "this hole must line up with that boss when both parts are at their
worst" — geometric controls can, and they name the *reference* (datum) explicitly.

- **Datums** — pick A/B/C as the surfaces the part actually mounts and locates from, and
  make them the same surfaces the model's datum scheme uses. Measurement, manufacture,
  and model should agree on where zero is.
- **Flatness** on a sealing or mounting face — "flat within 0.1" is checkable; "make it
  flat" is not. Seals care about flatness, not the face's position.
- **Perpendicularity** where a bore or wall must be square to a datum — a bore can be
  perfectly sized and still bind because it leans.
- **Position** (usually with Ⓜ, maximum material condition) for hole patterns — it
  tolerances the pattern as a pattern and legally trades unused size tolerance for
  position tolerance, which is exactly how mating parts behave.

That is enough to specify what matters on most parts. If you find yourself reaching for
profile-of-a-surface or composite frames, that's a sign to consult a real machinist or
the standard (ASME Y14.5 / ISO 1101), not recall.

## Failure-mode thinking

Something will eventually break, jam, drift, clog, or lose power. Whether that is an
inconvenience or a disaster is a design decision made now. The lightweight loop — a few
rows in a table, not a 40-page FMEA — per part or subsystem:

1. **How can it fail?** (fracture, leak, jam, sensor drift, power loss, wrong assembly)
2. **How likely?** (rough: often / sometimes / rare)
3. **How bad?** (annoyance / part scrapped / person hurt)
4. **Would anyone notice before it matters?** (drift and clogging are dangerous precisely
   because they're silent — see the plausibility-trip pattern below)
5. **What's the mitigation?** — and write it into the requirements, not the margin.

Two standing rules:

- **Fail safe / fail open.** Design so the *unpowered, broken, or stuck* state is the safe
  one: a valve that springs open when power is lost, a clamp that releases, a heater that
  can't latch on. Detection matters as much as response — a system whose sensors can all
  drift the same direction needs an independent plausibility check, because redundancy
  doesn't help against a common-mode error.
- **For anything that can injure a person, the safe failure mode is a requirement**, not a
  feature to trade away — including for a one-off prototype tested only on yourself. The
  prototype is exactly when the untested failure happens.

Safety factors cover what analysis doesn't: material scatter, load uncertainty, printing
defects. Typical: 1.5–2 for well-characterized static loads, 3–4 where loads are guessed
or the material is a printed polymer with layer-adhesion lottery, more where failure hurts
someone. A safety factor is not permission to skip the stack-up or the FMEA — it covers
*unknown* variation, not known arithmetic you declined to do.

## Units and magnitude discipline

The most common serious errors in this domain are not subtle: they are 10×, 25.4×, and
1000× errors, and they are invisible in a render because renders have no scale.

- **Mars Climate Orbiter (1999):** one team's software output thruster impulse in
  pound-force-seconds, the other consumed it as newton-seconds — a factor of 4.45 that no
  review caught. The $327M spacecraft hit the Martian atmosphere instead of orbiting.
- **Gimli Glider (1983):** Air Canada 143 was fueled using pounds where kilograms were
  required during a units transition and took off with roughly half the fuel computed.
  Both engines flamed out at 41,000 ft; the crew dead-sticked a 767 onto a drag strip.

Both had reviews, checklists, and professionals. What failed was the *cross-check against
an independent estimate*. So:

- **State units once, in the parameter block, and never mix.** In this pipeline everything
  is millimetres until a glTF boundary says otherwise (`verification.md` #5).
- **Estimate before you measure or compute.** A hose connector is ~20 mm, not 2 or 200; a
  fist is ~90 mm. If the number that comes back disagrees with the estimate by an order of
  magnitude, the *number* is guilty until proven innocent.
- **Cross-check any measurement a design depends on** by a second route: a different tool,
  a datasheet, a published standard, a cross-section of the mesh at a second height. Two
  agreeing independent sources are evidence; one source is a hypothesis
  (see `reference-geometry.md` for the contradiction check).

## Provenance and revision discipline

Six weeks later, a measured value and an invented one look identical in code. The only
defence is recording provenance at write time:

- **Per critical dimension:** value, source (measured / standard / vendor CAD / community
  mesh / guess — the SKILL.md authority ranking), and verification status (verified on
  real part / coupon-tested / UNVERIFIED). Keep it in the project docs
  (e.g. `docs/dimensions.md`) next to the parameter block that uses it.
- **Version the parametric source, not the exports.** The `.py`/`.scad` file is the truth;
  STEP/STL/GLB are build artifacts, regenerable and therefore not worth versioning beyond
  tagged releases. The person who "fixes" an STL directly has forked the design — the next
  regeneration silently reverts their fix (`verification.md` failure catalogue, last row).
- **Keep a change log that says what must regenerate.** "Increased CLEARANCE 0.25→0.35
  after coupon #3 — re-export adapter + collar; housing unaffected" is one line and saves the
  next session from re-deriving which artifacts are stale. If renders or a website consume
  the exports, the asset-contract note in SKILL.md covers handoff.
