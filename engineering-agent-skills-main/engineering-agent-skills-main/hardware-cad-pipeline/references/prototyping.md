# Prototyping — sourcing, coupons, and test discipline

## Standard parts first

Before modeling anything, check whether a commodity part exists: hoses, valves,
fasteners, connectors, bearings, gaskets are solved problems with published dimensions,
certified materials, and supply chains. Model only the interface or adapter that is
genuinely your design, and let the published standard define the mating dimensions. A
sourcing pass (with prices and links, buy-vs-make per subsystem) is usually an afternoon
that saves weeks — and it often reveals that the "custom" part you were about to model
is a $4 catalogue item with a certification you couldn't have produced yourself.

## Reference models and licensing

- Community models (Printables, Thingiverse, GrabCAD) are often **CC BY-NC** — you may
  measure and study them, but geometry *derived* from them cannot ship commercially.
  Measure → record dims + provenance → re-model clean from the numbers and the published
  standard. The clean re-model costs an hour; untangling a licence taint from a shipped
  product costs the product.
- Meshes from print-sharing sites bake in the author's print compensation; treat their
  dimensions as hypotheses, not authority (see `reference-geometry.md`).
- Some sources are login-walled (GrabCAD); don't create accounts just to grab a
  reference — find an open source or measure the real part.

## Prototype the risk, not the product

The purpose of a prototype is to answer a question, and the question decides the
fidelity. Building the whole product to answer one question is the most common and most
expensive prototyping mistake: you wait days for an artifact whose one interesting
feature could have been tested in an hour.

**Build the smallest artifact that answers the biggest unknown.** List the unknowns in
order of how badly a wrong answer hurts, then ask what the cheapest object is that
settles each. A coupling's real question is "does this engage the commercial mating
part" — a 20 g coupon answers it, and the full assembly answers it no better. A
mechanism's question is "does it move without binding" — a two-part bench rig answers it.
A consumable's question is "does it last as long as the model says" — a tube of the
material answers it. None of these needs the product to exist.

Climb the cost ladder only as fast as the questions demand:

| Rung | Cost of being wrong | Answers questions about |
|---|---|---|
| Cardboard / paper / tape | minutes | size, reach, ergonomics, packing, "does it even fit" |
| FDM print | an hour, cents | geometry, fit, mechanism, assembly order |
| SLA resin (certified grade where required) | hours, dollars | fine features, seals, surface finish |
| CNC / cast / metal | days, hundreds | strength, thermal, production-representative behavior |

Each rung should retire a risk before you pay for the next. If a cardboard mock-up shows
the enclosure won't sit flat where it must mount, that discovery cost tape — the same
discovery in a machined housing costs the housing. Iterate cheap → expensive: the order of
prototypes should follow the cost of being wrong.

## The coupon loop

Print the smallest artifact that answers the biggest unknown — usually just the mating
feature, a few grams of material:

1. Print the coupon with the current `clearance` value.
2. Test the fit on the real counterpart (twist, insertion, seal).
3. Adjust `clearance` (one variable at a time), reprint, retest.
4. Only then commit to the full part.

The coupon exists because printed dimensions are a function of *this* printer, *this*
material, *this* orientation — no table replaces it (`dfm.md` explains why holes print
undersize and first layers bulge). A coupon result is only transferable if the full part
prints in the same orientation with the same profile.

## One variable at a time, and a log

Three simultaneous changes teach you nothing: if coupon #4 fits after you changed the
clearance, the orientation, *and* the material, you don't know which change did it, and
you can't transfer the lesson to the next part. Change one thing per iteration — it feels
slower and is faster, because every print produces a conclusion instead of a shrug.

Keep a dated test log next to the part source. The format matters less than the
discipline of filling in the **concluded** line — a measurement without a conclusion is
a photo of a number:

```
## 2026-03-14 — coupon #3, twist-lock collar
CHANGED:   CLEARANCE 0.25 → 0.35 (only change; same PETG spool, same orientation)
MEASURED:  tab tip circle 22.38 / 22.41 / 22.40 mm (calipers, 3 readings, zeroed)
TESTED:    twist-fit onto the commercial mating part — engages, slight bind at last 10°
CONCLUDED: 0.35 near-correct; bind is on lug flank not tip circle → try 0.40 on
           lug width only, keep tip clearance at 0.35
NEXT:      coupon #4 with split clearances
```

Six weeks later this log is the only way to distinguish a tuned value from a guessed one
— it is the experimental provenance that `engineering-practice.md` demands for
dimensions.

## Design for testability

A prototype you can't measure answers nothing. Decide *how* each question will be
measured before printing, and give the artifact the features the measurement needs:

- **Instrumentation access:** a sensor port, a tap for a pressure line, a window, a
  removable lid — cheap in a prototype, and often worth keeping in the product (a
  service port is a test port that shipped).
- **Measurable features:** calipers need two parallel accessible faces; an internal
  channel's diameter can't be measured after printing unless a pin gauge can reach it or
  you print a sacrificial half-section. If a dimension matters, make it reachable.
- **Reference surfaces:** include a known flat or a known 10.00 mm step on early coupons
  — it separates "my printer is off globally" from "this feature is off locally."
- Cut-away and half-section prints are legitimate prototypes: an enclosure printed as a
  half-shell shows internal packing, wall thickness, and cable or tube routing for half
  the material and none of the disassembly.

## Measuring practice

The design is only as good as the numbers it stands on, and each tool has a band it's
honest in:

- **Calipers** — the workhorse, resolution 0.01 mm but practical accuracy ±0.02–0.05 mm,
  worse in unpracticed hands (jaw tilt and squeeze pressure are the errors). Fine for
  most printed-part work; not for deciding a 20 µm fit.
- **Micrometer** — ±0.01 mm or better over its 25 mm range; the ratchet stop removes the
  squeeze-pressure variable. Use it when a fit lives or dies on hundredths.
- **Pin gauges** for bores — calipers measure a bore's *chord* geometry badly and can't
  feel taper or out-of-round; a go/no-go pin pair answers "does a 12.25 pass and a 12.35
  not" directly, which is usually the actual question.
- **Thread gauges** for threads — pitch and form, not guessed from a blurry photo of the
  crest spacing.
- **Three readings, not one**, at different positions/rotations. Agreeing readings give a
  value *and* a spread; a lone reading gives neither. If two readings disagree beyond the
  tool's band, you have zero measurements — find out why before using either
  (`reference-geometry.md`).
- **Zero the tool first** (closed-jaw for calipers, standard bar for micrometers) and
  clean the faces. A caliper with 0.08 mm of grit zeroed into it faithfully adds 0.08 mm
  to every "verified" dimension in the project.

Record what tool made each measurement in the log — a caliper value and a pin-gauge
value are different confidence levels, just like a measured and a recalled standard.

## Contact-path materials are a hard constraint

If a part contacts skin, food, or any gas or fluid a person takes in, material selection
is a requirement, not a preference. Identify the standard that governs your contact path
early — biocompatibility and food-contact families each impose material *and* process
requirements — and note that certification generally covers the **validated workflow**
(print + wash + cure, or certified stock and coolant for machining), not the raw material
alone. An uncertified part that "looks clean" does not qualify. Record the constraint in
the project docs, not in someone's memory.

## Discipline

- **Prototype the risk, not the product.** Cardboard before resin, resin before metal,
  coupon before part, bench before assembly.
- **Iterate cheap → expensive.** The order of prototypes should follow the cost of
  being wrong.
- **One variable at a time, and log it dated** — or three prints teach less than one.
- **Design for testability**: leave instrumentation access and features you can actually
  measure with the tools you own.
