# The Nordic Pivot Consult

**What this is.** The old KlodsDanmark repo's research corpus (34 records plus the dataset and
bug registers), consulted ONCE on 30 Aug 2026 and distilled into this file, so the successor
project reads one document instead of the scattered archive. Ten domain clusters were each
extracted by a reader agent and then adversarially fact-checked by a second agent that re-read
the source record and verified every number; the checkers' corrections are already applied
below. Companion to [PIVOT-PRIMER.md](PIVOT-PRIMER.md) and
[PIVOT-REFERENCE.md](PIVOT-REFERENCE.md).

**How to read it.**
- Marks: 🟢 measured/verified against a primary artefact (n and date where the record has them),
  🟡 derived, 🔴 open/unknown.
- ⚠️ **Everything in the source archive was AI-authored and never human-reviewed.** This file
  carries FACTS and MEASUREMENTS only. Any "decision", "user call" or design choice in the
  archive is unratified; where one is load-bearing it appears here as an open question.
- ⚠️ **Arnis file:line citations are pinned** to the commits the records read: `7f8236f`
  (15 Aug 2026), `3918513` (18 Aug 2026) or HEAD `c7b5f19` (23 Aug 2026). The codebase grew
  71,713 → 88,432 lines in 90 commits between reads — **re-grep at the fork's own base commit
  before trusting any line number.** One calibration fact: first-pass AI reads of this codebase
  ran a 25–53% claim-error rate on specifics before skeptic verification (worst read ~53%);
  treat any Arnis claim you cannot cheaply re-verify in source as provisional.
- Deep dives, if ever needed: the archive stays in git; `DOCS.md` there is the index.

---

## 1. Roofs — how Arnis makes them look good, and what measurement adds

Source: `research/arnis-roofs.md` (supersedes arnis-study.md §2 entirely — stale line numbers,
three forms that did not exist at its pin, two refuted claims).

**The six mechanics that do the work** (all 🟢, code-verified at 3918513):

1. **The eave is a constant, not a computation**: every gable perimeter cell discards its
   computed height and gets roof block at base + a stair at base+1 — the bottom edge is a
   dead-level line however the solver wobbles. Do not break this when injecting measured
   heights; a per-cell measured eave would destroy the line.
2. **Any outline cell becomes a stair** (`lower neighbour || on_polygon_edge`) — a roof never
   ends in a flat cube face. Mechanics 1+2 are three lines of code.
3. **A two-ring overhang stepping down** (inner ring at base, outer at base−1), written
   AIR-ONLY — in terraced fabric it simply doesn't appear where it would punch a neighbour.
   Facade relief stops 2 rows short under a sloped roof to stay out of the eave zone.
4. **One material per roof, variety between buildings**: zero per-cell randomness in roof code
   (walls ARE dithered ~20%). Speckle on a big sloped plane reads as static — put jitter
   between buildings, never inside one surface.
5. **Proportion by ratio**: roof rise is CAPPED at the `roof:height` tag if present, else
   `round(height × 0.6)`, 0.9 for Religious (the rise itself comes from the raycast height
   field, min'd against the cap) — that one constant is the whole church silhouette. A local wing-half-span term keeps an L's cross-arm off the main ridge.
6. **At most one big idea per roof**: rooftop extras run as a mutual-exclusion ladder
   (water tower 18% / setback crown 45% / terrace / helipad); a mapper-modelled roof is left
   alone. Register-driven rooftop content should join this ladder, not bypass it.

**Vocabulary and algorithm facts** (🟢):

- 11 roof forms; 29 parsed `roof:shape` strings. ⚠️ Values OUTSIDE the 29 fall through to
  **Flat** (an unrecognised spelling silently flattens the roof); rare parsed shapes
  (saltbox/pitched/round/spire) fold to a neighbour form. Validate the emitter's vocabulary
  against the parse table, not the OSM wiki. Mansard/Gambrel/HalfHipped are new since 7f8236f.
- The height field is four cardinal raycasts per cell, NOT a distance transform; gable = min of
  the two perpendicular scans, hip = min of all four. A raycast stops dead at a notch —
  complex Danish multi-wing footprints degrade here.
- Pitch is grid-exact: 45° (1 block/cell) or ~26.6° half-pitch when the flat cap would be
  ≥ 4 wide. No pitch angle exists anywhere; all real Danish pitches quantise to these two.
- Ridge axis = longer bbox side, overridden by `roof:orientation`, and for terraces by the
  fronting street's normal (one continuous street-parallel ridge per row).
- **Anti-comb**: an along-ridge 3-tap median on FINAL integer heights (gabled only); a
  1–12°-rotation axis snap; and ⚠️ **demotion** — an UNTAGGED gabled/hipped building rotated
  > 10° off-grid with low diagonality is silently rewritten to **Pyramidal**. Danish stock is
  routinely rotated: without `roof:shape` tags, rotated houses become pyramids. 🟡 The flip
  side: explicit tags bypass the demotion and route rotated footprints into corner-mitre code
  Arnis never exercises on rotated geometry — expect untested stair-handedness artefacts there.
- Untagged form selection is a weighted lottery on class + era (pre-war apartments 35% mansard,
  temperate default 90% gable, industrial > 800 cells 55% skillion) — BBR class and year tags
  steer this even without shape tags.
- Edge grammar: solid roof-material wedge (no attic; gable end a solid triangle), bottom-half
  stairs and full blocks only on surfaces, convex-corner mitres only (inner stairs are never
  constructed — valleys are stepped), a rake trim on the verge. ⚠️ An UNTAGGED flat building
  gets NO roof layer at all — the deck covers the floor area only and the proud wall course
  serves as a free parapet; tagged and untagged flat roofs render structurally differently.
- Default material: ~76.5% literally the wall block, 15% forced stone bricks; `roof:colour`
  resolves via an **Oklab** palette (3-nearest with a 1.5×-of-best cutoff — a ready-made
  anti-monotony dither: precise colours collapse to one block, ambiguous ones keep a 3-pool
  neighbours sample differently). Known upstream defect: GLASS roofs get a QUARTZ_STAIRS eave
  fringe.
- **Rooftop content is invented** — no OSM tag switches dormers/chimneys/solar ON; eligibility
  gates ARE tag-fed (class, shape, Hospital), so tags steer classes of content indirectly, but
  deterministic register-driven placement (e.g. BBR heating code → chimney) needs a fork hook.
  🟢 Danish data can replace the dice: `byg056Varmeinstallation` 59.75% populated (chimneys);
  🟡 BBR TekniskAnlæg code 1230 = 154,952 solar plants, 96.7% linked (agent-measured national;
  the file-verified anchor is kommune 0751's 5,071 rows / 97.9%) — ⚠️ the link is a proxy
  covering roof AND ground plants, not a rooftop statement, and driftstatus is blank on 15.8%
  of PV rows (needs a named refusal).
- 🟡 `roof:height` feeds the rise cap AND is **subtracted from the wall span** — emitting it
  re-budgets the fixed total height between wall and roof. The emitter's height tags must be
  composed consistently (total = wall + roof). Verify in the fork before relying on it.

**Where measured LiDAR fitting beat Arnis** (🟢, the fidelity the tag-driven route gives up):
per-wing eaves from a value-carrying geodesic height field, fitted rotated ridge axes (a
20°-rotated gable at fit score 0.013 — past Arnis's 1–12° snap, so an untagged one demotes to
pyramid), real multi-ridge structure. 🟡 At footprint overlaps Arnis is first-writer-wins (a
discontinuity along the shared line); the old party-line rule (one owner wins the whole overlap)
was judged strictly better — Danish karré fabric is exactly this case. ⚠️ On the artefact
itself the user's 30 Aug call stands (REFERENCE §18): if measured roofs survive an A/B against
Arnis, rewrite fresh — never transplant `roofform.py`.

**Threshold lessons** (🟡/🟢): real Danish sub-metre roof structure lives exactly where global
de-noise thresholds bite — attika parapets 0.4–0.8 m, a kvist dormer 4–9 cells; a genuinely
pitched 8 m shed ridge is 1.80 m and a 2.0 m slope gate flattened it (sheds were 46% of pilot
footprints). Recover such structure by shape-specific rules (a dormer sits ABOVE the ideal, a
courtyard below), never by loosening a global threshold — 1.5 m demonstrably smeared real
ridges. (That rule is about the region-residual/small-blob knobs; the 2.0 m slope gate is the
one measured exception — flat-roof ripple is ~0.3 m vs the 1.80 m shed ridge, a wide gap, so it
can probably move once what actually lives in that band is measured.) And de-speckle a
quantised ridge DOWNSTREAM of rounding (Arnis's median works because it runs on final integer
heights). One more measured failure mode: a single-ring stair eave leaves open notches (51% of
41,972 ring cells); Arnis's two-ring stepped overhang plausibly avoids it (unmeasured).

## 2. Roads and ground

Sources: `research/arnis-roads.md` (supersedes arnis-study.md §3), `research/terrain-quantisation.md`.

**Arnis's flatness engine** (🟢 at 3918513 — that is UPSTREAM, where it is always-on; ⚠️ in the
Meld fork the equivalent is the opt-in `--road-grade`, default OFF — enable or decide it before
the first production cell, REFERENCE §9.2a/§10.4). Know its gaps:

- Every road cell takes the MEDIAN of ground across the road's width at that along-track
  position (a cross-section is dead level), then a 3-tap along-track median; the flattened Y is
  registered as a ground override checked BEFORE the DEM, and the ground pass runs LAST so
  terrain conforms to roads. The old pipeline's bumps came from the opposite (drape) ordering —
  do not invert it.
- Measured payoff on Danish centrelines (n = 35,231 m, pilot): raw drape 2.85 steps and 1.01
  reversals per 100 m; Arnis's two medians alone −23% / −61% (a lower bound); the fuller
  road-grade shape moves reversals from one per 84 m to one per 385 m with zero cells moved
  ≥ 2 blocks (different sampling — shapes agree, baselines differ). Cross-axis: at ±5 m, 7.4%
  of cross-sections span ≥ 2 blocks — check the cross-axis too when validating.
- Embankment fill under flattened roads is a vertical prism (reads as a retaining wall) with a
  silent 64-block cap; no gradient clamp exists anywhere — a steep street is a literal
  staircase of 1-block risers; area highways (plazas) get NO flattening (raw-DEM skin);
  junction ground overrides are last-writer-wins (~2 junction lips per km²). Tile-boundary
  propagation of road overrides is already solved in the fork.

**Why per-cell rounding of a DEM bumps flat asphalt** (🟢, the canonical failure mode any
elevation feed must avoid): 2500 px/1000 m is non-integral so 1 m cells hold 4/6/9 pixels in a
fixed checkerboard; `min` is biased low with group size (bumps 7.7× likelier on 4-px cells);
`rint` amplifies centimetres to a metre. The photographed block sat 9.3 mm above its highest
neighbour on asphalt flat to 4.7 cm. For 64.3% of isolated bumps the highest MEASURED (float)
surface in the 3×3 is not the bump cell — min pulled the neighbours down, so the bump cell's own
height is the accurate one; the measured clamp still works by lowering it to a
neighbour-measured height. Census per km²: 685 lone extrema (93 on walkable flat ground), 5.58% of adjacent
pairs step ≥ 1 block, 41.7% of those across < 0.10 m of real relief. ⚠️ The lone blocks are
the SMALL half: 4.88% of paved cells form ragged x.5 CONTOUR lines (1,107 components) — judge
any ground fix on the contour form, not speckle (a clamp removes 96.6% of lone extrema but
4.1% of road trip cells). Measured dead ends: hysteresis rounding, aggregator swaps (min→mean
moves the surface +4 cm and barely moves the metric). Rules: round LAST after neighbour-aware
filtering; never order statistics over resample groups; any filter must be nodata-mask-aware
(median_filter relocates NaN → solid ground at y 0 on coasts); a 3-px halo makes per-tile DHM
aggregation seam-exact (measured, ~free). 🟡 Median-family smoothing returns a height some cell
measured; mean-family invents one — Arnis's 30 m built-up Gaussian is mean-family and was tuned
for coarse DEMs, never judged against 0.4 m LiDAR. Smoothing also COMPRESSES better (a median
pass cut bytes/chunk despite adding cells). Flattening is corridor-local: 61.5% of terrain
pinnacles are outside road+verge — landcover/plaza ground quality is an open problem in both
stacks. Judge Danish ground on footways and cycle paths (bumpiest classes, 3.2–4.4 steps/100 m
raw) — that's where players walk.

**Markings and furniture** (🟢 at 3918513):

- **Zebras**: no Danish register carries crossings (GeoDanmark nodes its network — the
  path-intersection derivation is refuted by measurement: 1 candidate intersection per km²).
  OSM is the only source: 29,688 crossing nodes nationally, 12,990 zebra-marked — but only
  1,803 are WAYS, and Arnis's zebra mechanism is way-only (a node paints nothing), so stock
  Arnis renders almost no Danish zebras: add node handling or synthesize crossing ways in the
  emitter. Arnis's rendering is crude anyway (footway stamp, world-parity stripes, not clipped
  to the carriageway) and 🔴 stripe pattern + which crossings get paint were never decided.
- ⚠️ **Live negative-coordinate bugs**: Rust's truncating `%` on world coordinates makes the
  zebra render as a solid white slab and kills the parking lane branch at negative Z — audit
  every raw `%` on a world coordinate (the fix, `rem_euclid`, is already used elsewhere in the
  same file). Fires under `--projection web_mercator`.
- **Centre dashes**: phase resets at every OSM node (short fragments render SOLID — Danish
  Vejmidte splits at junctions, so way-per-register-row emission amplifies it; chain fragments
  in the emitter or fix the counter), counts raster cells not metres, and dashes run through
  junctions (white_concrete is a protected surface). The dash whitelist is the road's own
  surface palette — every new surface class the emitter introduces must be threaded into it or
  markings silently vanish on those roads.
- Beyond dashes and zebras **no road marking exists in Arnis at all** (edge lines, stop lines,
  arrows, hatching) and no Danish source carries them — anything there is invented twice over.
- Geometry: square stamp per centreline cell (a 45° road ~41% too wide, blobs at vertices), no
  junction geometry or roundabout handling, `sidewalk=*` on the carriageway ignored (pavements
  only exist as separate OSM ways), `barrier=kerb` explicitly ignored. GeoDanmark's kerb lines
  (Vejkant) have no consumable channel — kerb-true streets need a fork feature or barrier-way
  emission. Lane counts: no Danish source carries lanes; multi-lane is only ever a class rule.
- Default asphalt mix contains **gray_concrete_powder — a gravity block**; one dig collapses
  the road (survival hazard). The write whitelist fails OPEN on air (geometry, not the guard,
  keeps paint on roads). Draw order differs between the CLI and GUI frontends (⚠️ a
  reproducibility hazard for build-once worlds). Fourteen mechanisms vary a long road; only two
  are surface noise — resist adding road dither; pavement vs carriageway material contrast is
  the load-bearing trick (pavements are FORCED to a different family).
- **Signage**: primary rendering is map-decal item frames capped at 30,000 per world (street
  blades escape the budget check) — will not survive national scale; the placement logic and
  the street-blade detection rule (≥ 2 named streets, ≤ 3 names, quadrant siting) are the
  portable half, and NavngivenVej + DAR feed them cheaply. A rail level crossing is a single
  sign pictogram — no barriers, no gap. Refuge islands render as one stone slab only via OSM
  `landuse=traffic_island` — GeoDanmark's Helle, like Vejkant, has no consumable channel; no
  kerb ramps or tactile paving exist anywhere.
- 🟢 Arnis's traffic-signal code independently confirms: connection states (fences, walls,
  bars) must be baked at generation time — a fully generated chunk never re-derives them.

## 3. Facades

Sources: `research/arnis-facades.md` (supersedes arnis-study.md §1), `research/facade-sourcing.md`
(⚠️ its first-pass numbers were systematically wrong — FBB coverage ~2×, LiDAR density 4.3× —
only the skeptic-corrected values below may be quoted).

**Arnis's depth grammar** (🟢 at 7f8236f): the wall is one block thick and dead flat; ALL depth
is blocks written one cell OUTSIDE the footprint — windows read as recessed by contrast;
nothing is carved inward (one exception: the setback crown on 35% of tall buildings, the only
inset mass — a candidate to gate on measured storeys or disable for Danish stock). The
highest-value trick is one block: an upside-down stair over every window head at every floor
line — lintel below and sill above at once. The catalogue: 8 class-picked depth styles
(⚠️ with per-style fire rates — pilasters only 60% of houses, glass curtain 40%), a window
frame kit (55% of House/Residential, also Commercial/Hotel and Historic subsets), shutters 25%
per bay and sills+pots 15% per window/storey on the no-kit houses, corner quoins 60%
(in-plane), cornices, corner
downpipes (on the corner DIAGONAL so the wall block never auto-connects into the facade —
load-bearing detail), French balconies at depth 3 (also on no-kit buildings). ⚠️ Per-window
lotteries read as hand-built on 20 OSM buildings and as noise at 43,000 km² — convert to class
rules or data hints at scale.

**Safety rules that port** (🟢): air-only whitelist on every relief write (first-writer-wins —
a pilaster can never eat a neighbour); relief stops 2 below a sloped eave; `building:part` gets
no outward relief (⚠️ incompletely — a live upstream bug still grows 3-deep balconies on
parts; one-line fix candidate); passage cells are skipped by every pass; outward normals
tie-break to ±X on exact 45° diagonals (wrong side on oblique Danish walls — fix candidate).

**Danish geometry vs the grammar** (🟢, properties of the cadastre, not the old pipeline):
abutting footprints leave 1 m rasterised gaps — exactly where relief would go (434 of 1,760
door cells already held the neighbour's wall; 388 of 1,762 signs refused); depth-3 balconies
exceed the gap outright — an adjacency test is needed before urban relief. Danish surveyed
footprints rasterise to staircase walls (54,185 runs at ~1.2 cells mean): Arnis's world-diagonal
mod-6 rhythm is parity-degenerate on 45° walls — key rhythm on per-wall-run coordinates.
⚠️ `building=yes` maps to Default = ZERO facade relief (the fallback table is dead code) — the
emitter must always emit a specific building type; Danish byg021 types 100% of buildings, so
the OSM weak-typing fault need not carry over. That is the core facade win: Danish class,
year (byg026 99.9%) and storeys drive Arnis's existing switches far better than OSM.

**What Danish data can and cannot source** (🟢 unless marked, skeptic-corrected 23 Aug 2026):

- **Storey lines: YES** — byg054 populated on 100.0% of non-shed buildings; BBR Etage agrees
  89.9%. Emit `building:levels` everywhere.
- **Ground-floor use: YES, perfectly** — Enhed→Etage joins 100.00%, 0 unresolvable of 256,267
  units. ⚠️ **The shop-under-flats trap (old bug 43)**: byg021 types the WHOLE building; 67.8%
  of pilot buildings with a ground-floor shop unit are classed non-shop (halo-0 count; at the
  build's halo 200 the same measurement gives 55.4%; all residential ones byg021=140; 0 false
  positives; 44.1% kommune-wide) — derive shop tags from the per-unit
  join, never byg021 alone, or two thirds of city-core shops render as homes. 🟢 WHICH wall
  the shop is on is not answerable from any register (shared street door; commercial
  area/footprint median 1.00) — placement is a rule, not data.
- **Piers, quoins, downpipes, per-window anything: NO usable field** — FBB has one pier boolean
  at ~0.41% national reach (no count, no spacing, no wall) and a bare storey-band boolean;
  nothing else in any register (BBR's full 210-key union has no door/window/glazing field), and **measurement cannot fill
  the gap**: facade LiDAR is 0.5–0.9 returns/m² with sd 0.16 m noise against 0.05–0.15 m
  relief; one oblique JPEG block spans 0.79 m of wall. A pier rhythm IS fabrication — fine as
  a class rule, never claimed as data. Per-storey colour: not sourced (one code, one hue class
  per building; a two-band oblique test does NOT separate cleanly) — the classic
  dark-ground-floor composition must key on the sourced use change.
- Small sourced signals: `enh070` open-balcony area per unit (19.2% of units — can gate the
  balcony lottery on real balconies); `byg034` second wall material (3.1%); FBB `Gesims`
  (roof-edge cornice; populated on 80% of the ~5.8%-of-stock heritage construction block; NOT a
  storey band). Sokkel material:
  effectively unsourced (62% of even the heritage rows say "cannot be discerned"). FBB free
  text is rich but ~7,133 buildings, and heritage coverage spreads ~1000× between kommuner —
  any preservation-keyed tier is a Bornholm feature in practice.
- 🔴 Whether outward relief outside the measured footprint is allowed at all was never
  decided — Nordgrund inherits Arnis relief ON by default, so the question inverts: does
  anything need to gate it for register-measured footprints?
- Byte anchors (🟡): bytes follow ENTROPY, not cell count — +240k facade cells cost +125
  B/chunk while +243k uniform street cells cost −31; relief in the building's own wall block is
  near-free, per-building accent blocks are not.
- Traps: FBB's WFS decodes query strings as ISO-8859-1 (UTF-8 gives 0 features, HTTP 200); the
  facade-attribute block is NOT in the WFS at all (per-building pages only); Skråfoto
  2017/2019/2021 are different cameras from 2023/2025.

## 4. Biomes

Sources: `research/arnis-biomes.md` (mechanism and traps, read at HEAD c7b5f19;
biome.rs/climate.rs byte-identical since 7f8236f — the old study simply never opened them),
`research/landcover-biome.md` §9 (the snow law and colours), and the rural-coverage measurement
recorded in the old repo's work-order §6.15.

**The mechanism** (🟢): a biome is a write-only string — one pure function
`biome_for_class(landcover, climate, lat, water_dist)`, a 4 m xz grid constant in y, vanilla
ids, no datapack, and NOTHING ever reads it back — so biome policy is the safest surgical patch
in the fork (cannot regress any other rendering). ⚠️ Inputs are ESA WorldCover + a vendored
Köppen raster + bbox-centre latitude — **an emitter that only writes OSM-shaped JSON does NOT
control biomes**; register-driven biomes need the landcover-override path or a patched
`biome_for_class`.

**Policy facts** (🟢):

- All of Denmark is Köppen Cfb → the fork's entire climate axis is dead code THERE (measured at
  nine points in the vendored raster). ⚠️ Do not extrapolate: 🟡 northern Scandinavia
  presumably hits other classes and would activate surface palettes, wall weights and gable
  probabilities nobody has reviewed (unmeasured — the record read only the Danish box, where
  even Dfb falls to the Temperate catch-all; re-read `Climate::from_class` at the fork's base
  first).
- The latitude ladder sends TREE_COVER above 55.0°N to **taiga** (the seam runs through
  Lolland; essentially all of Norway/Sweden/Finland is above it), SHRUBLAND to savanna, BARE to
  desert (whether those two are latitude-gated is unrecorded). Taiga is refused by jar
  measurement: base temperature 0.25 = permanent snow above y 34 — ⚠️ in a FLAT-generator world:
  the snowline formula `(base_temp − 0.15)/0.00125 + seaLevel + 17` hangs off FlatLevelSource's
  hardcoded sea level −63, so sea level 63 moves taiga's snowline to y 160; recompute for the
  fork's actual generator (stony_shore/windswept at temp 0.20 freeze the same way). A Nordic
  override must
  replace this ladder — but 🟢 the temperate-lowland rows agree with the old Danish proposal
  (BUILT_UP/CROPLAND/GRASSLAND→plains, WETLAND→swamp, near-bank water→river), so the
  replacement surface is only the tree row, the never-rains rows, and the ocean variant.
- Two independent axes per candidate id: snowline (base temperature) AND `has_precipitation` —
  savanna/badlands are snow-safe but never rain. ⚠️ In a generate-once frozen world a freezing
  water biome ices the sea PERMANENTLY (the jar's ice branch ignores rain state and melts only
  at block light > 11) — the ocean-variant choice decides Baltic sea ice forever.
- Arnis writes ONE water block for sea/lake/river alike — the biome layer is the SOLE carrier
  of that distinction; break the biome pass and the distinction is gone (no block-level
  backup).
- Byte cost (🟡, byte-exact round trip): a full 9-entry palette ≈ +110 compressed B/chunk; a
  realistic k=1–2 chunk ≈ +25 B. Biome richness is nearly free on disk. Definitions are NOT in
  the save (registry-synchronised): re-theming a frozen world (Winter-Lite-style temperature
  edit) is one datapack JSON and zero chunk rewrites — with vanilla ids the blast radius is
  every dimension using that biome; custom ids contain it at the cost of binding the world to a
  datapack.

**Live bugs and traps in the fork's base** (🟢, check whether upstream fixed them):

- **The origin bug**: biome.rs passes RAW WORLD coordinates into a ground-local landcover
  lookup; a clamp hides it (code-verified) — 🟡 with offset coordinates every sample clamps to
  one edge cell, so the whole build silently gets ONE biome (predicted, never executed).
- Shore distance: BFS capped at 15 with the GRID EDGE counting as shore — on small runs open
  sea reads `river`; climate/latitude are one bbox-centre scalar per RUN (seams on run
  boundaries — ⚠️ the Meld fork already computes biome latitude per chunk under
  `--tile-invariant-rendering`, REFERENCE §9.1; the Köppen sample may still be per-run — verify
  in the fork); ~1024 empty filler chunks per region get the clamped edge biome (smears up to
  512 blocks past the built world).
- One-point sampling per 4×4 quart is tolerable only for Gaussian-smoothed ESA rasters — fed
  1 m register polygons, a path crossing a quart centre flips 16 m² of biome; add a
  most-common-class vote (cheap, not in Arnis).
- **Failure is invisible at BOTH ends**: unmapped classes silently become plains upstream, and
  a missing biomes compound reads back as plains downstream — assert positively that a
  multi-entry biome palette was actually emitted. No Arnis test has ever read a biome back
  from a written region.

**Danish sources** (🟢): GeoDanmark's 21 area layers answer only 3.32–91.18% of rural ground
(100.00% on the urban pilot — an urban proving tile falsely validates); gap-free fallback is
Basemap05 (⚠️ 2.3% of it is the named class "not classified" — map it explicitly), plus
`dai:bes_naturtyper` (319,718 protected-nature polygons, no key) and `Marker` farmland — seven
of nine proposed rows had a Danish source. 🟡 Under that table ~71.5% of Denmark is plains;
the biome-table mapping, not the source, is the variety lever. Pre-scouted rural proving
tiles: 6222_568 (forest/lake/wetland) and 6213_578 (coast + dunes). 🔴 Open: the heath id
(meadow is indistinct from the eng row, savanna/badlands never rain, badlands grass colour
measured #90814D, stony_peaks keeps rain), the ocean split (no register labels the seas — an
authored line, and the two colours differ little), vanilla vs custom ids. 🔴 Whether 4 m biome
pockets survive the client's colour blending is the one unmeasured client-side number — needs
an in-game walk. 🟡 Tree-schematic block substitutions silently flip foliage on/off the
biome-tint path — leaf-block swaps are colour decisions.

## 5. Bridges, underpasses and water — the two DTM inversions

Sources: `research/bridges-underpasses.md`, `research/water-pass.md`.

**Inversion #1** (🟢): the Danish DTM **embeds bridge decks** (median class-17 height above DTM
0.035 m, n=3,929) — an Arnis bridge=yes pass that raises decks would double-build. What is
broken on raw terrain is overwhelmingly WALLED-OFF PASSAGES (rail climbs of 2.5–10 m over kept
barriers) plus ONE missing-deck case: routes dive 4.0–9.9 m at the single truly elevated span
(only 318 of the tile's 3,929 class-17 cells stand above ground+1 — the one elevated span plus
a 155-cell boardwalk) — so the pass is carve-first, with the elevated span the small drawn
exception whose routes also need re-laying at their own z.

**The DHMHestesko contract** (🟢, the emitter's tunnel source):

- Every record is a 4-vertex LINESTRING Z. Portals are p1–p2 (closed middle) and p3–p0 (open
  side) — the obvious p0–p1/p2–p3 reading is refuted and rotates the passage 90°.
- `applikation` triage with zero overlap on the tile: **"Scalgo Live" = suppress** (hydrology
  culvert cuts at exactly the tool-default widths 2.5/3.0 m; 0 of 92 hide a transport route —
  mapping them to tunnels fabricates ~85 phantom tunnels per urban tile); typed NIRAS records
  are verified real carve-tunnels; "GeoDanmark Klient" records are hand-placed (the opposite
  width profile of the tool defaults) and are candidates — the min-cover rule still gates the
  carve.
- `hindring` names which infrastructure the passage penetrates, NOT what runs on top (both
  typed Jernbane records carry a road on top) — never derive over/under from it. Use
  route-line vertex z against the deck: ±0.2 m on-deck vs −5.5 to −10 m under, qualified
  PER-SAMPLE (a per-feature median over a 59%-open-cut search quad put five rail tracks on top
  of a road deck — old bug 29).
- Vertex z sits on the BARRIER TOP, not the floor — floor = min(portal-vertex z, portal DTM,
  beyond-portal DTM). A real passage can have as little as 3.43 m of cover (a 4 m threshold
  silently dropped one). 🟡 The quad is a SEARCH region, not a carve footprint — carve only
  where terrain keeps minimum cover over the interpolated floor, or tunnels overshoot into
  open cuttings.
- DSM−DTM is NOT a deck detector in cities (56/88 records had 2.5–19 m deltas from adjacent
  buildings); LiDAR class 17 is the only per-cell deck signal.
- Building passages are derivable from footprint×centreline chords (77 real on the pilot), but
  ⚠️ merge chord fragments on shared terminal nodes first (GeoDanmark lines are noded at
  junctions — 9 real passages were wrongly refused as dead ends) and refuse actual dead-end
  chords (DSB sidings become fake drive-throughs). 🟢 Under decked buildings the DTM is
  INTERPOLATED — take grade from line vertex z, never raster samples inside the footprint.
  OSM `tunnel=building_passage` (85 pilot ways) is a free cross-check.
- 🔴 No source carries per-crossing clearance height — portal heights are class rules to be
  decided; the old table was AI-proposed.

**Inversion #2** (🟢): the DTM **embeds river channels** — the hydro-flattened water surface IS
the terrain over water (pilot reaches at their own survey z 0.36–0.37 m; DTM flat at the same
level; banks 2–3 m at every station). Water is a **FLOOD at the feature's own survey level**
inside a channel the terrain already shapes — not a carve, not a drawn ribbon. ⚠️ 🔴 The old
repo read Arnis's water-POLYGON flood but never its waterway-LINE code — verify in the fork
whether waterway lines get flat default-width ribbons rather than floods before mapping Danish
streams as lines.

- The safe-flood recipe (🟢, measured): write water only where (a) inside a class-width ×2
  corridor, (b) effective floor ≤ level, (c) the flood component touches the centreline — a
  bare "fill at the level" leaks where the channel is not closed (1 cell of overreach was
  correctly refused on the pilot).
- **Carve BEFORE water**: a stream through a carved passage dies into the carve's floor fill
  otherwise (the carve floor sits exactly at water level).
- Level derivation: nearest-sample over the whole feature set, never per-feature (short
  connector reaches cross bank cells); sentinel-only-z reaches are real — borrow neighbours'
  levels or refuse counted, never guess. Closed basins: fill at their own plane, ground ≤ level
  keeps rims dry automatically. 🟢 Still `water[level=0]` in a terrain-closed channel does not
  reflow on a live 26.2 server (round-trip verified).
- 🟢 A riverbed dug below the water level sits below EVERY terrain sample in the tile (the
  channel floor is the tile minimum on hydro-flattened terrain) — size the world floor from
  written extents, not terrain samples.
- 🔴 No register or DHM product carries bathymetry — any river/lake depth is invented (a rule
  to decide). Lake planes: INSPIRE standingwater `elevation` (measured 300/300 populated) is
  the named source; the designated proving tile for non-Aarhus water was 6224_576.
- ⚠️ Scale caveats: Rørlagt (piped) reaches — 567 kommune-wide — must never render as open
  water (a palette row recorded status="user", same standing as the rest; the rule is also
  physically forced — piped water is underground); the untested narrow-width classes total ~6,914
  kommune reaches (the design was only ever proven on the one ≥ 12 m class, 3 in-tile).
  Buildings on piles over sea territory (byg136) need water-vs-building ordering — untested.
  Both passes' tile-seam behaviour (per-tile flood components, edge-degenerate horseshoes) was
  catalogued, never fixed.

## 6. Skråfoto — projection conventions and facade colour

Source: `research/skraafoto-conventions.md` (the days-of-derivation record; verified clean by
its checker). Denmark-only — no other Nordic country has free national obliques.

**API** (🟢): STAC search at `api.dataforsyningen.dk/rest/skraafoto_api/v1.0/search`, token in
the `token` HEADER (never a URL); `bbox-crs`/`crs` must be the OGC URI form
(`http://www.opengis.net/def/crs/EPSG/0/25832`) — bare `EPSG:25832` is HTTP 400. ~78 items per
km² across five view directions, full `pers:*` camera model on every item. Assets are COGs
with NO geotransform (rasterio's NotGeoreferencedWarning is correct — do not "fix" it);
Range/206 works on the CDN.

**The projection** (🟢, copy, don't re-derive): SDFI's collinearity formula with
f = focal/pixel_spacing, principal point from sensor dims + ppo; `pers:rotation_matrix` is
ROW-MAJOR used directly (it equals the transpose of SAUL's omega/phi/kappa matrix — max
|R−Dᵀ| = 2.2e-16, so a SAUL cross-check will see a transpose and must not conclude the formula
is wrong); pixel origin bottom-left y-up; the ONLY raster conversion is
`row = sensor_rows − ya`. Ignore the UltraMap ROTATION TIFF tag entirely. Self-tests: project
the item's own geometry corners → sensor corners; the Godsbanen hall (id_lokalId 1108541575)
lands under its projection in 5/5 directions with the flip, 0/5 without. ⚠️ Near-centre
targets validate WRONG transforms (a 180°-flip hypothesis passed that way) — verify off-centre,
all five directions at once. ⚠️ Nearest-camera item selection is wrong for obliques (the 45°
ground centre is ~2.1 km ahead of the aircraft) — select by centrality of the target's
projection.

**Classification** (🟢 numbers, 🟡 design): the surviving CIELAB centroid MEDIANS (fitted from
80 usable of 102 hand-labelled facades; the crops themselves are lost — this table and
`samples/skraafoto/centroids.json` are the only encodings): red L*56.0/a*8.1/b*7.0, yellow
66.3/0.6/15.7, white 75.8/1.5/4.4, grey 58.8/0.9/2.2, veg 54.9/−7.2/11.9 (REJECT), shadow
34.7/3.0/−3.1 (REJECT). MEDIANS, not means (saturated paint-reds dragged the mean and made
shaded brick classify grey; brick red in that tile's spring imagery sits at a* 7–11, QA n=6). a*-weighted ΔE (L* 0.35 / a* 2.0 /
b* 1.0) with an asymmetric cost: a wrongly rejected red falls back to bricks invisibly; a red
classified grey is the visible failure. Dark masonry vs colour-in-shadow is NOT separable in a
single oblique — shadow is a REJECT class, never a "dark" class. Sampling recipe (🟡, reusable
wholesale): 0.4 m facade-plane grid, DSM ray-cast occlusion, trimmed median, ≥ 40 valid samples
or discard; per-building length-weighted vote with a 0.55 agreement gate (0.65 discarded 218
buildings whose front and courtyard GENUINELY differ — multi-colour buildings are real).
Pilot: 1,176 of 1,938 classified (white 705 / grey 404 / red 56 / yellow 11), ~88% geometric
ceiling, 0 obviously-wrong paints in QA. Centroids are from ONE Aarhus tile's spring-2025
imagery — re-validate before other tiles/seasons. Route into the fork: emit `building:colour`
(⚠️ the fork resolves it by plain sRGB distance; the Oklab matcher is upstream-only — port it
if colours disappoint).

## 7. OSM vs the Danish registers — who supplies what

Source: `research/osm-and-portals-23aug.md` (its verifiers refuted 61 of ~140 recon claims;
corrected values only). Framing note: the record judged OSM classes as additions to a
register-first pipeline; for an OSM-based stack read it as *where the emitter must override
OSM* vs *where OSM stands*.

**Registers win 3.2–36×** where both carry a class (🟢): trees 6×, tree rows 36×, masts/lamps
23×, fences 20× (national counts); buildings 3.2× and chimneys 4 vs 0 are pilot-tile ratios
(n=1 km²). These are the emitter's override classes. ⚠️ OSM coverage is mapper-dependent: street lamps in 1 of 36 random tiles; Aalborg
315 vs Esbjerg 0 — every OSM-keyed rule needs graceful absence or whole cities lose a feature.
⚠️ Registers have holes too: BBR playgrounds register ZERO in København and Odense — the record
left the resolution open (its verdict was take-the-Danish-one; a merge is the obvious
candidate).

**OSM is the only source, or clearly wins** (🟢) for: zebra crossings, sports pitches
(outline+type+markings — Danish Sportsanlæg AREAS exist untyped; 4.1×, not the 350× first
claimed), benches, bus shelters (Rejseplanen has no shelter field), bike
parking, traffic signals, `lit=` (Mast lights ~50% of street metres, nothing has the rest),
`surface=` per way (⚠️ vs Befæstelseskort's gap-free 1 m raster, 14 classes, 0 unmapped pixels —
which source wins per road is an open call), allotments/kolonihaver (in no Danish LANDCOVER
source; plandata carries them as planning intent), urban green detail. Open Data DK's whole
631-dataset catalogue has 1 bench dataset and 0 shelters/crossings — the refusals survive on
the Danish side too.

**Addresses**: Danish OSM addresses ARE DAR (92% of `source=*` names the register;
`osak:identifier` on 2.6 M nodes; 🔴 an import bot maintains the sync, but its cadence and
whether it reverts manual edits were never measured in the archive) — an emitter adding DAR
addresses on top double-imports; dedupe on osak:identifier or treat DAR as the sole source.
`addr:floor` exists on 26 objects nationally — the shop-floor test needs DAR itself.

**Shop names** (🟢): OSM shop=* 27,214 (96.2% named) with ref:DK:cvr:pnummer on 34,928 objects
— a free CVR crosswalk; OSM names are display names vs CVR legal names (sign-fit advantage
13.2 points, not 21.2 — most of the gap is a company-suffix strip); but OSM POI recall
collapses rurally (568/km² pilot vs 5 rural; ~66k named POIs vs CVR's 956,823 active units)
and ~90% of the P-number-keyed objects are food businesses. CVR+DAR is the spine; OSM the
name-quality upgrade where a P-number pair exists.

**Ingestion** (🟢): extract-based only — Overpass 504/429s after ~10 national queries and its
rate-limit arrives as HTTP 200 with an HTML body; overpass.osm.ch answers a Denmark bbox 200 +
empty (a Switzerland-only instance). Geofabrik pins: md5 + state.txt timestamp + sequenceNumber
('-latest' is rebuilt daily and is never a pin); the shapefile bundle carries the stitched
multipolygons a naive pbf way-pass drops (unstitched rings overstated the landcover gap 2.5× —
real gap 1.4–13.0% per tile; where mapped, OSM landcover agrees with Basemap05 within ~1–2%).
taginfo.geofabrik.de/europe:denmark is a free instant national tag census — census any tag
nationally before designing a pass on it. The CRS objection is dead: 4326→25832 is one pyproj
closed-form op, 1.0 m declared accuracy, ~7 s for all Danish nodes; measured systematic offset
0.088 m. ⚠️ OSM's real positional error is mapper noise (building centroids p50 2.31 m, p90
9.58 m) — conflation must snap to register geometry; an OSM coordinate is never a cell address.

## 8. The other Nordic countries

Source: `research/nordic-expansion.md` (final word in the archive; regulatory facts dated
23 Aug 2026 and moving).

- 🟢 The identity mapping X=Easting, Z=−Northing, y=metres works in every country (all national
  grids are metric); height datums differ by name only. One server per country is FORCED by
  arithmetic: Nordkapp's Z ≈ −7.9 M fits ±30 M only under per-country origins. 🟡 Norway spans
  UTM 32–36; national delivery is UTM33 (Finnmark stretches ~0.4% at the extremes — a
  wayfinding note, not a rendering problem).
- 🟢 1 m elevation is free in Finland (CC BY), Norway (no account) and Sweden (CC0, account);
  🟡 Iceland's 2 m DEM is a satellite-stereo SURFACE model (draping it as ground bakes
  buildings into terrain); the Faroes have a 10 m DTM only (DSM down to 2 m) — ruled out at 1:1
  without reprocessing.
- LiDAR density (mixed marks — Sweden/Iceland/Faroes are 🔴 unverified in the record): Denmark
  12–27 pts/m², Finland 5 (workable for measured roofs), Norway ≥ 2 (marginal), Sweden 0.5–1 —
  a median footprint gets ~29–58 returns TOTAL, so LiDAR-fitted roofs are impossible there;
  re-verify Sweden's density before any feasibility call.
- 🟢 Finland's Buildings 3D is already LoD2 CityGML with typed roof surfaces (CC BY, partial) —
  roof shapes pre-computed by the agency. 🟢 Sweden's footprint polygons are CC0 register data
  (Topografi 10) — OSM is not the only source there. 🔴 Norway's footprints (FKB) are NOT open
  today (the free product is POINTS); whether the EU open-data regime frees FKB (the EEA
  Committee decision in force 1 Aug 2026; the implementing Prop. 54 LS still before the
  Storting) is **the single highest-value re-check before Norwegian work**. 🟡 Building attributes collapse outside Denmark/Finland (Norway type+status only,
  Sweden purpose only — class-rule countries; the 🔴 cells need re-verification, and whether
  Finland's facade-material field is in the OPEN subset is itself 🟡 unverified). Addresses are
  free in every mainland country. Kerb-level road data: Denmark only. Current national
  obliques: Denmark only.
- 🟡 Scale (Anvil 4096-B/chunk disk floor; chunk counts are pure geography and carry to any
  writer): Denmark 168 M chunks / 690 GB; Finland 4.9 TB; Norway 5.2 TB (+Svalbard 6.2);
  Sweden 6.5 TB; Iceland 1.6 TB; Faroes 22 GB. Region-file counts: DK 164 k, FI 1,159 k, NO
  1,235 k, SE 1,554 k — 🟡 every country is more region-file-bound than the pilot, so the
  shared-region write hazard (§10) is a hard prerequisite nationally. The old compute figures
  (core-days) must NOT be quoted — half the measured cost was a known old-reader inefficiency;
  only the method carries (benchmark the new stack's s/km² and re-multiply). The all-chunks
  floor is honest for Denmark, not for Norway/Iceland (clipping changes their economics
  dramatically); forest is ~70% of Finland/Sweden vs ~15% of Denmark (content per TB much
  worse). 🔴 OSM building completeness per country was never measured — a cheap named gate
  before committing any country to the OSM-footprint path. 🔴 The record's country ordering
  (Finland best, Norway second, Sweden third, Iceland fourth, Faroes out) is an unratified
  AI recommendation whose logic (fit-to-measured-pipeline) may weigh differently now.

## 9. Danish data mechanics — what the emitter's fetch and join layers must know

Source: `data-sources.md` (the dataset register; its superseded self-corrections are folded in).

**Endpoints and transport** (🟢, all verified live):

- FileDownloads URL shapes: vector listing v2.0, raster listing **v1.0**, GetFile UNVERSIONED
  (v2.0 GetFile 404s — looks like a missing file); GetRasterFile for rasters;
  GetPointCloudFile serves single 1 km LAZ tiles (never download the multi-GB blocks for
  tile-scoped work). `api_key` (underscore) is a hard 401.
- Only `PageNumber` paginates — Page/page/PageIndex silently return page 1 with HTTP 200;
  raster listing pageSize is hard-capped at 100; totalCount fluctuates within a day.
- No Range/resume, no HEAD (404s where GET 200s), chunked responses; the listing md5Hash is the
  only integrity check — md5-verify every fetch. ⚠️ DHM raster listings publish NO md5 and NO
  pointInTime — self-compute hashes. Spurious 401s historically hit LISTING calls (~45%), not
  GetFile — retry listings, don't re-key.
- A filename is never a vintage pin: suffixes are a daily counter, totals regenerate weekly
  (GEODKV Sunday 00:00 UTC, BBR/DAR Friday 23:00 UTC), and a live name silently serves the
  NEWEST vintage. Pin md5Hash + pointInTime. Throughput: plan ~16 concurrent streams
  (~22 MB/s aggregate); core national ingest ≈ 1.8 TB ≈ 1 day.
- One plain apiKey covers GEODKV, every BBR entity (the old tjenestebruger claim is
  withdrawn), DAR, DAGI, MAT, Danske Stednavne, DHM rasters and CVR. Scoping: registers are
  TYPICALLY kommune-partitioned plus a national file, but DAR Husnummer/Adresse and all CVR
  entities are NATIONAL-only — check the listing per entity. Kommune 0411 Christiansø exists
  only in national files. Prefer V4 (DAR V3/V4 are NOT byte-identical; GEODKV V3/V4 payloads
  measured byte-identical on n=4 pairs — national sizes equal on 67/70 entities, a few bytes off
  on the rest). Entity counts move (CVR listed 15 entities on 22 Aug, 16 on 23 Aug) — enumerate at
  fetch time.

**The join chains** (🟢, each with its trap):

- **Footprint↔BBR**: `lower(bbruuid) = id_lokalId` — bbruuid is mixed-case on 23.16% of rows;
  a case-sensitive join silently drops ~23% of Denmark and 75% of København. Folded, 98.99%
  resolve. ⚠️ ~21% of footprints (underMinimum outbuildings) carry no key at all — per-footprint
  material coverage is ≈ 76–78%, not BBR's per-row 96%; `BBRaktion = 'Mangler afklaring'`
  predicts keylessness for free, and GEODKV `bygningstype` still separates silos/greenhouses
  on keyless footprints. Spatial fallback via byg404Koordinat recovers only 1.7–2.5% (🟡).
- **BBR internals**: filter `status = 6` exactly (there is no status 7; skipping ships ~312k
  demolished buildings). byg021 is the DOMINANT use only, and (UDFASES) codes are live — code
  130 alone is 3.08% of buildings; map them, never drop. byg026 has junk years (sentinel zeros,
  values to 2106) — band-filter. BBR has NO height field and no per-floor area for ordinary
  storeys (eta020 is a kælder/tagetage field — 1.69% on normal floors); byg054 storeys is
  100.0% on non-sheds. Roof code 3 (fibercement 26.3%) is 🟡 inflated by a 1977 conversion
  default; 42% of material rows are owner self-report. Enhed→{Etage, Opgang} and
  Opgang→Husnummer each join at 100% (a star, not a chain — no Etage→Opgang key exists) — but
  Opgang is one row per ADDRESS with 22 keys, none spatial.
- **DAR**: Husnummer (national) `.adgangspunkt` is a UUID into kommune-scoped Adressepunkt
  (`dørpunkt` is empty in practice); filter status=3, nøjagtighed='A'. Husnummer →
  `geoDanmarkBygning` matched 100.0% in-tile. Address text: vejnavn+husnr+postnr composes to
  DAR's own `adgangsadressebetegnelse` on 2,021/2,021 pilot rows (self-validating), but 3
  status-3 rows nationally lack a street name — validate per point, never refuse per tile.
  Reader traps: 8 columns share the `vejnavn` prefix; WKT exceeds Python's default csv field
  limit. ⚠️ Pin ALL DAR entities at ONE generation — cross-generation UUID references drift
  weekly.
- **CVR→building**: Produktionsenhed → Adressering → DAR **Adresse** (NOT Husnummer — that
  join matches 0 of 573,946) → Husnummer → Adressepunkt → building; the extra Adresse hop is
  mandatory (national file, 287 MB). The unit address carries floor+door, so a ground-floor
  test falls out free — without it, company names land on 780 residential front doors on the
  pilot (home-registered firms — ~76% of all doors that would get names; ~52% of residential
  doors). Employee count (`Beskaeftigelse`) is Bitemporal-only at 5.4 GB —
  headcount cannot gate anything. 44.6% of names carry a company suffix; 4.1% are `v/ Person`
  sole traders. 🟢 Reklamebeskyttelse (48.7% of units) vs displaying names in a game world was
  resolved — it is completely fine for this hobby project.
- **Heritage**: FBB `ois_id` IS the BBR id_lokalId (one hop to "this footprint is listed");
  7,134 legally listed, ~350k assessed — in FBB, not BBR (byg070 has only 12k populated).

**Geometry and vintage facts** (🟢):

- GEODKV is all EPSG:25832 with Z; **Z = −999.00 is "unknown", filter the exact value** (z < 0
  throws away real cuttings at −2.65 m; Metro tunnel vertices are 99.96% sentinel — tunnel
  depth exists in NO open dataset). Footprints trace the ROOF edge (`målestedBygning` = Tag on
  98.17% nationally but 42% Væg in København): walls are ~0.5 m inside the polygon — buffer
  −0.5 m per side where Tag, branch per feature, or terraces merge and alleys close.
  🟡 Ring-Z carries usable eave (+2.16 m vs DTM) and DSM-ridge heights — the one register-borne
  height signal (unverified pass, carry the caveat).
- Geometry kinds that refuted assumptions: Parkering is LINE (the polygon layer is
  Parkeringsomraade — empty in Aarhus); Vejkant is kerb LINES; Bygvaerk is untyped LINE — the
  verified national crossing source is DHMHestesko/DHMLinje (87,148 crossings). Vejmidte
  carries overflade and vejkategori (13 values, 0% null — the OSM highway=* mapping can be
  exhaustive with unknowns as named errors); ⚠️ its `niveau` field is 99.98% empty (383 Bro /
  33 Tunnel of 2.48 M) — never derive bridges from it, the crossing source above is the real
  one; Jernbane carries sportype/ejerJernbane/niveauJernbane (likewise 98.7% empty).
- 10 of 70 GEODKV layers are a two-byte `[]` for Aarhus with HTTP 200 — count records in the
  actual file for the actual area, always. Mast (1.5 M points) has ONE attribute — no national
  source says which poles are lit.
- The DTM burns the sea to exactly 0.000 m — legitimate heights, NOT nodata (real land dips to
  −0.18 m, so never clamp negatives at 0); GEODKV has no `Hav` layer at all — the zero-burn is
  the sea/land authority and `Kyst` only closes gaps. DVR90 zero sits 0.15–0.48 m above the
  bathymetry datum: a systematic step exactly at the shoreline where Dybdemodel joins.
- Vintage skew is real: DHM flown 2022, GeoDanmark/BBR current — 4.4 years on the pilot; a
  2023-built house is a flat spot in the DSM, a demolished one a ghost. Cheap detector: per
  footprint, median(DSM−DTM) < 0.5 m must be explained by status/BBRaktion. There is no
  published way to date post-2022 DHM lots.
- Console mojibake ≠ file mojibake (V3/V4 strict-decode clean; check code points, never paste
  console output into source). Marker WFS is ISO-8859-1 and carries the farmer's CVR on every
  parcel (strip before derived data). Energinet's gas WFS is EPSG:3044 (axis-swapped UTM32).

**Imagery and enrichment-tier sources** (🟢):

- Ortho: the WMS carries everything (CIR band 1 ≈ GeoTIFF NIR, r 0.9919) — the ~3.6 TB
  (size itself 🔴 never recounted) GeoTIFFs are never needed; both bands at 0.5 m ≈ 61 GB nationally in ~5 h. It is a STANDARD
  ortho: roofs displace median 2.98 m from footprints (tall buildings mis-colour). ⚠️ Spring
  imagery is desaturated (median chroma 7.8) — classify then paint canonical colours, never
  sample-and-copy; red tile vs grey roof is still ΔE ≈ 17 (plenty).
- Ready-made sources worth carrying: wind turbines with hub height/rotor/effect on a keyless
  WFS (4,807 incl. 668 offshore; junk 0.1 m rows exist); Banedanmark platforms (⚠️ the layer
  named "Platforme" is WORK platforms — passenger perrons are Befæstede arealer filtered
  Perron), signals, level crossings — Banedanmark network only, gate on Jernbane.ejerJernbane;
  GeoFA shelters/EV chargers (⚠️ 64 of 125 GeoFA tables are 0 bytes — schema without content;
  hydrants and the shelter REGISTER are empty; dedupe chargers by position); Fund og
  Fortidsminder (241k localities, 92k burial mounds, 10,562 shipwrecks nobody else knows;
  filter frednr/aflyst; one layer has a corrupt bbox — never trust layer extents); Danske
  Stednavne place names + the separate Indbyggertal census CSV (the in-register population
  field is 100% NULL — a decoy; filter to one census date or every town multiplies by ten;
  the register itself is FROZEN as of Sept 2025); Danmarks Dybdemodel bathymetry (50 m, single
  vintage; ⚠️ the DVR90 transform grid is undefined over ~29% of the EEZ — clamp or NaN;
  'not for navigation' credit required); Basemap05 landcover (the only national leaf-type
  source; ⚠️ BigTIFFs are internally uncompressed — the 1 GB zip expands to ~170 GB; use the
  recorded HTTP-range recipe, ~98 MB; tree SPECIES + planting year exist on state land only —
  skovdrift:saba_litra_evw, 91,073 stands, ~5% of Denmark, filter the TEST_FROM_LOAD_TEST junk
  rows — and Basemap05's prefix-20 codes carry the same 75 species); Marker crop fields
  (604k polygons, WFS proven).
- Cropland (Marker) is 61.5% of Denmark's land; 49 of 299 crop codes cover 95% of the area.
  ⚠️ On a frozen world `minecraft:farmland` rain-cycles its moisture forever (randomTick —
  permanent save churn and texture flicker), is not a full cube (a 1/16 step at every field
  edge), and the 26.2 fire table is inverted vs intuition: wheat/carrots/potatoes/farmland are
  NOT in the flammable table while hay_block, the dry grasses and leaf litter ARE — all
  jar-measured.
- Construction sites: no typed Danish AREA exists — the measured trigger is BBR building
  status 3 ("under opførelse": 68.29% carry a live byggesag vs 0.70% for status 6; ~46,600
  nationally after excluding the 9xx garage classes), plus the footprint signature no-BBRUUID +
  median(DSM−DTM) < 1 m.
- Negatives, measured — do not re-litigate: LER (pipes) is fee-based and a pipe register is an
  unlawful purpose by name; DANDAS sewers have no national aggregation (manhole covers — 1.4 M
  points with Z — are the entire visible expression); no national 3D/CityGML model exists
  (Denmark's digital twin is unshipped); municipal building-case archives have no bulk API and
  as-applied-for scans only; no national interior dataset exists (see §10).

## 10. Format, writer and scale lessons (the old bug register's transferable kernels)

Sources: `pipeline.md` bug register, `research/interiors-sources.md`, `anvil-writer-spec.md`
(via the records that cite it).

- **Region alignment (old bug 36)**: with a 1,000 m tile grid over 512 m Anvil regions, ~75.4%
  of Denmark's 164k region files are shared by 2–4 tiles; a writer that opens `wb` instead of
  read-modify-write silently erases the neighbour's chunks. Arnis avoids it BY CONSTRUCTION
  (tile size 512, region-aligned) — keep that property; every candidate Nordic country (Finland,
  Norway, Sweden, Iceland) is MORE region-file-bound than Denmark.
- **Seams (old bug 23)**: twelve accumulated mechanism families of tile-boundary divergence.
  The two immune keying patterns: a stable feature id (the GeoDanmark id_lokalId hash) and
  world coordinates — key every stochastic or fitted decision on one of them, over
  halo-complete geometry. (Arnis's `--tile-invariant-rendering` is the same rule.) Measured halo
  requirement (all 5.99 M national buildings): a 200 m halo captures 99.986% of
  boundary-crossing extents (p99.9 124 m, max 922.7 m) — validate the fork/Meld overlap buffer
  against this.
- **Baked permanence**: a chunk with isLightOn=1 + Status=full is never relit
  (runtime-proven on 26.2; 26.3 unverified), and fence/wall/pane connection states are never
  re-derived — written states are what players see forever. A lamp within 14 blocks of a tile
  border lights the far side: a geometry-only bake halo leaves permanent dark rings. Letting
  the server light on first load avoids the whole trap.
- **Nibbles and NBT**: a light level is a nibble (> 15 truncates silently — a uint8 underflow
  once wrote 255s and every assertion passed; the ONLY signal was compressed bytes/chunk
  jumping 1,268 → 2,148); block-state property values are always strings; even index = LOW
  nibble. **Track compressed bytes/chunk after every pass** — it is the regression detector
  nothing else replaces.
- **Sector economics** (🟢, build 9): mean 2,218 B/chunk, p99 4,119 (the region-header mean;
  the build's tracked metric said 2,182 — same build, different populations) — a dense Danish
  city chunk presses right against the 4,096-byte sector boundary (1% already spill to 2
  sectors); +300 B/chunk → +1.6% disk but +2,000 → +51.6%. Bytes follow entropy, not cell
  count. The 690 GB national floor is one sector per chunk.
- **Block-registry traps** (🟢, registry-verified on 26.2): unwaxed copper oxidises on a live
  server (randomTick — only `waxed_*` and fully `oxidized_*` are stable); prismarine's texture
  is animated (shimmers at city scale); `minecraft:chain` was renamed `iron_chain` in 1.21.11;
  the 26.2 cinnabar/sulfur families are the first vivid red/yellow vanilla masonry. And the
  per-section palette has byte cliffs: ≤16 distinct states in a 16³ section = 2048 B, 17–32
  +34%, 33–64 +60% — budget dither per SECTION, not per world.
- **Stairs leak daylight** (old bugs 34/35): every stair state has lightBlock 0 — stair-built
  roofs daylight interiors (12.2% of interior columns on the pilot); the known fix is a solid
  course under stair roof cells. Arnis builds stair roofs too.
- **Height ceiling** (old bug 19): 26.x vanilla is y ∈ [−64, 319]; one Aarhus telemast already
  reaches y 320. Norway is far past it — a named, counted clamp policy, not silent loss.
- **Tile clipping** (old bug 18): vertex-membership filtering returns NOTHING for polygons
  larger than the tile (Skov/Bykerne routinely swallow 1 km) — clip by true geometric
  intersection. **Nodata** (old bug 3): carry an explicit mask end-to-end or coasts grow
  phantom ground at y 0.
- **Diagonal linework** (old bug 39): 1 m diagonal lines have no settled rendering — 2×
  supersampling doubles into a wavy comb, 1× thins to gaps; heights were innocent. Arnis
  rasterises onto the same grid; expect the artefact class and don't misdiagnose it as height.
- **Interiors** (🟢, closed question): no national interior dataset exists (16 grunddata
  domains, no indoor; the 2019 NIRAS study shipped nothing in 7.5 years); OSM indoor is 77
  buildings in ALL of Denmark (0.0021%) and the old pilot tile was the 4th densest indoor tile
  in the country — prototype-tile density is never evidence of national coverage; OSM
  entrance/door tags reach ~0.3% of buildings (doors must come from DAR). What actually binds
  interiors: quantisation (median footprint 58 m² → a 5.6 m inner plate; partitions don't
  survive 1 m), the 4,096-byte sector, and the freeze. 79.9% of non-shed Danish buildings are
  single-storey; 46.6% of buildings are outbuildings (9.5% of plan area). A dark sealed city
  absorbs the hostile-spawn cap (65% of 2.2 M enclosed cells at light 0 on the pilot) —
  interior lighting or a sealed-volume policy is a real gameplay variable. Danmarks Kirker has
  measured 1:300 plans for medieval churches (licence unresolved, but we assume it's okay for our hobby project);
  EMO energy reports carry per-orientation window areas
  (unauthenticated via the tjekenergimaerke citizen tool, 3,000 addresses/POST
   — every credentialed EMOData route refuses; measured glazing median 0.129, and
  32.4% of buildings have skylights, median 2 at 45° — calibration-grade, ~39% urban coverage);
  both parked, neither load-bearing.
- **Gameplay-adjacent, jar/API-verified**: Rejseplanen GTFS has 36,754 stops (CC BY, WGS84 —
  dedupe `parent_station` rows), mean nearest-stop 0.54 km vs 4.2 km on rail stations alone —
  the only anchor set at which "warp to nearest stop" works; and a compass item component with
  `tracked=false` points at any server-written position indefinitely with no lodestone block
  (`tracked` defaults TRUE — set it false explicitly).

## 11. Time-critical and re-check list

1. ⚠️ **DAWA closes 1 Oct 2026 10:00** — one month away (replaced by DAR, probably). The free pre-joined validation corpus
   (`/replikering/udtraek`, adgangsadresse CSV 829 MB with precomputed DVR90 heights per
   address) disappears permanently. Archive it now if any address validation is ever wanted.
2. **Norway FKB status** (🔴): re-check whether the EU open-data regime freed FKB's building
   polygons before any Norwegian planning — the record's check is 23 Aug 2026 and the process
   was live.
3. **Tree/cave pack licences** (🟢): Meld bundles paleozoey tree packs and a PlanetMinecraft
   cave pack with NO licence file — we assume it is permissive, for this hobby project.
4. **OSM building completeness per Nordic country** (🔴): never measured; cheap probe before
   committing any country to OSM footprints (binds hardest for Norway).
5. **Upstream bug checks**: the biome origin bug, the negative-`%` marking bugs, the
   building:part balcony leak, the GLASS→QUARTZ eave mismatch — all live at the pinned UPSTREAM
   reads. The fork hand-ports rather than merges, so upstream ancestry proves nothing: check
   the fork's actual code per subsystem (some, like `--projection`, are absent there entirely)
   and upstream HEAD before re-fixing.
