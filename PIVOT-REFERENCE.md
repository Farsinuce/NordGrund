# The Nordic Pivot Reference

**What this is.** The technical-reference companion to [PIVOT-PRIMER.md](PIVOT-PRIMER.md):
Part 2 is verified facts about the Arnis fork, Meld, upstream Arnis, Mapterhorn and the
Minecraft format traps; Part 3 reads the old project as evidence. Read on demand — the primer
is the place to start. §1–7 references point into the primer.

**Confidence marks**: 🟢 verified against a primary artefact, 🟡 derived, 🔴 open/unknown.

---

# Part 2 — Technical reference

Everything here was verified 29 Aug 2026 against each repo's then-current HEAD (even though some of the original,
deprecated documentation from the old project might have been wrong). Record the exact commits
when the forks are created — §13's pin-one-commit rule needs them anyway.
File paths are relative to each repo.

## 8. Verified facts: what matters most

The three highest-leverage technical facts, up front:

1. **Adding a national elevation source is deliberately easy** — a Danish 0.4 m GeoTIFF
   provider is one struct plus one registration line against a small trait (§9.2).
2. **True 1:1 vertical mapping already works**: with scale 1, no vertical exaggeration and the
   elevation lock, in-game Y = real elevation in metres plus a constant offset (§9.3).
3. **The determinism machinery is the general solution to tile seams**: key every random or
   fitted decision on stable feature IDs and world coordinates, never tile-local state (§9.1).

## 9. The Arnis fork (`Teddy563/arnis`, Apache-2.0)

This is the Meld production fork (`src/meld_telemetry.rs`; "Required by external schedulers
(e.g. Meld)" in the flag docs, `args.rs:349-350`). Its README's own framing: "Every fork flag is
purely additive. Omit them and the binary behaves exactly like upstream."

### 9.1 Determinism machinery

`--tile-invariant-rendering [SEED]` (alias `--seed`, `args.rs:364-368`): building decisions
read *pre-clip* bounds from the unclipped way, so a building straddling two cells computes the
same answer in both; every salted random stream is seeded from
`element_id ^ rotate(salt) ^ rotate(global_seed)` (`src/deterministic_rng.rs:59-61`), and
per-block streams key on world coordinates `((x<<32)|z) ^ element_id` (`:74-79`). The rule to
preserve in everything we add: **anything stochastic or fitted must key on stable feature IDs
or world coordinates.**

Everything seam-critical hangs off this one flag: pre-clip building metrics, position-seeded
tree/scatter placement, the cave engine's noise seed, and the continuous per-chunk biome
latitude (fork-only, `java.rs:307-326` — upstream gives every chunk the run's centre latitude,
a visible grass-colour step at cell borders). The seed is set once per process and a
conflicting re-set is refused — pin one value per country. ⚠️ Regardless of the seed, the
fork's built-in biome table sends tree-covered land above 55° latitude to (potentially) **taiga**
(`biome.rs:66-72`) — most of Denmark and all of the rest of the North — so a Nordic biome
override is needed whatever else is decided about biomes.

### 9.2 Elevation subsystem

Providers are ordered finest-first by `select_provider` (`src/elevation/selector.rs:30-56`):
USGS 3DEP 1 m, IGN France 1 m, IGN Spain 5 m, Japan GSI 5 m, then **Mapterhorn as the global
default**; AWS Terrarium (~30 m) is reached only via `--aws-only-elevation` or as a fetch-time
failure fallback. **No local-file/GeoTIFF provider exists yet** — but the trait
(`src/elevation/provider.rs:14-43`) is small: `name()`, `coverage_bboxes()` (in lat/lon),
`native_resolution_m()`, `accepts()`, and `fetch_raw(bbox, w, h) → RawElevationGrid`
(`heights_meters: Vec<Vec<f64>>`, NaN = missing). The `tiff` and `image` crates are already
dependencies (`Cargo.toml:41,61`), and the helpers a Danish provider would reuse exist in two
files: bilinear sampling in `fixed_tile.rs` (`sample_tile_bilinear`, :257) and the GeoTIFF
float32 decoder in `providers/regional.rs` (`decode_geotiff_f32`, :324).

Three verified rules for writing that provider:

- **Sample bilinearly.** Build on `fixed_tile.rs`'s sampling, not the `regional.rs` scaffold —
  the latter resamples nearest-neighbour (`regional.rs:386`), which would alias 0.4 m data onto
  the 1 m grid.
- **Sample by absolute coordinate, independent of the requested bbox** — the same coordinate
  must return the same height whichever cell asked. That, plus one provider for every cell, is
  what actually prevents elevation seams. A trait provider has **no** Web-Mercator grid
  requirement (that constraint applies only to the cache-injection shortcut below).
- **Don't hand the fork a country-sized bbox.** The elevation grid might be capped at 16384² per
  fetch and silently degrades to bilinear upsampling above it (`mod.rs:83, :124-125`) — a huge
  single box yields a plausible-looking low-resolution world, not an error. Meld cells are the
  operating mode.

**No zoom configuration is needed for Denmark**: the provider picks **z16 (~0.65 m/px) for all
of Denmark at 1:1** from grid cell size (`mapterhorn.rs:130-152`; z17 only at scale > 1). The
`ARNIS_ELEV_ZOOM` env var Meld sets caps only the coarse AWS fallback path (≤15, lower never
raise) — irrelevant to the default provider.

⚠️ **`--offline` (alias `--elevation-cache-only`) is not fail-closed**: a cache miss NaN-fills
and degenerates to flat ground (`mapterhorn.rs:529-539`); only Meld's post-run
`cell_health.json` marks the cell suspect (`"elevation-not-baked"`), with no fail or retry.
Frozen-build discipline: pre-bake (Meld's bake route drives `--prewarm-elevation`), verify
coverage, run `--offline`, treat every suspect cell as failed — the hard-error patch is on the
§5 list. Two more cache hazards: a fresh `z…​.missing` marker makes the sampler silently write
ocean (height 0) for that tile, and standalone (non-Meld) fork runs age out cache files older
than 7 days.

### 9.2a The terrain-"repair" pipeline — the gate is a required patch

Between a provider's `fetch_raw` and the final blocks, the fork runs cleanup stages.
**None of them read provider identity or resolution**, so a Danish 0.4 m provider's data would
pass through all of them today:

- `repair_terrain_anomalies` (`postprocess.rs:22-125`) — unconditional 5×5 median-replace of
  cells deviating >6 m *and* >3×MAD from their neighbours, up to 10 passes. Near-harmless to
  Danish micro-relief (a kerb or dike can never reach 6 m) but it erodes sheer >6 m edges such
  as tall quay walls, and it is the dominant postprocess CPU cost.
- The land-cover repair (on by default, steered by ESA WorldCover 10 m) adds further
  stages. A **σ = 30 m Gaussian over built-up areas** (`postprocess.rs:843-934`): at 1 m cells
  that is a 30-cell blur, and it flattens railway cuttings, ramps and urban micro-relief. A
  **coastal pull** (`postprocess.rs:739-823`): every land cell within 25 m of water and ≤15 m
  above it is ramped down toward water level, so harbour fronts become slopes. And
  `level_water_surfaces` overwrites water-surface heights from ESA components, colliding with
  any sea-at-datum-zero policy of ours.
- `fill_nan_values` and `scale_to_minecraft` live in the same file and are **load-bearing;
  keep them** — disabling `postprocess.rs` wholesale would break the vertical mapping itself.
- The whole-grid IQR outlier filter is already **skipped in Meld master-origin mode**
  (`mod.rs:264-272` — per-cell reject bands would seam). That skip is the in-tree precedent
  and template for our gate: a provider-trust flag over the three stages above, plus an
  explicit policy call on `level_water_surfaces`. The fork treats postprocess output as
  hash-stable (golden tests), so the gate must be a new flagged path, not an edit in place.
- After all of it, the final per-block height is a per-column round with **no neighbour
  de-speckle** (`ground.rs:758-762`) — the exact artefact class of the old project's bug 37
  (lone one-block steps on flat roads). The fork's own remedy is `--road-grade` (default
  **off**, opt-in via Meld settings) — try it in the pilot, and decide it before the first
  production cell (§10.4).

**The cache-injection alternative (zero Rust).** The verified recipe: write
`<ARNIS_CACHE_ROOT>/arnis-tile-cache/mapterhorn/z{z}_x{x}_y{y}.webp` as 512×512 **genuinely
lossless-WebP** Terrarium tiles, at exactly the zoom the fork will pick (z16 for Denmark at
1:1); decoding is keyed on the file extension, so a renamed PNG fails validation and is
deleted. ⚠️ Meld's pack-folder import also ingests `z*_x*_y*.png` elevation tiles, but into
the **AWS** cache, capped at z15 — coarser than the DHM; don't use that variant. Verdict: the
provider is the clean path; injection is at most a bring-up experiment.

### 9.3 Vertical mapping — real metres

`scale_to_minecraft` (`src/elevation/postprocess.rs:1238-1348`) maps
`mc_y = ground_level + (h − min)/range × scaled_range`, and honours a global elevation-range
override (`:1252-1256`) — exactly Meld's cross-cell lock. So
`--scale 1.0 --vertical-exaggeration 1.0 --elevation-min M --elevation-max H --ground-level G`
gives **Y = h + (G − M)**, slope exactly 1.0, whenever the range fits (there is a fixed 15-block
reserve below the world top; outputs clamp to it). `ground_level` defaults to −62
(`args.rs:137-138`).

Extended world height beyond vanilla is supported: `--disable-height-limit` plus a
version-aware datapack, which Meld's merge carries correctly. The engine's absolute window is
fixed at Y −2032..2031, verified both in `src/height_profile.rs:29-35` and in the real 26.2
server jar. Vanilla −64..319 suffices for Danish terrain — though the tallest register
structure, a 320.47 m telemast, is one block over (clamp it counted, or keep headroom);
per-country vertical planning lives in the old repo's `research/nordic-expansion.md`. Countries, whose highest peak exceeds 2031 m, must
have a lower Y level foundation, and having their sea level lowered:

**Highest point in each country**

| Rank | Country | Summit | Height | Modified Sea Y level |
|---|---|---|---|---|
| 1 | Norway | Galdhøpiggen (Jotunheimen) | 2,469 m | -500 m |
| 2 | Iceland | Hvannadalshnúkur (Öræfajökull) | 2,110 m | -100 m |
| 3 | Sweden | Kebnekaise, north peak | 2,097 m | -100 m |
| 4 | Finland | unnamed point on the slope of Halti | 1,324 m | 0 m |
| 5 | Denmark | Møllehøj (Ejer Bjerge) | 171 m | 0 m |

### 9.4 Horizontal mapping — the one structural gap

⚠️ The fork maps lat/lon to blocks equirectangularly from a master origin:
`x = (lng − olng) · 111320·cos(origin_lat) · scale`, `z = (olat − lat) · 111320 · scale`, with
the east–west metre-per-degree factor **anchored at the origin latitude by design**
(`src/coordinate_system/transformation.rs:170-190`; duplicated in `src/elevation/mod.rs:91-130`).
Across Denmark's latitude span that is ~9% of east–west stretch between the extremes if
uncorrected (cos-ratio 1.0885). A `Projection` trait and `--projection` arg exist but are
**dead code in this fork** (`src/projection/mod.rs:1-4`, zero callers), so in-game X/Z are
*not* national-grid coordinates — the §6 coordinate decision. Upstream has since shipped a
working `--projection web_mercator` (§11.4); study it before writing anything new.

### 9.5 Flags that matter

All verified in `src/args.rs` at HEAD (focusing on Denmark, first):

| flag | default | note |
|---|---|---|
| `--mode geo-terrain` | ⚠️ **none** | No default: omit `--mode` (and the hidden legacy `--terrain`) and the world renders **flat**, silently. Always pass it. |
| `--snow-mode` | `realistic` (:64-75) | Latitude snow line — **set `off`** or Denmark ices over. |
| `--bake-lighting` | false (:506) | Per-chunk bake for LOD mods; **leave off** — permanent chunk-border light seams (§12). |
| `--caves` | false (:197) | Whole `src/caves/` subsystem incl. GPU carver; leave off for a frozen surface world. |
| `--scale` | 1.0 (:127) | Values outside [0.01, 4.0] are **refused at parse time** (not clamped) (:742-766). |
| `--mc-version` | table default 4440 | Set `26.2` explicitly (§9.6). |
| `--height-headroom` / `--height-underroom` | 32 / **16** (:390-396) | Note the asymmetry. |
| `--osm-tile-dir`, `--osm-tile-z` | — / 11 (:21-26) | Fork-only; how Meld feeds the tile cache. `--file` is the merged-single-JSON alternative. |
| `--elevation-min/max`, `--master-origin-lat/lng` | — | The Meld cross-cell locks. |
| `--overture` | ⚠️ **true** (:274-275) | Satellite-derived Overture footprints, on by default — **set `false`** for a registers-fed build (§3); also ~93% of a cell's wall time. |
| `--road-grade` | off (:500-502) | Slope-limited road profiles — the fork's remedy for the old bug-37 ground-step class (§9.2a); decide before the first production cell. |
| `--aws-only-elevation`, `--regional-elevation-only`, `--offline` (alias `--elevation-cache-only`) | — | ⚠️ `--offline` does **not** fail loudly on a missing elevation tile — NaN-fill toward flat ground; only Meld's post-run `cell_health.json` flags it (§9.2a). `--prewarm-elevation` pre-bakes the tile cache. |
| `--no-buildings` (:263), `--overpass-url`, `--tree-pack DIR` (:40-41) | — | Tree/cave packs are external drop-ins; see §14 licensing. |

### 9.6 Minecraft versions and the writer

`assets/mc_versions.json` is fail-closed: known rows 1.21.4=4189 through **26.2=4903 (the
maximum, verified from a real world's level.dat)**; unknown versions are refused with
instructions to add a verified row (`src/mc_version.rs:129-148, 184-191`); DataVersion is
set-once per process (`java.rs:39-55`). The file's own house rule matches the old project's
doctrine: no value written from memory — only read out of a real generated world or the client
jar.

⚠️ **26.3 is not just a table row**: the writer hardcodes the pre-26.3 chunk palette keys
`Name`/`Properties` (`java.rs:1196-1198`); 26.3 renames them to `id`/`properties` (the old
repo's `anvil.py` carries both as profiles, DataVersion 5009). No 26.3 support exists anywhere
in the fork today. Porting = a verified table row + the writer key switch + re-running the
§12 trap checks against the real 26.3 jar.

### 9.7 Block entities and signs

A real, general block-entity channel exists: `insert_block_entity`
(`src/world_editor/mod.rs:1018`), with coordinate-dedup at serialization built for tile halos
(`java.rs:442-452`). Shipped writers: banners, loot chests, beds. A `set_sign` exists but is
**dead code** (`mod.rs:1257-1318`: `#[allow(dead_code)]`, standing oak sign only, rotation
ignored, zero callers) — and it writes sign text JSON-quoted, which is the wrong form for 26.2
(§11.2). Per-feature sign *text* logic lives upstream (§11.2).

⚠️ **The parser drops `addr:*` at parse time**. Both repos filter every element's tags
through a discard list (28 exact keys + 17 prefixes, `osm_parser.rs:13-63`); upstream carves
two exceptions the fork lacks — `addr:housenumber` (feeding its door-plate signage) and
`start_date` on buildings. The signage port (§11.2) must bring those exceptions along, or DAR
house numbers fed through the emitter are silently discarded before any processor sees them.
Street names are safe — the bare `name` tag is never filtered.

## 10. Meld (`Teddy563/meld`)

### 10.1 What it is

A local Flask web app + tray. `server.py` (7,603 lines) is the orchestrator — generation
queue, per-cell runner, elevation lock, retry/resume. `src/` = 36 modules / 15,383 lines. The
ones that matter:

| module | role |
|---|---|
| `survey.py` | coarse elevation survey of the whole selection → one global (min, max) lock. ⚠️ Hardcodes the AWS Terrarium source (z10), not the provider that renders — teach it to sample our Danish provider when that lands, or the lock comes from the wrong DEM. |
| `prefetch.py` | fetches OSM once per z11 grid tile via `arnis --download-only`; atomic writes; auto-splits Overpass queries above ~30,000 km² (:59-66) |
| `osm_grid.py` | the tile cache naming: `osm_g1_z11_{x}_{y}.json` (`g1` = query-shape version, :47-51) |
| `osm_pack.py` / `geofabrik.py` | bake a local Geofabrik `.pbf` into the cache **offline** |
| `arnis_cmd.py` | builds the Arnis command line (the de-facto planner) + the `arnis_supports()` capability probe |
| `grid.py` / `coords.py` | bbox → region-aligned cells; the single lat/lon→block/region convention |
| `merge.py` | copies whole region files only, never looks inside one (:31-33) |
| `finalcheck.py` + `experimental/headless.py` | post-run hole scan → retry queue; `repair-gaps` |
| `governor.py` / `workers.py` / `occupancy.py` | worker pool; auto-scaling is opt-in, default off |
| `project.py` | persisted per-cell status; `merged` is terminal — the crash/overnight resume path |

### 10.2 Merge safety

Read-only preflight before any mutation: container homogeneity (mixed formats refused), a
coordinate-drift guard, a collision check (`merge.py:95-195`). A refused merge leaves the master
world untouched. It copies `region/`, `poi/`, `entities/`, and datapacks **before** `level.dat`
— and **never `data/`**, so map items cannot survive a merge; Meld accordingly forces map-based
signage off itself (`arnis_cmd.py:346-355`, `project.py:22-26`).

### 10.3 Operations numbers

Defaults 4 workers × 4 threads, hard cap 64 (`workers.py:22`); the maintainer's 24-core bench
put the throughput knee at 8–12 workers; ~559 region-files/min steady state; a 9,408-region
city-scale run ≈ 30 min at 8 workers (`docs/native-blinear-generation.md:199-200`). Per-process
RAM: the fork's own bench band is 1.3–4.9 GB peak (`CHANGELOG.md:399-402`). Java Edition only;
the experimental B_Linear output is irrelevant to us.

### 10.4 Feeding it our data — injection routes and traps

⚠️ There is no overlay/second-tile-dir mechanism; enrichment happens by getting our tiles into
the cache Meld reads. Three routes in: (a) `datapack.import_pack_folder` hardlinks any folder's
`osm_*.json` into the cache (`datapack.py:748`); (b) the offline `.pbf` bake; (c)
`MELD_CACHE_DIR` repoints the whole cache (`paths.py:156`). Verified traps, all with fixes:

1. **The TTL trap**: `osm_cache_ttl_days` (default 365) treats an old-enough tile as stale and
   re-downloads plain OSM **over** it (`prefetch.py:585-593`). Set it to `0` = never expire
   (`prefetch.py:323-334`).
2. **The mtime trap**: the hardlink import preserves the *source* file's timestamp, so an
   injected tile can be born already "stale". Same fix: TTL 0.
3. **The validity check**: a tile must be non-trivial JSON whose last non-whitespace byte is `}`
   or Meld treats it as absent and re-downloads (`prefetch.py:159-168`). Emit well-formed files.
4. **Sidecars (new in 1.9.8)**: Meld writes a binary `.osmbin` sidecar per tile. Harmless — the
   reader re-hashes the `.json` and falls back when it changed, so a replaced tile is never
   shadowed — but the rebuild cost recurs each time we re-emit.
5. **The `--help` handshake**: `arnis_supports()` is a cached grep of `arnis --help`
   (`arnis_cmd.py:151-175`). Any flag we add to our fork must appear in clap's help output, or
   Meld silently never passes it.
6. **Output-changing options**: 1.9.8's "road grading" and "smooth river beds" are opt-in and
   change generated output, so toggling one mid-project makes new cells mismatch earlier ones.
   Fix the option set before the first production cell.

### 10.5 Scale, scripting and the height-profile trap

- **Planning cap**: one planning call is capped at 20,000 cells (`MELD_MAX_PLAN_CELLS`,
  `grid.py:19`). Denmark as a country-outline polygon at the default 4-region cell (a ~2 km
  square) is ~10,000 land cells and fits; a naive full-bbox selection (~39,000 cells) trips
  the cap. Bigger countries need bigger cells (up to 64 regions; stream-to-disk arms itself
  automatically at cell size ≥ 8).
- **Workers**: input 1–64, default 4; the UI warns above a RAM-derived ceiling (~16 at 32 GB,
  32 at 64 GB, 64 at 128 GB) — the save phase is the RAM burst. Don't rebuild Meld's
  scheduling: CPU-budgeted pool, staggered starts, transient-vs-deterministic retry
  classification (drift and collision never retry), `/api/resume` crash recovery, spiral
  build order, an optional adaptive governor.
- **Scripting**: the browser UI is just a client of Meld's local JSON API (origin → settings →
  selection → queue → poll state → resume), so a fully scripted national run is feasible — but
  the API is an undocumented internal surface, so scripting it is engineering we own. The
  shipped `experimental/headless.py` only repairs or re-runs an already-planned project.
- ⚠️ **The height-profile trap**: Meld's cross-run guard compares only scale and origin; the
  master's `level.dat` and the fixed-name extended-height datapack are **first-merge-wins**
  (`merge.py:226-249`). Re-rendering cells with a different `min_y`/`height`/`ground_level`
  silently leaves the vertical range whatever the first merged cell had, and later cells'
  out-of-range content is dropped on load — recoverable (regenerate the offending cells at
  the original settings) but expensive. **Pin the height settings per project and never
  change them after the first merge.** The guard patch is ~10 lines (the sidecar already
  records every height key) and is on the §5 list.
- **Don't hand-pin binary versions in scripts**: the fork's bundle version stamp has twice
  lagged the crate — exactly why Meld probes `--help` rather than trusting a version string.
  Pin *commits* per campaign (§13).

## 11. Upstream Arnis (`louis-e/arnis`) — the porting shelf

Upstream moved past both the fork and the old project's studies. Reminder from §2: these are
**hand-ports**, not cherry-picks.

### 11.1 `roof:height`

Upstream consumes the OSM `roof:height` tag in two places: subtracted from the wall span in
`calculate_building_height` (`buildings.rs:2579-2592`; unit test `:10857-10874`), and as
`RoofConfig.peak_cap` (`:8556-8557`, parsed `:10363-10369`) overriding the heuristic
roof-rise cap. The fork has none of it (grep = 0). With it, a LiDAR **ridge** height goes to
`height=` and the **rise** to `roof:height=` — correct eaves *and* ridge; without it, feeding
ridge heights over-heights every pitched building.

### 11.2 Signage — and the 26.2 sign-NBT fix

Upstream's signage subsystem is one file, `src/element_processing/signage.rs` (2,279 lines):
per-feature text from tags — names (`:147-157`), house numbers (`:202`), street blades,
station boards, memorial plaques. ⚠️ Its *primary* rendering is map-decal item frames, which
cannot survive Meld's merge (§10.2) — **the vanilla wall-sign fallback is the path to port**:
`place_name_sign` (`signage.rs:849`) → `split_lines(text, 15, 4)` (`:860`) →
`place_wall_sign` (`:862`; block-side writer `world_editor/mod.rs:1401-1439`, with
`sign_block_entity` `:1329-1357` writing exactly four `front_text.messages`).

⚠️ Both codebases JSON-quote the message strings (upstream via `json_string()`, `mod.rs:113-126`;
the fork in its dead `set_sign`). The old project verified by live-server readback, Danish
characters intact, that **26.2 wants a bare string as the text component, exactly four
messages** — a small fix at the quoting site when porting. Related trap: sign text must be
written as Java modified UTF-8, or a single non-BMP character (an emoji in a shop name) makes
the server drop the whole chunk (§12).

### 11.3 `building_facade.rs` — porting candidate

Upstream ships a 506-line `FacadePlan` module the fork lacks: it classifies every wall
segment as street-facing / rear / party wall / open from precomputed global inputs, so it is
deterministic by construction. Party-wall detection is exactly what the old pipeline needed
to suppress windows/signs in the 1 m slots between abutting buildings. Evaluate after the
first building passes.

### 11.4 Worth watching upstream

Post-divergence upstream work relevant to us: `--projection web_mercator` ("global projection
for multi-generation worlds" — study before the §6 coordinate decision), country-scale
elevation/ground work, tunnel improvements, water shoreline work, Overture building heights, a
block-palette overhaul, and an interiors overhaul. Watch releases; don't track the branch.

## 12. Writer & format traps (paid for once — do not pay again)

Runtime-verified against real 26.2 servers; full lists in the old repo (`anvil-writer-spec.md`
§6, `lessons-from-factcheck.md`). The ones that survive into an Arnis-based stack:

- **Baked light is forever.** A chunk saved as fully generated with `isLightOn=1` is never
  re-lit (runtime-verified: a deliberately wrong light value survived a load+save round trip).
  The fork's `--bake-lighting` stops propagation hard at the chunk border (`java.rs:897,903`),
  so enabling it means a permanent light seam at every border. Leave it off and let the server
  light on first load. Re-verify all of this on 26.3.
- **Never run `--forceUpgrade` / "Optimize World"** on a generated world — it strips heightmaps
  and light data. This is also why the DataVersion must be right *before* generation (§9.6).
- **The autosave trap**: after any load test, hash the region files before and after — merely
  loading a chunk can dirty and rewrite it, a real corruption channel and the reason the §4
  harness hashes regions.
- **Sign NBT on 26.2**: bare string text components, exactly four `messages` (§11.2); and write
  Java **modified** UTF-8 — with plain UTF-8, the first non-BMP character makes the server drop
  the entire chunk (Danish text is safe, emoji are not).
- Small-but-fatal NBT facts: a light level is a nibble (>15 truncates silently); block-state
  property values are always strings (an integer silently decodes as the default); in packed
  nibble arrays the even index is the LOW nibble.
- **Order statistics turn noise into structure.** Rounding a height per cell with `min`/`max`
  aggregation chases the most extreme sample — how the old ground pass littered flat asphalt
  with lone one-block bumps (old bug 37; read `research/terrain-quantisation.md` before
  touching any ground code). Arnis/Meld's answer is the right shape: median smoothing plus
  per-road cross-section flattening ("road grading", §10.4).
- **Bytes-per-chunk is a tracked metric.** Region files allocate in 4096-byte sectors, so at
  national scale +2 KB/chunk ≈ +50% disk. Old fully-built reference: 2,182 B/chunk. Measure
  after every visual pass.

## 13. Working conventions that survive the pivot

- **Measure, don't assume; state n and the date; prefer the primary artefact** (a real
  level.dat, the deobfuscated jar, one live API request). Mark claims 🟢/🟡/🔴.
- **Fail-closed**: a value the data contains and our tables don't is a named error, never a
  silent default.
- **Every check first asserts the thing it checks was actually produced**; every error branch
  gets constructed input that triggers it.
- **Determinism by construction**: hash on stable feature IDs / world coordinates only (§9.1).
- **Pin one fork commit and one Meld commit per country campaign** and never update mid-run —
  the fork shipped eight releases in the last two weeks of August 2026 alone. Any upgrade means
  re-running the golden-hash gate (§4) and re-baselining deliberately. Parity merges with the
  Teddy563 upstreams happen **between** campaigns (§2).
- **Docs**: lean, and genuinely user-reviewed. Record real user calls the same day with the
  quote; proposals stay [PROPOSED] until ratified — the old project's failure mode was
  AI-recorded "decisions" acquiring false authority.
- **Never junction/symlink data directories into git worktrees, and never `git worktree remove`
  one that contains a link** — this deleted 17 GB of source data (and the hand-labelled facade
  crops, permanently) on 22 Aug 2026. Agents/scripts read data via absolute paths.
- **Precious vs regenerable** — know which is which before any destructive operation. Precious:
  provenance manifests, hand-labelled data, user-ratified tables, research records, **and the
  build-9 baseline world** (§4). Regenerable: newly generated worlds, downloaded samples,
  server runtimes.

## 14. Licensing & distribution

- **Arnis fork: Apache-2.0** — fork, modify, redistribute freely (keep NOTICE/attribution).
- **Meld: no licence file** (GitHub reports none; the only LICENSE in the tree covers a
  vendored Rust subproject, MIT). Its site states "Meld is free and open source, built on the
  open source Arnis generator by louis-e". **[USER 29 Aug 2026]: assume Apache-2.0 in spirit
  and move on — do not relitigate.**
- **OSM: ODbL.** A generated world is a Produced Work — attribute "© OpenStreetMap
  contributors". Our enriched composite *geodata cache* is closer to a derivative database —
  if we ever distribute the cache itself, review ODbL share-alike first 🔴.
- **Danish sources** (DHM, GeoDanmark, BBR/DAR): **CC BY 4.0** — attribution required.
  **Mapterhorn**: © Mapterhorn + per-source credits; Sweden's Lantmäteriet data is CC0.
- ⚠️ **The tree packs and cave pack ship with Meld** (`tree-packs/`, `cave-pack/`; the fork
  only consumes them via `--tree-pack DIR`). **No licence file exists for either**,
  we assume it's permissive for our hobby project, and that's fine.

## 15. Mapterhorn (`mapterhorn.com`) — Nordic elevation through one pipe

A donated, open elevation tile service the fork already uses as its default provider. Its
attribution catalog (148 entries, live-fetched 29 Aug 2026) includes national entries for the
whole North — all eight Nordic rows access_year 2025:

| source | name | res | producer | license |
|---|---|---:|---|---|
| `dk` | Danmarks Højdemodel – Terræn | 0.4 m | Klimadatastyrelsen | CC BY 4.0 |
| `no` | Terrengmodellar (DTM) | 1.0 m | Kartverket | CC BY 4.0 |
| `se` | Markhöjdmodell Nedladdning | 1.0 m | Lantmäteriet | **CC0** |
| `fi` | Elevation model 2 m | 2.0 m | NLS Finland (GeoCubes) | CC BY 4.0 |
| `is` | ÍslandsDEM útgáfa 1.0 | 10.0 m | Natural Science Inst. | CC BY 4.0 |
| `dkfaroe` | DTM hæddarmodell | 10.0 m | Umhvørvisstovan | Open Gov Data |
| `nosvalbard` | S0 Terrengmodell | 20.0 m | Norwegian Polar Inst. | CC BY 4.0 |
| `dkgreenland` | Elevation model Greenland | 2.0 m | Klimadatastyrelsen | CC BY 4.0 |

(`glo30`, Copernicus 30 m, is the global backstop.) ⚠️ The table is what Mapterhorn INGESTED,
not the finest national product — Finland's national open DEM is 1 m and ÍslandsDEM's national
release is 2 m (CONSULT §8); feed finer national products through our own provider. What a
developer needs to know:

- Tiles are Terrarium-encoded 512-px webp, **lossless** (verified on live tiles and in
  Mapterhorn's own writer code); high-zoom quantisation is centimetres — irrelevant at 1 m.
- **Served max zoom varies by region** (live-measured 29 Aug 2026): Denmark z17 (~0.33 m/px),
  Oslo/Stockholm z16, Tromsø z15, Svalbard z13, **Iceland and the Faroes only z12 today**
  despite 10 m sources.
- Bulk download: `pmtiles extract --bbox=…` against the regional archives (Denmark = 4 archives
  of 75–94 GiB, zoom 13–17; they cover more than Denmark, so an extract is much smaller). The
  infra is donated — don't hammer the per-tile endpoint; no rate limits are stated 🔴. The
  catalog's "Raw Download" tarballs are the pre-processed source GeoTIFFs — for Denmark
  essentially DHM Terræn itself.
- 🟡 **Verdict for 1:1 work**: feed the fork raw national DEMs through our own provider (§9.2,
  work item 3); Mapterhorn is the zero-effort fallback and covers countries not wired yet. Its
  Danish z16 tiles are themselves DHM-derived, so the provider's decisive wins are a **pinned
  vintage and an explicit vertical datum** (Terrarium tiles carry no datum metadata) plus
  native 0.4 m sampling — measure the actual difference before assuming it.
- Fetch note: automated fetchers may hit a Cloudflare 403 on the catalog; `curl` (optionally
  with a browser User-Agent) works.

---

# Part 3 — The old project as evidence

## 16 What the Danish data adds that OSM/Arnis cannot

The enrichment catalogue: what the old project measured (evidence paths under
`d:\ai\KlodsDanmark\`) and the route into the new stack. The first four are the identity of the
product. ⚠️ Every "the user chose X" in this section is a **pre-pivot recorded call —
AI-recorded, never actually user-reviewed. Treat it as a proposal and re-confirm before
building** (§6).

1. **Roofs from LiDAR.** (incl. realistic roof colour), Arnis has *no measured building input at all*
   (`research/arnis-roofs.md` — trust it over the older arnis-study); the old pipeline fitted
   per-building LiDAR height fields, idealising 87.3% of building plan area. Route: A/B
   Arnis's tag-driven roofs against measured fitting first; if measured wins, rewrite the
   measurement stage fresh — `tools/kd/roofform.py` is reference only, never transplanted (the
   user's 30 Aug call, §18). Its output reduces to `height=` (ridge) + `roof:height=` (rise) +
   `roof:shape=` per building (§11.1). Adopt free what Arnis does better: dead straight eave
   lines, stairs on every outline cell, one material per roof (arnis-roofs.md §1).
2. **BBR attributes.** Wall/roof material (85% coverage), use code (105-code map), storeys
   (100% of non-sheds) and construction year emit as `building:material`, `roof:material`,
   `building=`, `building:levels`, `start_date`. ⚠️ Join BBR↔footprint on **lowercased** IDs —
   a case mismatch silently drops 23% of the country. ⚠️ The use code types the WHOLE building
   and misses a shop under flats (old bug 43: 16.9% of pilot buildings); the ground-floor
   unit→floor join (100.00%, n=256,267) detects it. Field names carry Danish letters
   (`byg026Opførelsesår` …; list in `data-sources.md`) — strict UTF-8, or match the `bygNNN`
   prefix as the old repo did. In the fork an explicit `height=` beats `building:levels` and
   every heuristic (height ≤1000 m, levels ≤200, "m" suffix parses, negatives refused) — write
   `height` on every footprint, and keep synthetic element IDs below bit 63 (the fork's
   Overture ID marker).
3. **Kerb-true streets.** GeoDanmark's road-edge and traffic-island layers have no OSM
   equivalent, and Arnis explicitly ignores kerbs and never derives sidewalks
   (`research/arnis-roads.md`). Hardest item to express as tags — either emit kerbs as barrier
   ways and mold the road processor, or port the old kerb-stopped flood as a fork feature fed
   by emitter polygons. Also recorded pre-pivot: real street surfaces from Befæstelseskort's
   1 m classes rather than uniform asphalt (re-confirm).
4. **Doors + address signs.** The DAR address chain (house number → access point → building ID)
   measured 100.0% in-tile; the old pilot had 1,762 enterable entrances and 1,340 address
   signs, live-server-verified. The sign format (street name + house number) is a pre-pivot
   call — re-confirm. OSM cannot replace DAR: Danish OSM addresses **are** DAR (an import bot maintains the sync —
   its cadence and whether it reverts manual edits were never measured; 92% of `source=*` in
   OSM Denmark names the register) but without the joins we need — `addr:floor` exists on 26 objects nationally, so
   the shop-floor test needs DAR itself. Shop-name boards, so e.g. a Burger King would show
   "Burger King" on its sign instead of the street address: CVR→DAR join 100.0%; the gating
   rules (ground-floor unit only, refuse `v/ <person>` names) need re-confirmation. If CVR→DAR
   serves difficult, there must be other ways to obtain shop/institute/etc names - e.g. they
   are all available on OSM under tag "Brand", example:
   https://www.openstreetmap.org/node/442918117#map=19/56.150756/10.203656&layers=D
5. **Bridges and underpasses.** The Danish terrain model **embeds bridge decks** (median deck
   height above the DTM: 0.035 m, n=3,929 — `research/bridges-underpasses.md`), so passages
   must be *carved*. The fork can carve from `tunnel=yes` (`highways.rs:860, 910`), so the
   route is the emitter tagging the DHMHestesko horseshoe geometry as tunnel ways
   (`applikation` separates real passages from synthetic hydrology cuts — §7).
6. **Water at survey level.** Same inversion: the DTM embeds the channels; the old pass flooded
   each watercourse at its own surveyed level through the carved passages, sea at elevation 0
   (recorded pre-pivot, re-confirm). ⚠️ Check the fork first: it floods OSM water *polygons*;
   the old repo never read the waterway-*line* path — verify whether lines get flat
   default-width ribbons rather than floods before mapping Danish streams as lines.
7. **Facade colour from Skråfoto** (Denmark-only; no other Nordic country has free national
   obliques): 1,176 buildings classified red/yellow/white/grey in the old pilot. The survivors
   are `research/skraafoto-conventions.md` (the hard-won projection conventions) and the
   *rebuilt* `samples/skraafoto/centroids.json`. ⚠️ The hand-labelled crops behind the
   centroids were lost in the 22 Aug incident; the centroids also live in the conventions
   record. Route in: emitter writes `building:colour`. ⚠️ The **fork** resolves that tag by
   plain sRGB distance; hue-aware (Oklab) matching is **upstream-only** — add it to the §11
   port list if the colours disappoint.
8. **Landcover and street furniture from GeoDanmark**: GeoDanmark wins 4–36× on shared classes
   and OSM landcover leaves 1.4–13% of a Danish tile bare
   (`research/osm-and-portals-23aug.md`). Emit progressively.
9. **Where OSM genuinely wins — keep it** (measured, `research/osm-and-portals-23aug.md`):
   zebra crossings (no Danish register has them — ⚠️ but most OSM crossings are NODES and
   Arnis paints way-crossings only, so a node-handling port is needed before any render;
   CONSULT §2), sports pitch markings, benches, bus shelters, bike parking, `lit=`, and named
   shops — free with the OSM base, one of the pivot's real wins. (Recorded pre-pivot: biomes should come from Danish sources, not OSM —
   re-confirm.)

### Extra custom features
- Manholes and grates with water below. Idealy, waxed weathered copper grate/trapdoor,
flush with road, with 1 water-filled cauldron below.
- Lit lanterns in the ceiling of ground floor in every building (just barely enough,
so monsters won't spawn) + one torch on the block above every address door entrance (on the inside).
- Pale oak signs are placed on the block above every door entrance (on the outside) with the Streetname and House number.
- Non-residental buildings have a **hanging** sign above every address dor entrance (on the outside),
showing e.g. "Burger King" instead of the actual address.

## 17. Danish data-source mechanics

- **The services** (§7 glossary): registration is free self-service — an **email account** at
  selfservice.datafordeler.dk plus an "IT-system" API key covers everything this build reads
  (~15 min to active, key valid 2 years). **MitID Erhverv is NOT needed**: it gates
  access-restricted data only (none of ours) and requires a Danish organisation. The old
  credentials live in the old repo's gitignored `.env` (`DATAFORDELER_KEY/USER/PASS`,
  `DATAFORSYNINGEN_TOKEN`). The Datafordeler key travels in the **query string — never log
  full request URLs**; the Dataforsyningen token in a **header, never a URL**; one canonical
  reader per credential; max ~10 GB per sample file (user's standing preference).
- **Which portal serves what**: the bulk downloads — GeoDanmark, BBR, DAR, the DHM 1 km
  GeoTIFF tiles (`GetRasterFile`) — all come from **Datafordeleren's FileDownloads** with the
  apiKey; Dataforsyningen supplies Skråfoto (STAC, token in header). A live-tested BBR
  **GraphQL** endpoint exists (`graphql.datafordeler.dk/BBR/v2` or `/v3`; the documented `/v1`
  is dead), but FileDownloads is the path proven at national scale; the BBR *REST* lookups'
  15 Jan 2027 retirement does not touch FileDownloads.
- **Never trust HTTP 200**: wrong-case bbox parameters return an empty result with status 200;
  only `PageNumber` paginates (other spellings silently return page 1); HEAD 404s where GET
  200s; `Range` is ignored.
- **A filename is never a vintage pin**: GeoDanmark file-name suffixes are a daily counter and
  bulk downloads regenerate every Sunday — the same name silently serves newer data. Pin by
  md5 + timestamp in a provenance manifest (the old `manifest.json`; copy it).
- **`Z = −999.00` means "elevation unknown", not a depth.** Filter it exactly, everywhere.
- **Nationally present ≠ locally populated**: 10 of ~70 GeoDanmark layers are empty for Aarhus.
  Count records in the actual file for the actual area before designing around a layer.
- BBR downloads are per-municipality; DAR's house numbers are national-download-only while the
  address points are per-municipality (prefer the V4 API for DAR). The point cloud comes as
  1×1 km LAZ tiles in 10×10 km bundles (`data-sources.md` is the full reference).
- Console mojibake ≠ file mojibake: check suspect strings by code point; never paste
  console-rendered text into source code.

## 18. What to copy, what to consult

**Copy: only what git does not hold.** Everything else in the old repo is tracked in its git
history and stays consultable forever — copying it into the new project would just carry
unreviewed material along. Exactly three things exist solely on the old machine's disk
(gitignored):

- `.env` — the working credentials (never committed anywhere).
- **`testserver/denmark-test`** — the build-9 baseline world (§4). The pipeline that made it is
  retired, so it is not regenerable. Archive before anything else.
- `samples/skraafoto/centroids.json` — the facade-colour centroids. Cheap insurance: the values
  are also recorded in the tracked conventions record, but the hand-labelled crops behind them
  are gone for good.

**Consult: [PIVOT-CONSULT.md](PIVOT-CONSULT.md).** The old repo's research corpus was consulted
once (30 Aug 2026) and distilled into that single document — the verified findings, traps and
open questions per domain, with the archive's unratified "decisions" reported as open
questions, and every extracted number adversarially re-checked against its source record. Read
it instead of the scattered records. For the rare deeper dive the archive stays in git
(`d:\ai\KlodsDanmark`, `DOCS.md` is its index). Two named archive files worth knowing:

- `palette.toml` — raw material for the substitution table (work item 8); its "user" statuses
  were AI-recorded, never actually user-reviewed, so the table needs real ratification.
- `tools/kd/roofform.py` — the old LiDAR roof-measurement stage, reference implementation only.
  [USER 30 Aug 2026]: not certain we want it — its results are less visually pleasing than
  Arnis's. If the measured-roofs idea survives an A/B, rewrite fresh; never transplant the code.

## 19. Beware of old, deprecated data

In the old KlodsDanmark project, everything was vibe-coded without any proper human review. So, even if some of its documents may appear to be sound decisions, they should be treated with caution.