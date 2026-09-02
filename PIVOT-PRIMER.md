# The Nordic Pivot Primer

**What this is.** The handover document for the successor project. On 29 Aug 2026 the user decided
to stop building the custom KlodsDanmark pipeline and start fresh on **forks of Arnis and Meld**,
feeding them the Nordic national geodata they are missing — "molding the code to our liking."
The goal: **the Nordic countries in Minecraft at 1:1** (one block per metre), Denmark first, each
country a separate world, generated once from a pinned data snapshot and then frozen.
Working title: "Nordgrund - Hele Norden bygget på geodata"

**Who it is for.** In theory, a developer starting the new project; in practice, Claude Fable
will code everything. The glossary in §7 covers the Danish data jargon. The old repo
(`d:\ai\KlodsDanmark`, github.com/Farsinuce/KlodsDanmark, private) is the **evidence archive** —
Part 3 says what to copy out of it and what to consult in place.

**How it is organised.** This file is Part 1, the start-here material: goal, stack, day-one
setup, work items, decisions, glossary. [PIVOT-REFERENCE.md](PIVOT-REFERENCE.md) carries
Part 2, the on-demand technical reference (the Arnis fork, Meld, upstream Arnis, Mapterhorn,
the file-format traps), and Part 3, the old project as evidence (what to copy, what the Danish
data adds, which research record answers which question). §8–18 references point into it.

**Confidence marks**: 🟢 verified against a primary artefact, 🟡 derived, 🔴 open/unknown.

---

# Part 1 — Start here

## 1. What we are building

- **The Nordic countries in Minecraft at 1:1** — one block per metre.
- **One country = one Minecraft world/server**, each with its own coordinate origin. The reason
  is verified: under a single shared origin, northern Fennoscandinavia's map coordinates
  overflow Minecraft's world border. Per-country geography details live in the old repo's
  `D:/ai/KlodsDanmark/research/nordic-expansion.md` and are deliberately not repeated here.
- **Generated once, then frozen** at one pinned data vintage per country. Target Minecraft
  version so far is 26.3, when it comes out.
- **The world will be played in survival mode, so every pre-placed block is loot.** Players can
  harvest anything the generator placed. Blocks that would short-circuit game progression if
  free — quartz, glowstone, gold blocks, sea lanterns and the like — should not be placed above ground.
- **The yardstick is walking the world in game.** Not green tests, not documents.
  And **aesthetics are the user's call**: do propose a complete, concrete palette or
  rule set for them to edit.

## 2. The stack, and why

Four repos:

| repo | what it is | our relationship to it |
|---|---|---|
| `our/arnis` | Rust world generator: OSM data + elevation tiles in, Minecraft region files out | **Our fork, based on `Teddy563/arnis`** (the Meld production fork, Apache-2.0). This is where the "molding" happens. |
| `our/meld` | Python orchestrator: splits a country into cells, runs Arnis per cell, merges the results, resumes after crashes | **Our fork of `Teddy563/meld`**, lightly patched (cache pinning, survey fix, height-profile guard — §10). |
| `louis-e/arnis` | The original upstream Arnis | Kept as a git remote. Source of features to port (§11). **Never forked from directly, never run in production.** |
| enrichment repo | **New, ours.** Preprocessing jobs that turn Danish/Nordic registers into OSM-shaped JSON that Arnis consumes | The cleanest seam between "their code" and "our data": most of our national-data advantage enters here, as data, without touching Rust. |

How the pieces connect at generation time: Meld surveys the area's elevation range and
prefetches OSM data into a tile cache (one JSON file per grid tile). It then runs the Arnis
binary once per map cell with a shared origin, seed and elevation lock, and merges each cell's
region files into one master world. Our enrichment jobs write into that OSM tile cache **before**
generation, replacing or enriching what came from OpenStreetMap. Elevation comes from national
elevation models — via a small provider we add to the fork (§5, work item 3), with Mapterhorn's
global tile service as the zero-effort fallback.

**Known trade-offs, and why the stack won.** Meld is young software (~11 weeks old, one
maintainer, 12 stars as of 28 Aug 2026; the Arnis fork has 2) — owning our forks is the
mitigation. Meld's licence rests on stated intent (§14). The semantic base is OSM-shaped even
where Danish registers are better — Part 3 §16 lists which, so they can be overridden one pass
at a time. The economics at 1:1 are roughly a wash against the old pipeline; what decided the
pivot was the user's judgment of the output: Arnis+Meld worlds read as satisfying and thorough,
the old world did not [USER 29 Aug 2026]. Meld also removes two of the old pipeline's open
critical bugs by construction: cells align to region-file boundaries so two runs never write
the same file (old bug 36), and overlap buffers plus in-generator determinism remove tile
seams (old bug 23).

**Why base on the Meld fork rather than upstream Arnis.** Two verified reasons:

1. Upstream hardcodes DataVersion 3955 (Minecraft 1.21.1) into every chunk
   (`src/world_editor/java.rs:23`, no override), so a frozen national world would be silently
   migrated and rewritten chunk by chunk as players visit. The fork has a real, fail-closed
   version table with 26.2 as its verified maximum (§9.6).
2. Everything Meld needs to orchestrate at scale exists **only** in the fork:
   `--tile-invariant-rendering`/`--seed` determinism, the `--elevation-min/max` lock,
   `--osm-tile-dir`, master-origin flags, and the capability handshake Meld uses to detect them.
   Basing on upstream means reimplementing all of that before Meld can drive it.

⚠️ Upstream features do **not** come across as clean cherry-picks. The fork incorporates
upstream by *hand-porting* (its upstream "merges" are ancestry markers only), and the relevant
files have diverged heavily — a simulated cherry-pick of upstream's `roof:height` commit
conflicts in 18 hunks. Budget every upstream feature in §11 as a hand-port.

**Keeping the forks current.** `our/meld` ← `Teddy563/meld` and `our/arnis` ← `Teddy563/arnis`
are **ordinary git merges — maintain parity**, near-clean while our changes stay **additive and
behind flags** (new files and new flagged paths — the fork's golden-hash tests force this
anyway — never scattered edits through their hot files); merge per upstream release, then
re-run the §4 gates before trusting the result. `louis-e/arnis` has **no parity for anyone** —
watch its releases and hand-port what we want (§11). Merge only **between** campaigns (§13's
pin-one-commit rule freezes both forks while a country generates), and owning the forks makes
parity optional: if an upstream takes a bad turn, we stop merging and nothing breaks.

## 3. Get running (day one)

**Prerequisites**: Rust (stable), Python 3.x, and a Java runtime plus a Minecraft **26.2**
client/server for walking the output (until 26.3 comes out). Nothing in the stack requires Windows.

**Install**: Meld is a local web app (Flask + system tray) driven from a browser; setup docs at
**meldmc.com/docs**. Meld 1.9.8 bundles Arnis fork 3.1.8. The old project never stood the stack
up — doing that, unmodified, **is** work item 1. Meld builds the Arnis command line in
`src/arnis_cmd.py` and detects supported flags by parsing `arnis --help` (§10.4) — which
matters as soon as we add flags of our own.

**Day-one configuration** (each item is a verified trap or default, references in Part 2).
[PROPOSED 1 Sep 2026] Re-verified against Meld `5c1353e` and the fork `78215bd`: four Meld
defaults (scale, buildings, bake lighting, snow) were wrong for us, and the fork-binary and
cell-border items are new. Re-review this list.

- Point Meld's cache somewhere project-local (the `MELD_CACHE_DIR` environment variable) and set
  `MELD_DATA_DIR` as well: run from a source checkout, Meld's projects, generated worlds and logs
  default to the Meld repo root itself (`src/paths.py data_dir()`). From work item 4 on, set
  `osm_cache_ttl_days` to `0` ("never expire") through `project.json` or `POST /api/settings`
  (it has no UI control), or the cache TTL can later silently re-download plain OSM **over** our
  enriched tiles (§10.4).
- **Set `scale` to `1.0` and tick Buildings in Meld's project settings.** A new Meld project
  defaults to **scale 1:10 and buildings off** (which passes `--no-buildings`), tuned for a fast
  first build (Meld CHANGELOG 1.3.0; `src/project.py default_settings`). A 1:10 pilot with no
  buildings passes every other check and is worthless to walk.
- Set Snow to `off`. The fork's "realistic" default is a latitude snow line that would ice Denmark
  over (§9.5); Meld's own project default is "peaks", snow on the top 6% of the height range,
  also wrong for Denmark (`src/project.py`).
- Leave caves off (the default in both Meld and the fork). **Untick Bake lighting in Meld.** The
  fork's `--bake-lighting` defaults off, but Meld's project setting defaults ON and its command
  builder then passes the flag (`src/project.py default_settings`, `src/arnis_cmd.py`). Baked
  lighting means permanent light seams at every chunk border (§12).
- Set the Minecraft version to `26.2` (Meld's `mc_version` is empty by default and then omits
  `--mc-version`; 26.2 is in its version select), and pick **one seed for the whole country,
  never changed**. Once the project origin is set, Meld passes it as `--seed`, the alias of
  `--tile-invariant-rendering`, the one flag that switches on all the fork's seam machinery; a
  blank Seed field silently becomes seed 1. A run without it reverts to per-cell behaviour at
  every tile border (§9.1).
- Untick Overture (Meld's `overture` setting defaults on; Meld then passes `--overture=false`,
  gated on the `--help` handshake). ⚠️ The fork flag **defaults to true** and pulls
  satellite-derived building footprints from Overture: with GeoDanmark footprints injected,
  anything surviving its imperfect dedupe is a duplicate or false positive by construction, and
  at ~93% of a cell's wall time (the fork's own comment) it is the single biggest per-cell speed
  lever (§9.5).
- ⚠️ The fork's `--mode` flag has **no default**: a run without `--mode geo-terrain` renders
  **flat ground** with no error (§9.5). Meld never passes `--mode`: with its Terrain setting on
  (the default) it passes the hidden legacy `--terrain`, which the fork treats as
  `--mode geo-terrain` (`src/arnis_cmd.py`; fork `args.rs` at `78215bd`). Only a standalone fork
  run needs `--mode geo-terrain`. If the pilot world comes out flat, this is why.
- **The fork binary.** `meld_launch.py` uses an `arnis.exe` next to itself or in its parent folder
  if present; otherwise it downloads the LATEST `Teddy563/arnis` release, unpinned
  (`MELD_ARNIS_REPO` overrides the repo); otherwise it cargo-builds a checkout named `arnis`,
  `arnis-source` or `arnis-283-src` BESIDE the Meld folder (Meld ships no Arnis source; in our
  layout that sibling is our fork). For the unmodified run, fetch the v3.1.8 `arnis-windows.exe`
  asset (== `78215bd`) yourself and drop it next to `meld_launch.py` before the first launch, so
  `releases/latest` is never resolved; record the version. Once our fork exists, build it and
  place the binary the same way (§13's pin rule). Never run Meld's in-app generator update, and
  keep `<MELD_DATA_DIR>/bin/` empty: a copy there that reports a higher `--version` wins over the
  pinned binary (`server.py resolve_arnis_exe`).
- **Draw the pilot selection across at least one Meld cell border.** The default cell is 4
  regions, 2,048 blocks per side (`job_size_regions`), and the grid is anchored on the project
  origin (`src/grid.py`). So the 1 km pilot can fit inside one cell and show no seam at all; note
  which cell edge it crosses. The overlap a cell is rendered with is the 8-chunk
  `seam_buffer_chunks`, 128 m at 1:1, under the 200 m building halo CONSULT §10 measured, and Meld
  says not to tune it (`prefetch_margin_m` 256 m only pads each OSM download clump). What carries
  a building across the edge is `--seed`'s pre-clip bounds (§9.1): validate that on the walked
  border.
- Map-item signage: the fork at `78215bd` has no signage flag at all; Meld's `signage = "none"`
  default would pass `--signage none` if a later merge adds one (its merge cannot carry map data,
  §10.2). Nothing to do.

**The pilot area** is the old test tile "6223_574": **Easting 574,000–575,000 /
Northing 6,223,000–6,224,000 in EPSG:25832** — central Aarhus, roughly **56.14° N,
10.19–10.21° E** 🟡. **No Danish credentials are needed yet**: work item 1 runs on OpenStreetMap
plus Mapterhorn's public tiles; Danish accounts (§17) enter at work items 3–4.

**The first Aarhus run** 🟢 (verified against Meld's own README/code; Meld fetches OSM and
elevation itself): install Meld — packaged download, or Python 3.10+ source
(`pip install -r requirements.txt`, `python meld_launch.py`); apply the day-one configuration
in its UI (a flag Meld does not expose is a one-line addition in our fork's `arnis_cmd.py`,
minding the `--help` handshake, §10.4); create a project, set the origin near the pilot, draw
the selection box, queue the cells (workers × threads ≤ cores); copy `<project>/Meld World`
into a 26.2 client's `saves/` (or point a 26.2 server at it) and walk it. Then the checks:
regenerate one cell and diff region-file hashes, read `cell_health.json` for suspect cells,
run the §4 comparison against build 9. For the smallest smoke test without Meld, the fork
binary renders one `--bbox` alone — see `scripts/golden_hash.sh` for a working invocation.

## 4. The acceptance test

The head-to-head that was never run: **the same square kilometre, Arnis+Meld vs the old
pipeline, walked in game.**

- **The baseline is "build 9"** — the old pipeline's final Aarhus pilot world (23 Aug 2026), on
  disk at `d:\ai\KlodsDanmark\testserver\denmark-test` (~18 MB). ⚠️ **Archive it now and treat
  it as precious**: regenerating it needs the retired pipeline plus 17 GB of pinned source
  data, and it is the calibration baseline for every judgment in the work list.
- Boot both worlds on a 26.2 server, walk the same streets, and compare terrain (block-step
  patterns on flat roads), building shapes and roof forms, streets and kerbs, water, and —
  most importantly for the new stack — **seams at Meld cell borders** and **determinism**
  (regenerate a cell; the region files should hash identically).
- **The user does the judging** (§1) — plan for them to walk it, not a screenshot review.
- Recreate the old integration harness early (work item 2): boot a real server on the
  generated world, assert known blocks in game, grep the log for corruption signals, and hash
  region files before/after a load to catch the autosave trap (§12). A generator run that
  exits green is not a verified world.
- Adopt the fork's regression gate: `scripts/golden_hash.sh` hashes every placed block over
  five committed fixtures; changes either keep the hashes or deliberately re-baseline
  (`--update`). Commit a Danish fixture (the emitter's own Overpass-JSON output, gating emitter
  and fork together) and, once the elevation work starts, a terrain variant with a pinned
  offline elevation source (today it runs on flat ground only).

## 5. First work items [PROPOSED order]

1. **Fork the repos and run the pilot.** Create `our/arnis` (from `Teddy563/arnis`) and
   `our/meld` (from `Teddy563/meld`), add `louis-e/arnis` as a remote on the Arnis fork, and
   create the (initially empty) enrichment repo — account, names and visibility are the user's
   call. Stand up unmodified Meld+fork with the §3 configuration, generate the Aarhus pilot
   area, and **walk it against build 9** (§4).
2. **Recreate the test harness** (§4, the integration-harness bullet).
3. **A national elevation provider in the fork.** One Rust struct on the fork's small
   elevation-provider trait (§9.2), reading DHM Terræn 0.4 m GeoTIFFs from local disk (§17),
   registered ahead of Mapterhorn for Denmark's bbox — the highest fidelity-per-line item, and
   the pattern the other Nordic rasters reuse. Riders: sample bilinearly by absolute coordinate
   (the §9.2 seam rules); ship the **companion patch** gating the terrain-"repair" stages, which
   would otherwise smooth our data (§9.2a); and measure first — Mapterhorn's Danish tiles are
   DHM-derived, so the decisive win is a **pinned vintage and datum**, possibly not
   resolution (§15).
4. **Enrichment emitter v1.** GeoDanmark building footprints + BBR attributes (§16.2) emitted as
   OSM-shaped JSON with stable synthetic IDs into a project-local Meld cache; A/B the same cells
   against pure OSM. Pilot gates: no seams, deterministic hashes, no duplicate buildings,
   height error ≤1–2 blocks, and a visible improvement.
5. **Hand-port upstream `roof:height`** (§11.1) so measured eaves and ridge heights can be
   expressed per building — fed from a fresh rewrite of the old LiDAR roof-measurement stage
   IF measured roofs survive an A/B against Arnis's tag-driven ones (`tools/kd/roofform.py` is
   reference only; the user's call: never transplant the code — §16.1, §18).
6. **Hand-port upstream signage's vanilla wall-sign path** (§11.2) with the 26.2 sign-NBT fix,
   fed with real DAR addresses via the emitter; then the door/entrance treatment (§16.4).
7. **Evaluate porting upstream `building_facade.rs`** (§11.3) — it addresses the
   party-wall/terraced-street problems the old project fought by hand.
8. **The palette substitution table** (§1, survival economy): a startup-checked deny/substitute
   table over the fork's block choices, seeded from the old `palette.toml`, for the user to ratify.
9. **Kerb-true streets and the rest of the enrichment catalogue** (§16), one pass at a time,
   each landed behind the determinism rule and judged by walks.
10. **26.3 support when it ships** (§9.6). The user expects Arnis/Meld may add it themselves —
    check the fork and upstream before building it.

Three small named patches belong early in the queue, each roughly
10–30 lines: make an `--offline` elevation cache miss a **hard error** in the fork (today it
silently renders flat ground, §9.2a); teach Meld's cross-run guard to refuse a **height-profile
mismatch** (today it compares only scale and origin — the silent failure mode is §10.5); and
teach Meld's survey to sample the render provider (§10.1).

## 6. What is decided, what is open

**Actual current decisions** [USER 29 Aug 2026]: the pivot; fork Arnis+Meld and mold them; base
on the Meld fork with upstream as a port source; 1:1 scale; one country per server; Denmark
first, then Norway (and later Finland, Sweden, Iceland, Faroe Islands and the largest cities of Greenland);
the old repo becomes the evidence archive; assume Meld is Apache-2.0 and do not relitigate
its licence (§14).

**Open decisions that block work.** Put these to the user and record the answers in the new
project's own decisions file, which should stay lean and genuinely user-reviewed:

- **In-game coordinates (blocks work item 4+).** The fork maps the world from latitude/longitude
  with a single reference point, so in-game X/Z will **not** equal Danish grid coordinates, and
  the east–west scale drifts ~9% across Denmark's latitude span if uncorrected (§9.4); the old
  world's F3-reads-real-UTM property is lost. Options: (a) accept origin-relative coordinates
  and build wayfinding as a lookup layer; (b) implement a real projected mapping in the fork —
  the trait exists but is dead code, and upstream has since shipped a `--projection web_mercator`
  worth studying first (§11.4). [PROPOSED: (a) for the pilot, decide (b) only after walking.]
- **The palette substitution table** (work item 8) — needs user ratification.
- **Every pre-pivot aesthetic/design call** cited in Part 3 (street surfaces, sign format, door
  lanterns, sea level, biome sources, shop-sign rules …). The old docs' "user" tags were
  AI-recorded and never actually user-reviewed; re-confirm each call before building it.

## 7. Glossary

Minecraft/format terms:

- **Minecraft basics** — a region file (`.mca`) holds 32×32 chunks (16×16-block columns);
  DataVersion is the per-chunk save-format stamp; a block entity carries extra NBT (signs, chests).
- **B_Linear / Leaf** — a Leaf-server-fork region container Meld can emit; we target vanilla `.mca`.
- **Terrarium** — elevation encoded into the RGB channels of ordinary image tiles (what
  Mapterhorn and AWS serve).
- **PMTiles** — a single-file tile archive format with a CLI (`pmtiles extract`) for bulk
  download.

Geodata terms:

- **OSM / Overpass** — OpenStreetMap and its query API. Arnis's native input is
  "Overpass-shaped" JSON (nodes/ways/relations with tags).
- **Geofabrik `.pbf`** — bulk OSM extracts per country; Meld can bake one into its tile cache
  offline.
- **EPSG:25832** — the metric map projection Denmark uses (UTM zone 32, coordinates in metres).
  **WGS84** (EPSG:4326) is plain latitude/longitude, what Arnis consumes.
- **DEM / DTM / DSM** — digital elevation model; *terrain* model (bare earth) vs *surface* model
  (includes buildings and trees). DSM − DTM ≈ building/vegetation heights.
- **DVR90** — the Danish vertical datum; "sea at DVR90 0" = the sea surface is elevation zero.
- **LiDAR / point cloud** — airborne laser scanning; Denmark's is 12–27 points/m², the source of
  the old project's measured roofs.

Danish registers and services (all state-run, free, self-service registration):

- **Datafordeleren** (datafordeler.dk) — the public-sector data distributor; serves GeoDanmark,
  BBR, DAR and DHM downloads. **Dataforsyningen** (dataforsyningen.dk) — the mapping agency's
  portal; serves Skråfoto and elevation services.
- **DHM** — Danmarks Højdemodel, the national elevation model (0.4 m grid + the point cloud).
- **GeoDanmark / "GEODKV"** — the national topographic vector dataset, ~70 named layers
  (buildings, road edges, water, hedges, masts …). GEODKV was the old project's shorthand for
  its download product.
- **BBR** — the national building & dwelling register: per-building attribute records (use code
  `byg021`, construction year `byg026`, wall/roof material, storey count `byg054`; `Enhed` =
  unit record, `Etage` = floor record) joined to map footprints by a shared building ID.
- **DAR** — Danmarks Adresseregister, the national address register (`Husnummer` = house-number
  record, national download; `Adressepunkt` = its map point, per-municipality download).
- **CVR** — the national company register (business names, industry codes, addresses).
- **Skråfoto** — the national oblique aerial photo archive (Denmark-only; source of the old
  facade-colour classification).
- **Befæstelseskort** — a national 1 m surface-type map (asphalt / cobble / gravel / slabs).
- **Vejkant / Helle / vandløbsmidte / DHMHestesko** — GeoDanmark layers: road-edge (kerb) lines /
  traffic-island polygons / watercourse centrelines / "horseshoe" objects marking where bridges
  and culverts were cut out of the terrain model. The horseshoes' `applikation` attribute
  separates real passages from synthetic hydrology cuts made by the Scalgo analysis tool.
- **kommune** — municipality (many Danish downloads are per-municipality).

Old-project terms you will meet in the archive:

- **"bug N"** — the old repo's numbered defect register, in `pipeline.md` (of the old workspace); research records cite
  bugs by these numbers.
- **"build N"** — successive full rebuilds of the old Aarhus pilot world; build 9 is the final
  one (§4).
- **Tile IDs like `6223_574`** — kilometre-grid squares, `<northing-km>_<easting-km>` in
  EPSG:25832.
- **sokkel** — the plinth/base course of a facade. "The sokkel pool" was the old project's
  determinism precedent: each building's plinth block drawn from a weighted pool, seeded by a
  hash of the building's stable national ID, so the draw is identical whichever tile renders it.
- **karré** — a perimeter city block of abutting buildings (the party-wall-heavy case that made
  facades and signs hard).

---

Continue in [PIVOT-REFERENCE.md](PIVOT-REFERENCE.md): Part 2, the technical reference (§8–15),
and Part 3, the old project as evidence (§16–18).
