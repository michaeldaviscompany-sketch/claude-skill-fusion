# Design for manufacture — the constraints that bite

Every process rejects certain geometry, and it tells you at the worst possible time —
after the part is quoted, printed, or moulded. This file lists, per process, the rules
that actually reject parts, with the numbers where numbers exist. Exact values vary by
machine, material, and shop — **verify against the actual printer profile or supplier's
design guide; do not trust recalled numbers for anything critical.** Ranges below are
typical for hobby/prosumer FDM and SLA and general job-shop CNC.

## FDM printing

- **Overhangs beyond ~45° from vertical need support.** Below that the previous layer
  carries the new one; beyond it the perimeter droops. Supports work but scar the surface
  they touch and cost removal time — chamfer instead of overhang where you can (a 45°
  chamfer under a boss prints clean; a square underside doesn't).
- **Strength is anisotropic — parts are weak across layer lines.** Layer adhesion is
  commonly around half the in-plane strength, sometimes much less; a part loaded in
  tension across layers delaminates at loads it would shrug off in-plane. **Orient the
  print so the load runs along layers**, and treat any Z-loaded snap or thread as suspect.
  This single fact decides the orientation of most functional FDM parts.
- **Holes print undersize, typically 0.2–0.5 mm** (worse for small holes): the extrusion
  path corner-cuts arcs and the bead bulges inward. Drill or ream critical bores, or
  compensate through the model's `clearance` parameter tuned on a coupon
  (`prototyping.md`) — never by editing the mesh.
- **Elephant foot:** the first layer squishes outward ~0.1–0.3 mm. Any fit that engages
  at the bottom face will jam. Chamfer the bottom edges of mating features (0.3–0.5 mm
  at 45° is enough).
- **Bridging:** unsupported horizontal spans print acceptably to roughly 5–10 mm and sag
  beyond; a flat ceiling over a large pocket needs support or a shallow arch/teardrop.
  Round horizontal holes combine an overhang and a bridge — teardrop them if the top
  surface matters.
- **Walls as nozzle-width multiples.** With a 0.4 mm nozzle at ~0.45 mm line width, walls
  near multiples of the line width (0.9, 1.35, 1.8, 2.4 mm) print solid; an off-multiple
  wall (e.g. 2.2 mm) leaves an internal gap or forces thin infill that weakens and slows
  the print.

## Resin / SLA / MSLA

- **Hollow volumes need drain holes — plural.** A closed cavity traps uncured resin, and
  worse, the trapped volume acts as a suction cup against the FEP/build platform each
  lift, ripping parts off supports. Add at least two holes of ~3.5 mm or larger (one for
  drain, one for air), positioned so the volume drains in the print orientation. Plug
  them after wash if the design needs a sealed volume.
- **Supports leave witness marks** — small raised/torn nubs where each tip touched. Keep
  supports off cosmetic faces and off sealing/mating surfaces; orient the part so those
  faces are self-supporting or face away from the plate.
- **Post-cure shrinkage and distortion are real.** Parts shrink slightly (resin-dependent,
  fractions of a percent to ~1% linear) and can warp during UV post-cure, especially thin
  flat sections. Measure critical dimensions *after* full post-cure, not off the printer,
  and coupon-tune fits at that state.
- **Thin free-standing features are brittle** compared to FDM — cured resin is glassy.
  Below ~1 mm expect breakage in handling; below ~0.5 mm expect breakage in washing.
  Standard resins also creep and embrittle with age and UV; don't use them for
  load-bearing clips.
- **Parts contacting skin, food, or anything a person takes in need an explicitly
  certified resin** (e.g. medical/dental classes tested to the relevant biocompatibility
  standard), printed and post-processed per the manufacturer's validated workflow — an
  ordinary resin part that "looks clean" does not qualify. See `prototyping.md`. Bureaus
  and makerspaces keep a dedicated printer loaded with certified resin precisely because
  the material and workflow cannot be mixed.

## CNC machining

- **Internal corners inherit the cutter's radius.** A rotating endmill physically cannot
  cut a sharp internal corner. Design internal radii *larger* than a standard cutter
  radius (so the tool doesn't dwell in the corner), or add a relief/dogbone where a
  square mating part must seat.
- **Depth-to-diameter limits:** pockets and holes beyond ~3–4× the tool diameter need
  long-reach tooling, lighter cuts, and cost disproportionately; beyond ~8–10× many shops
  simply decline. A deep narrow slot is the classic uncostable feature — widen it, or
  split the part.
- **Every setup (reorientation) adds cost and tolerance loss.** Features cut in one
  clamping locate to each other beautifully; features cut in different setups relate only
  as well as the re-fixturing. Design so critical features share one face of approach,
  and put the tight relationships within a single setup.
- **Undercuts need special tooling** (T-slot/lollipop cutters, or a 5-axis machine) —
  avoid unless the function genuinely demands them.
- **The tolerance cost curve is steep:** ±0.1 mm is routine; ±0.025 mm means slower
  feeds, better fixturing, and inspection time; ±0.01 mm and better means grinding,
  temperature control, and gauges. Cost roughly doubles per band. Tolerance the two
  surfaces that matter and leave the rest at general tolerance (ISO 2768).

## Injection moulding

Tooling costs thousands to tens of thousands before the first part, so the geometry rules
are enforced at quote time — and violating them produces cosmetic defects on every one of
the ten thousand parts.

- **Uniform wall thickness is the prime rule** (typically 1–3 mm). Thick sections cool
  slower than thin ones and shrink after the skin freezes → sink marks outside, voids
  inside, warp everywhere. Core out thick regions; keep adjacent walls within ~25% of
  each other and make transitions gradual.
- **Draft on every face in the pull direction, 1–2° typical** (more for textured
  surfaces). Zero-draft walls scrape the mould on ejection and scuff or stick.
- **Ribs at 0.5–0.6× the nominal wall.** A rib as thick as the wall creates a thick
  intersection that sinks on the cosmetic face opposite it. Get stiffness from more ribs,
  not thicker ones.
- **Generous radii** (inside radii ≥ ~0.5× wall) — sharp corners concentrate stress,
  impede flow, and cost mould life.
- **Parting line and gate placement, decided early.** Both leave visible marks and the
  parting line constrains where draft must go; a cosmetic face crossed by a parting line
  is a design error discovered at the first shot.
- **Undercuts cost side-actions** — sliding mould sections that add thousands per
  feature. Snap features can often be redesigned so a pass-through hole lets the main
  mould halves form the undercut for free.

## Sheet metal

- **Minimum bend radius ≈ 1× material thickness** as a rule of thumb (softer alloys
  tighter, hard/thick material larger). Bending tighter cracks the outside of the bend.
- **Bends stretch the material**, so the flat pattern is shorter than the sum of the
  faces. The bend allowance is computed from the K-factor (position of the neutral axis,
  typically 0.3–0.5, ~0.44 as a default) — let the CAD tool's sheet-metal environment
  compute the flat pattern with the shop's K-factor, then verify the first article.
  Hand-unfolding with nominal lengths yields parts that are millimetres off.
- **Minimum flange length ≈ 4× thickness** (plus bend radius) — shorter flanges can't be
  gripped by the brake tooling and come out mangled.
- **Keep holes and slots ≥ ~2.5× thickness + bend radius away from bends**, or they
  distort into ovals as the material stretches. Punch after bending if a hole must sit
  closer.

## Design for assembly

The cost of a product is mostly decided by its part count and how those parts go
together, not by any single part's machining.

- **Fewer parts beat cleverer parts.** Every part carries ordering, stocking, handling,
  and a chance to be missing. Merge parts that don't move relative to each other and
  don't need different materials.
- **Self-locating features beat instructions.** Chamfers, pilots, and nesting steps make
  parts fall into place; a part that must be held aligned while fastened will be
  assembled crooked some fraction of the time.
- **Poka-yoke: make wrong assembly impossible**, not discouraged. Asymmetric bolt
  patterns, keyed shafts, connectors that only fit one way. Anything that *can* be
  assembled backwards eventually will be — and for a device with a gas path, a reversed
  check valve is a safety event, not a rework ticket.
- **Snap and press fits vs fasteners:** snaps assemble in one motion with zero loose
  parts but are process-sensitive (FDM snaps must flex along layers) and hide their
  failure; fasteners cost time and inventory but survive disassembly. Prefer snaps for
  high-volume light-duty joins, fasteners where service or load demands them.
- **Provide tool access.** A bolt you can't reach isn't a fastener; leave driver
  clearance (straight-line access, plus room for the hand or bit holder).
- **Design for disassembly** where service, cleaning, or consumable replacement is
  expected — which for a consumable-cartridge product is the business model, not a nicety.

## Choosing a process

| Factor | FDM | SLA resin | CNC | Injection moulding | Sheet metal |
|---|---|---|---|---|---|
| Sensible volume | 1–50 | 1–50 | 1–500 | 1,000+ (tooling amortized) | 10–10,000 |
| Tolerance (practical) | ±0.2–0.5 mm | ±0.1–0.2 mm | ±0.025–0.1 mm | ±0.05–0.1 mm | ±0.1–0.5 mm |
| Materials | commodity thermoplastics | resins incl. certified biocompat | metals + engineering plastics | huge thermoplastic range | metal sheet |
| Cost of unit #1 | cents–dollars | dollars | tens–hundreds | thousands (mould) | tens |
| Cost at 10,000 | poor | poor | poor–fair | excellent | good |
| Lead time | hours | hours–days | days–weeks | weeks–months for tooling | days–weeks |
| Reach for it when | functional iteration, coupons | fine detail, seals-adjacent, biocompat one-offs | tight-tolerance metal, real fits | committed design at volume | enclosures/brackets from flat stock |

The usual path for a product like this: FDM to iterate geometry → SLA (certified resin)
for fine-feature or certified-material prototypes → CNC for the few metal or tight-fit parts → injection
moulding only once the design is frozen, because the mould freezes it for you.
