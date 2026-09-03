# Design brief: DHM provider, repair gate, emitter, entrance features (PRIMER §5 items 3, 4, 16)

Written 3 Sep 2026 from the verified evidence plus the files opened below. Legend: 🟢 read on disk, 🟡 derived, 🔴 open. Line numbers are at the pinned fork commit `78215bd` unless marked **HEAD** (`b8972b8b`, see §0). Upstream is `louis-e/main` at `e431474`, Meld at `5c1353e` (+1 commit, §0). Anything marked [PROPOSED] is Claude's call and waits for the user.

**What the world will look like.** Item 16 (doors, torches, signs, lanterns, manholes) is the only one that shows something new on screen, and it is already built (§4). Item 3 (the DHM provider) shows almost nothing new: Mapterhorn's Danish tiles *are* the DHM (`research/elevation-mapterhorn-vs-dhm-2026-09-03.md`: median difference 0.00 m, 96.5 % within 0.5 m, n = 35,762). Its value is a pinned vintage, no tile server, fail-closed cells, real harbour depths, and the repair gate (§2), which is where quays and building edges stop being smoothed. Item 4 (the emitter) is built (§3); what changes on screen is register footprints with BBR materials and DAR doors instead of OSM's.

## 0. Where the tree actually stands (differs from STATE.md and the task's pin)

| repo | pinned | on disk | what moved |
|---|---|---|---|
| `arnis` | `78215bd` (v3.1.8) | **HEAD `b8972b8b`** (`git log`: `v3.1.8-2-gb8972b8b`) | `3f47e6f9` "parser: keep addr:street, addr:housenumber and addr:postcode" (`src/osm_parser.rs` +30 lines); `b8972b8b` "nordgrund: doors, torches, signs, lanterns, manholes behind --nordgrund" (9 files, +554/−1: new `src/element_processing/nordgrund.rs`, hooks in `buildings.rs`, `man_made.rs`, `world_editor/mod.rs`, six block ids, `--nordgrund` flag) |
| `meld` | `5c1353e` | **`602449e`** | `settings: nordgrund passthrough` (`src/arnis_cmd.py:364-368`, `src/project.py:27`) |
| emitter | none | `tools/emit_geodk.py` (22 KB, 3 Sep 07:41), notes in `research/emitter-v1-2026-09-03.md`, `research/nordgrund-features-2026-09-03.md` | item 4 v1 exists and has run once (20,239 buildings, 14,227 manholes) |
| DHM data | none | `data/raster/DHM_TERRAEN_1km_<N>_<E>.tif`, 24 tiles (rows 6221–6225, cols 572–576) | item 3 input is on disk; no provider code exists |

Line offsets for HEAD in the six touched files: `osm_parser.rs` +30 after line 65; `buildings.rs` +3 after 4707, +23 after 4743, +27 after 5411; `world_editor/mod.rs` +64 after 1015; `block_definitions.rs` +7 after 381, +13 after 575, +7 after 1352; `args.rs` +19 after 557; `main.rs` +4 after 127.

**One blocking defect on HEAD** (§4.2): the six new block ids 270–275 sit on top of the existing `calcite`…`obsidian` arms. In a Rust `match` the first arm wins and the second only warns, so every cave calcite/amethyst/basalt/obsidian now serialises as a sign, torch, grate, lantern or cauldron, and CI's `clippy -D warnings` fails. The golden gate cannot see it (it hashes ids, not names).

## 1. Elevation provider (item 3)

### 1.1 The trait as it is 🟢

| member | file:line | contract |
|---|---|---|
| `RawElevationGrid { heights_meters: Vec<Vec<f64>> }` | `src/elevation/provider.rs:5-8` | "Height values in meters above sea level. NaN for missing data." |
| `trait ElevationProvider: Send + Sync` | `provider.rs:14-42` | five methods, below |
| `name() -> &'static str` | `:16` | log label and cache subdir; also the string `fetch_elevation_data` and `prefetch_elevation` match on (`mod.rs:166,192`, `:416-429`) |
| `coverage_bboxes() -> Option<Vec<LLBBox>>` | `:18-22` | `None` = global; the selector only considers providers that return `Some` (`selector.rs:40-42`) |
| `native_resolution_m() -> f64` | `:24-26` | read in exactly one place, the selector's log line (`selector.rs:43-47`); order is the hand-written vec |
| `accepts(&LLBBox) -> bool` | `:28-33` | default `true`; a `false` falls through to the next provider |
| `fetch_raw(&self, bbox, grid_width, grid_height) -> Result<RawElevationGrid, Box<dyn Error>>` | `:35-42` | an EPSG:4326 bbox sampled onto a w×h grid |

Selection (`src/elevation/selector.rs`): `--aws-only-elevation` short-circuits to AWS (`:30-36`); otherwise the first entry of `build_provider_list()` (`:60-69`, `Usgs3dep, IgnFrance, IgnSpain, JapanGsi`, "Ordered by resolution (finest first). First match wins.") whose coverage overlaps the bbox (inclusive, `:11-16`) and whose `accepts` is true (`:40-51`); else Mapterhorn (`:53-55`), whose coverage is `None` (`mapterhorn.rs:62-64`). None of the four regional boxes reach Denmark (IGN France metro tops out at lat 51.5, `ign_france.rs:125`). Selector tests to keep green: Sydney → `"mapterhorn"`, forced AWS → `"aws"` (`selector.rs:93-108`).

### 1.2 Request/response contract 🟢

| item | fact | file:line |
|---|---|---|
| bbox | `args.bbox` unchanged; under Meld that is the **seam-expanded, grid-snapped** cell bbox (cell + `seam_buffer_chunks`×16 blocks, default 8) | `mod.rs:184`; `ground.rs:933-937`; `meld/server.py:2707-2717` (`arnis_bbox = expand_bbox_for_seam(...)`), `meld/src/coords.py:183-213,226-243` |
| w × h | `world_width = scale_factor+1` clamped to `[2, 16384]`; world dims from origin-anchored flat metres per degree with `floor()` at both edges | `mod.rs:104-111,119-125`; cap `:76-83` |
| shape | exactly `grid_height` rows of `grid_width`; anything else panics in `FlatGrid::from_vec` | `mod.rs:360-374`; `src/flat_grid.rs:33-39` |
| row order | row 0 = north (max lat), col 0 = west; node `gx` at `min_lng + gx/(W−1)·span`, node `gy` at `max_lat − gy/(H−1)·span`; nodes sit on the bbox edges | `providers/fixed_tile.rs:576-599`, spacing note `:381-388`; `src/elevation_map.rs:41-42` |
| what a node is | when uncapped (always for a Meld cell), node `gx` is block `X = floor(min_x)+gx` and `Ground::level` reads it directly (`fx == block index`); the node lat/lng is the block's **west/north edge**, not its centre | `ground.rs:719-723,730-753`; `mod.rs:106-110` |
| rounding | `.round() as i32`, no neighbour de-speckle | `ground.rs:758-762` |
| NaN | partial NaN is filled from 3×3 neighbours, one ring per pass with a whole-grid copy per pass; a non-Mapterhorn grid > 50 % NaN is replaced by AWS with a stderr warning (> 98 % errors under `--regional-elevation-only`) | `postprocess.rs:1107-1146`; `mod.rs:192-216,202-211` |
| Err | falls back to AWS unless `--regional-elevation-only`, which propagates and exits 1 | `mod.rs:232-255`; `ground.rs:314-320` |
| seam | samples outside the bbox are edge-clamped "wrong, and wrong differently in each neighbouring Meld cell"; Meld's 8-chunk halo hides it | `ground.rs:639-645`; `ground.rs:608-612` (slope reads ±4) |
| floor slip | Meld snaps edges with `round()` and the fork takes `floor()` of the same product: a slip to N−1 is possible up to f64 rounding (not swept) 🟡 | `coords.py:206-213`; `mod.rs:106-107` |

### 1.3 The data as it really is 🟢 (tifffile 2025.6.11 / rasterio 1.5.1 on `data/raster/DHM_TERRAEN_1km_6221_572.tif`, 3 Sep 2026)

| property | value | consequence |
|---|---|---|
| name | `DHM_TERRAEN_1km_<northing-km>_<easting-km>.tif` (Dataforsyningen's own) | the emitter already uses it (`tools/emit_geodk.py:72`); the provider adopts it |
| raster | 2500 × 2500 float32, one band, `PlanarConfiguration 1`, `SampleFormat 3` | `decode_geotiff_f32`'s `F32` arm shape (`providers/regional.rs:324-368`) |
| compression | Deflate (8), predictor 1, **untiled strips of 1 row** | tiff 0.11.3 default features decode it (`tiff-0.11.3/src/decoder/image.rs:538-551`; predictor 2/3 also fine `:868-878`; `Cargo.lock:6125-6136`) |
| georeferencing | `ModelTiepoint (0,0,0, 572000, 6222000, 0)` = the tile's **NW corner**; `ModelPixelScale (0.4, 0.4)`; `GTRasterTypeGeoKey = PixelIsArea`; `ProjectedCSTypeGeoKey 25832` | pixel (i, j) covers `[E0+0.4i, E0+0.4(i+1))`, centre at `+0.2`; the fork reads no geotags anywhere (grep `ModelPixelScale|ModelTiepoint|get_tag` in `src`: none) but the crate exposes them (`tiff-0.11.3/src/tags.rs:141-157`, `decoder/mod.rs:1585-1630`) |
| nodata | `GDAL_NODATA = -9999`; this tile has 0 nodata, 0 NaN | `-9999 → NaN` |
| values | min 1.50, max 30.40 m (inland). Sea is exactly 0.0 (CONSULT §9: "The DTM burns the sea to exactly 0.000 m — legitimate heights, NOT nodata"); **harbour basins are negative**: −14.81 m in 6223_575, −10.64 in 6222_575 (`research/elevation-mapterhorn-vs-dhm-2026-09-03.md`) | sea needs no special-casing; the elevation lock does (§1.6) |
| size | 21.4 MB on disk, 25 MB decoded | 16-tile LRU ≈ 400 MB; tiff default limit 256 MB per decode is fine (`decoder/mod.rs:497-505`) |
| datum | ETRS89 / UTM 32N; the fork treats ETRS89 as WGS84 (`ign_spain.rs:15-16`) and so does the emitter's pyproj null transform (`emit_geodk.py:22-23`) | registers and DHM stay mutually exact; OSM (true WGS84) sits ≤ 1 m off, inside OSM's own noise (CONSULT §7: centroids p50 2.31 m) |

### 1.4 Implementation plan: `src/elevation/providers/dhm_dk.rs` [PROPOSED]

**Struct and configuration.** `build_provider_list` instantiates unit structs and `select_provider(bbox, force_aws)` never sees `Args` (`selector.rs:60-69`), so `pub struct DhmDk;` carries no fields. Configuration travels as the fork's own deep-flag pattern: `--dhm-dir <DIR>` (§5.1) → `main.rs` sets `ARNIS_DHM_DIR` (like `ARNIS_OFFLINE`/`ARNIS_NO_AWS`, `main.rs:133-145`) → a `OnceLock<Option<DhmStore>>` in the module reads it on first use. `DhmStore { dir: PathBuf, index: HashMap<(i32,i32), Square>, tiles: Mutex<LruCache<(i32,i32), Arc<Vec<f32>>>> }`, `enum Square { Tile, Sea }`.

**Index file, fail-closed.** `<dir>/dhm_index.tsv`, one line per 1 km square inside the coverage: `N_km E_km tile|sea [min max]`, written once by our tooling from the Dataforsyningen raster listing (CONSULT §9: raster listings publish no md5, hash yourself) plus each tile's `GDAL_METADATA` `STATISTICS_MINIMUM/MAXIMUM` (tag 42112, read without decoding). Policy per sampled square: `tile` present → value; `tile` absent or undecodable → **Err** whose text contains both `offline: ` and `not cached` (Meld's health scan marks `elevation-not-baked` only on both substrings, `meld/server.py:1027-1032`); `sea` → `0.0`; **not in the index → Err**. For the pilot the index is the 24 tiles, so any cell reaching outside fails instead of rendering sea. With `regional_elevation_only=true` in the Meld project (`meld/src/arnis_cmd.py:444-451`) an Err exits 1 (`ground.rs:315-320`) rather than becoming AWS terrain; that is the only fail-closed path the fork has (`--offline` is not one: `args.rs:526-536`, `arnis_cmd.py:456-463`).

**`accepts` and coverage.** `coverage_bboxes()` = one coarse box, lat 54.4–58.0, lng 7.9–15.4 (keeps the Sydney test); `accepts(bbox)` = the bbox's UTM extent intersects at least one index square. So a Swedish or German cell falls through to Mapterhorn whole; a Danish border cell whose halo crosses the border renders foreign land as index `sea` = 0.0 or Err, whichever the index says. Note this in the index tooling (add foreign-land squares as `tile` from a neighbour's DEM later, or accept flat sea at the border: user's call).

**lat/lon → EPSG:25832.** No projection crate is in the tree (`Cargo.toml:39-61`; `Cargo.lock` has no proj/utm/geodesy). Hand-write Transverse Mercator on GRS80 (`a = 6378137`, `f = 1/298.257222101`, `k0 = 0.9996`, `λ0 = 9°`, `E0 = 500000`, `N0 = 0`), Krüger series: `n = f/(2−f)`; `A = a/(1+n)·(1 + n²/4 + n⁴/64)`; `α1 = n/2 − 2n²/3 + 5n³/16`, `α2 = 13n²/48 − 3n³/5`, `α3 = 61n³/240`; `t = sinh(atanh(sin φ) − 2√n/(1+n)·atanh(2√n/(1+n)·sin φ))`; `ξ' = atan2(t, cos(λ−λ0))`, `η' = atanh(sin(λ−λ0)/√(1+t²))`; `ξ = ξ' + Σ αj·sin(2jξ')·cosh(2jη')`, `η = η' + Σ αj·cos(2jξ')·sinh(2jη')`; `E = E0 + k0·A·η`, `N = k0·A·ξ`. Truncation ≈ n⁴·A ≈ 5·10⁻⁵ m. Unit-test against pyproj 3.7.2 (computed 3 Sep 2026, tolerance 1 mm):

| point | lon, lat | E, N (m) | tile |
|---|---|---|---|
| Rundetårn | 12.5758, 55.6813 | 724793.411, 6176406.626 | 6176_724 |
| Aarhus Domkirke | 10.2104, 56.1567 | 575182.152, 6224179.710 | 6224_575 |
| Skagen | 10.5849, 57.7247 | 594394.922, 6399164.780 | 6399_594 |
| Rønne | 14.7000, 55.1000 | 863505.613, 6120769.276 | 6120_863 |
| Tønder | 8.8630, 54.9350 | 491222.152, 6087566.914 | 6087_491 |
| inverse check | E 574500, N 6223500 | lon 10.1992302, lat 56.1507014 | centre of 6223_574 |

**Sampling by absolute coordinate.** Add one additive default method to the trait: `fn fetch_raw_anchored(&self, bbox, w, h, anchor: Option<&GridAnchor>) -> Result<RawElevationGrid, _> { self.fetch_raw(bbox, w, h) }` with `GridAnchor { origin_lat, origin_lng, scale, min_x: i64, min_z: i64 }` computed in `fetch_elevation_data` (it already holds the origin, `mod.rs:151-152`, and `compute_grid_dims` already computes `min_x/min_z`, `:106-110`), passed only when the grid is uncapped (`grid_w == world_w && grid_h == world_h`). Existing providers keep the default, so nothing they do changes. The DHM provider maps node `(gx, gy)` → block `(X, Z) = (min_x+gx, min_z+gy)` → the exact inverse of `transform_point` (`src/coordinate_system/transformation.rs:182-189`; the same inverse already exists at `ground.rs:366-371`): `lng = olng + (X + 0.5)/(mpd_lon·scale)`, `lat = olat − (Z + 0.5)/(111320·scale)`. Two cells sharing a block compute bit-identical `(E, N)`, which retires the floor-slip seam (§1.2) by construction. `+0.5` = block centre [PROPOSED]: a block covers `[X, X+1)` and the emitter's footprints are placed by the same `floor()`, so the centre is the representative point; today's providers sample the NW corner (§1.2), a half-block bias that is invisible at 30 m and visible at 0.4 m on kerbs and quays. Without an anchor (standalone runs, `--elevation-map`) use the bbox-fraction formula of `fixed_tile.rs:576-599`.

Per node: `(E, N)` → `n_km = floor(N/1000)`, `e_km = floor(E/1000)`; `c = (E − 1000·e_km)/0.4 − 0.5`, `r = (1000·(n_km+1) − N)/0.4 − 0.5` (PixelIsArea, centre sampling; the emitter's `Dhm.at` does the same, `emit_geodk.py:83-97`, but clamps inside the tile at `:94-95`, which the provider must not do); `c0 = floor(c)`, `r0 = floor(r)`; a pixel index of −1 or 2500 resolves to the west/east/north/south neighbour square through the index (tiles abut exactly at the 1 km corners, §1.3); blend the four values with `blend_finite_samples` (`fixed_tile.rs:288-323`, `pub(super)`, NaN-aware: "all-NaN → NaN"). `fixed_tile`'s own sampler is Web-Mercator only (`:70-102,257-286`) and `resample_nearest` is private and stretches a raster onto the grid (`regional.rs:386-419`); reuse neither. Cost: a 1.3 km cell is ~1.7 M nodes, each one series evaluation and four loads: well under a second.

**Decoding a tile.** `tiff::decoder::Decoder::new(File)` → check `dimensions()`, read tag 33550 (must be `0.4, 0.4`), 33922 (tiepoint must equal `(1000·e_km, 1000·(n_km+1))` from the filename), 42113 (nodata, default −9999), then `read_image()` → `DecodingResult::F32`; any mismatch → Err (fail closed, REFERENCE §13). Permit `dims × scale = 1000 m` rather than hard-coding 2500 so a 100 px @ 10 m synthetic tile can be a test fixture (§5.2). Values `== nodata` or non-finite → NaN; everything else, including 0.0 and negatives, is data.

**Registration** (three lines): `pub mod dhm_dk;` in `src/elevation/providers/mod.rs:1-7`; `use providers::dhm_dk::DhmDk;` next to `selector.rs:1-8`; `Box::new(DhmDk), // 0.4 m local GeoTIFF` as the first entry of the vec at `selector.rs:60-69`. `name()` = `"dhm_dk"`, `native_resolution_m()` = `0.4`.

**`--prewarm-elevation` and `--elevation-map`.** `prefetch_elevation` warms any non-Mapterhorn/AWS provider by calling `fetch_raw` and discarding the grid (`mod.rs:425-429`), a full sample for nothing; Meld's bake runs it per sub-bbox because the pilot projects have `prefetch_terrain: true` (`data/meld-data/projects/*/project.json`; `meld/src/prefetch.py:478-491`). Add a `"dhm_dk"` arm that walks the index squares of the bbox and returns `(name, present, sea, missing)`; `main.rs:336-354` already prints the summary Meld parses and exits 2 on `missing`, so Meld's terrain bake becomes the DHM preflight. `--elevation-map` asks for ≤ 1024 nodes over the whole bbox (`src/elevation_map.rs:36-46`); a country-wide preview would decode ~45,000 tiles. v1: Err when the bbox touches more than 64 index squares; v2: build the overview from the index min/max.

### 1.5 Caches, offline, hash neutrality, tests

- No network, so `ARNIS_OFFLINE` is irrelevant. Keep the store **outside** `ARNIS_CACHE_ROOT/arnis-tile-cache`: the 7-day mtime sweep (`src/elevation/cache.rs:6-7,211-221`) runs on every start without a master origin (`main.rs:174-176`: `--prewarm-elevation`, `--elevation-map`, standalone runs). `data/raster` is outside Meld's root `data/meld-cache` (`meld/server.py:101-111`). Meld's own cache accounting knows only `aws` (`meld/src/prefetch.py:358-360`).
- Golden hashes cannot move: the harness runs `--mode geo-only` (`scripts/golden_hash.sh:110-115`) → `terrain()` false → `Ground::new_flat`, no provider or postprocess code runs (`args.rs:679-681`; `ground.rs:932-966`); `accepts()` is false without `ARNIS_DHM_DIR`, so terrain runs elsewhere select exactly as today; the anchored default method leaves other providers untouched.
- Tests (offline, like the rest of `src/elevation`: three live tests are `#[ignore]`, `aws_terrain.rs:567-569`, `mapterhorn.rs:1048-1050,1072-1074`): the five UTM vectors; index parse; `accepts` false without the env var; grid shape `h × w`; corner sampling across a tile edge with two injected 100 px @ 10 m tiles (give the store a `TileSource` trait so tests inject arrays); nodata → NaN; `sea` → 0.0; missing listed tile → Err containing `offline: ` and `not cached`; unlisted square → Err; anchored vs fraction sampling agree on a grid-snapped bbox. One `#[ignore]` test reads `data/raster` when present and checks the Aarhus Domkirke sample against rasterio.

### 1.6 The elevation lock must change before the first DHM cell [PROPOSED, amends decisions.md I]

Meld's lock comes from an AWS z10 survey (`meld/src/survey.py:2-5`, applied at `server.py:4425-4429`) or, in all three pilot projects, the manual `0–180 m` with `ground_level 62`. `scale_to_minecraft` clamps every height to `[ground_level, …]` (`postprocess.rs:1297-1336`, `:1335`), so basins at −14.8 m and reclaimed land (Lammefjord ≈ −7 m) flatten to sea level (STATE.md item 6 already saw this). To keep *Y = 62 + metres*: `--elevation-min -20 --elevation-max 175` (Møllehøj 170.86 m; scan the national tiles' `STATISTICS_MINIMUM` for the true floor) and `ground_level 42` (`mc_y = 42 + (h + 20)`), i.e. Meld `ground_level: 42`, sea at Y 62, Møllehøj at Y 233, deepest basin at Y 47; 106 blocks stay below sea for mining instead of 126. First merge wins on the height profile (REFERENCE §10.5): decide before the first production cell. The named patch "teach Meld's survey to sample the render provider" (PRIMER §5) is unnecessary with a manual lock.

## 2. The repair-stage gate

### 2.1 What runs today, in order (`src/elevation/mod.rs:263-340`) 🟢

| stage | call | what it does to 0.4 m data | v1 action |
|---|---|---|---|
| `filter_elevation_outliers` | `mod.rs:270-272`, only when `master_origin_lat.is_none()` (the in-tree gate template, `:264-275`) | never runs under Meld | unchanged |
| `repair_terrain_anomalies` | `mod.rs:276`; `postprocess.rs:22`, 5×5 window, ≥ 8 finite neighbours, up to 10 passes, replace when `deviation > 6 m && > 3·max(MAD,1)` (`:32-35,85-87,99-103`) | erases every genuine edge over 6 m in ~2 m: quay walls, cliff tops, bridge abutments, silo edges | **skip** |
| `fill_nan_values` | `mod.rs:280`; `postprocess.rs:1107-1146` | fills nodata holes; near-free on DHM | keep |
| `apply_land_cover_repair` | `mod.rs:316-326` with σ = 30 m and pull = 25 m converted to cells (`:303-314`); `postprocess.rs:151-157`; bails on grid-size mismatch (`:167-173`) | see the four sub-stages | keep the call, change its arguments |
| ↳ `level_water_surfaces` | `postprocess.rs:180`; still water → component mode, cells `≤ surface + 2 m` **and** enclosed cells overwritten (`:260-278,405-421`); flowing (IQR > 5 m) → local 12-cell median (`:388-393`) | sea mode is 0.0 (no-op), basins are raised to 0.0 (needed, see 2.3), but quays and banks ESA calls water within 2 m are pulled down | **raise-only** (new mode) |
| ↳ `reclassify_non_surface_water_cells` | `:192-204`; drops LC water cells that were not levelled and recomputes `water_distance`/`water_blend` | with raise-only this turns ESA's quay pixels back into land: DHM decides | keep |
| ↳ `smooth_built_up_gaussian` | `:208`; σ = 30 cells at 1 m = 181 taps (`:954`); skipped when σ < 1.5 (`:850-853`) | blurs the whole city to 30 m | pass σ = 0.0 |
| ↳ `pull_coastal_land_toward_water` | `:215` gate; `:751-812`, ≤ 15 m above water within 25 m ramped down | every beach, dune foot, harbour front and low cliff ramped to 0 | pass 0 |
| `scale_to_minecraft` | `mod.rs:330`; `postprocess.rs:1239-1336` | the vertical mapping | keep |

### 2.2 The flag and the insertion points [PROPOSED]

`--elevation-trust <off|v1>`, `default_value = "off"`, `value_parser = ["off", "v1"]` (the `--river-bed` recipe, `args.rs:483-487`: a retune ships as `v2`, never as a changed `v1`). Name check: `trust` occurs 0 times in `data/downloads/arnis-3.1.8-help.txt`, so Meld's substring probe (`arnis_cmd.py:166-175`) cannot misfire. Thread it by value: `generate_ground_data` (`ground.rs:932-966`) → `Ground::new_enabled` (`:199-218`, one caller at `:935`) → `fetch_elevation_data` (`mod.rs:141-156`, already `#[allow(clippy::too_many_arguments)]`). Edits: wrap `mod.rs:276` in `if !trust`; at `mod.rs:316-326` pass `(0.0, 0, WaterLevel::RaiseOnly)` under v1 and `(σ, pull, WaterLevel::Full)` otherwise; add the `WaterLevel` parameter to `apply_land_cover_repair` (`postprocess.rs:151-157`) and to `level_water_surfaces`, where the two write sites (`:388-393` flowing, `:418-421` still) become `if mode == Full || orig < surface { heights = surface }`. Fire the `bench.mark` calls outside the gate so labels stay stable (`mod.rs:264-275`). `Full` must stay bit-identical: the two bit-exact postprocess tests and the existing three keep passing; add a raise-only test (never lowers) and an args default test.

The flag applies whatever the provider. In a border cell rendered by Mapterhorn it would also switch the repairs off; keying it on `provider.name() == "dhm_dk"` as well is the alternative if that ever shows.

### 2.3 Why water is levelled at all, and the carve

The fork has no flood-to-level pass: a water cell's surface **is** its terrain height, and `water_depth.rs:511-534` then sets `WATER` from that Y down at most 6 blocks (`MAX_WATER_DEPTH`, `:56-60`) with a bed below; Meld always sends `--water-carve-clearance max` (`meld/src/arnis_cmd.py:388-393`), so `water_floor = max(ground_level, MIN_Y + 8)` (`ground.rs:259-284`). Skipping `level_water_surfaces` entirely would leave a −14.8 m basin as a 14-block pit with 6 blocks of water at its bottom; raise-only fills it to 0.0 and the carve gives the usual 6-block bed (real bathymetry, Dybdemodel, is a later provider-side merge, CONSULT §9). The water *mask* stays ESA 10 m; the next step after v1 is a mask from the DTM's own zero burn (CONSULT §9: "the zero-burn is the sea/land authority"), which is work item 8/9 territory, not this gate.

## 3. Emitter contract (item 4): the fork's rules and `tools/emit_geodk.py` checked against them

### 3.1 What the fork accepts 🟢

| rule | file:line |
|---|---|
| top level `{"elements": [...]}`; `remark` optional; other keys ignored (no `deny_unknown_fields`) | `src/osm_parser.rs:96-101,84-91` |
| element: `type`, `id: u64`, `lat/lon`, `nodes: [u64]` (ids, never inline coords), `tags: {String: String}` (**values must be JSON strings**), `members [{type, ref, role}]`; a negative/fractional id or a numeric tag value fails serde and the **whole tile is skipped** with one stderr line | `:84-94,77-82`; `:199-206` |
| tiles named exactly `osm_g1_z{z}_{x}_{y}.json`, `g1` hard-coded, x outer/y inner, missing tiles counted not raised; slippy math `:242-249` (= Meld `survey.py:24-29`) | `:159-165,132-135`; Meld `osm_grid.py:46,51,77-82` |
| cross-tile dedup on `(type, id)`, **first tile wins, content not compared** | `:216-223` |
| within one tile a later node with the same id **replaces** the earlier | `:991` |
| every node a way references must be in a loaded tile; unresolved refs are dropped silently | `:1013-1024` |
| relations only `type=multipolygon|building`; member ways must be loaded | `:1102-1105,1170-1177` |
| building rings: first id repeated last, ≥ 4 ids | `:1434-1437` |
| tag filter: 28 keys + 17 prefixes dropped, `source*` and `start_date` among them; **HEAD keeps `addr:street/housenumber/postcode`** | `:14-64`; HEAD `:66-79` (`KEPT_ADDR_TAGS`) |
| ids: bits 61–62 are read as a style hint on tall buildings, bit 63 is Overture's marker; three way ids are skipped outright | `:523-527`; `buildings.rs:308-311`; `overture.rs:53-56`; `buildings.rs:4899-4902` |
| an out-of-range lat/lon panics the run | `:977-980` |
| outline suppression: an outline ≥ 50 % covered by `building:part` rings is dropped | `:1546-1553,1224` |

### 3.2 IDs as built 🟢 (`emit_geodk.py:24-25`, `:307-330,348`)

`way = 2^40 + 4·lid + ring`, `node = 2^41 + 2048·lid + vertex`, `relation = 2^42 + lid`, `entrance node = 2^43 + husnummer_seq`, `manhole node = 2^44 + lid`, all keyed on GeoDanmark `id_lokalId` (deterministic, no randomness: header `:1-12`). Real magnitudes (read from `GEODKV_V4_Bygning_0751_…_717.zip`, n = 199,406): `id_lokalId` 1,008,424,036 … 1,241,852,595. So node ids run to ≈ 4.7·10¹², past `2^42` (harmless: relations are a different `type`) and stay below `2^43` while `lid < 3.0·10⁹`; every range is < 2^45 ≪ 2^61 and above OSM's ≈ 1.4·10¹⁰. Add `assert lid < 3_000_000_000` next to the existing `assert vi < NODE_STRIDE` (`:308`).

### 3.3 Tags emitted per building and what each does

| tag | emitter source | fork effect |
|---|---|---|
| `building=<value>` | BBR `byg021` through the closed `USE` table (`:28-49`, `:220-222`; unknown code aborts `:333-335`); `bygningstype` Tank/Silo → `silo`, Drivhus → `greenhouse` (`:209-213`); unkeyed → `shed`/`yes` (`:215`) | category `buildings.rs:302-431` (religious list `:350-360`: `church` ✓); inference table only without height (`:1717-1746`); auto-gable list (`:4851-4874`); residential list HEAD `:5445-5453`. **Fall to `Default`** (no auto-gable, generic palette): `service`, `transportation`, `sports_hall`, `grandstand`, `allotment_house`, `conservatory`; `silo` goes to the tank renderer (`man_made.rs:516-521`), `roof` and `parking` exit early (`buildings.rs:5041-5086`), `ruins` → Ruined (no doors/interior/roof, `:31-56,5152-5169`) |
| `building:levels` | `byg054` (`:224-228`), `1` for 9xx sheds | `(levels·4+2)` blocks, tall > 7, sanitised ≤ 200 (`:1789-1808,1646-1663`); overridden by `height` |
| `height` | eave = median(ring Z − DHM) when 2–200 m (`:241-253`; n = 18,189, median 3.6 m per the note) | wall height in metres, tall > 28 m, skips inference (`:1815-1846,1860-1876`); REFERENCE §16.2 asks for it on every footprint |
| `building:material` | `byg032` via `WALL` (`:51,229-231`) | `:1425-1455` → `get_wall_block_for_material` (`block_definitions.rs:2017-2078`). Accepted after normalisation: `brick`, `concrete`, `wood`, `metal`, `glass`. **Not accepted → None → palette**: `timber_framing` (table has `timberframe`/`halftimbered`), `eternit` (table has `fibrecement`/`asbestos`), `plastic`. Fix the three strings in `WALL` |
| `roof:material`, `roof:colour` | `byg033` via `ROOF` (`:52,232-236`) | `:7725-7742` → `get_roof_block_for_material` (`block_definitions.rs:2079-2113`): `tar_paper`, `eternit`, `concrete`, `roof_tiles`, `metal`, `thatch`, `glass`, `grass` ✓; `plastic` ✗ → colour match; named colours via `colors.rs:52-88` 🟡 (check `grey` vs `gray` spelling in that list) |
| `name` | OSM building name inside the footprint (`:254-256`) | hanging board text (`nordgrund.rs:201-205,264-268`) |
| `nordgrund:residential=yes|no` | `RESIDENTIAL` codes (`:50,239`) | HEAD `buildings.rs:5445-5447` |
| `nordgrund:id` | `:238` | tracing only; survives the filter (not `addr:`/`source*`) |
| not emitted | `construction_date` (BBR `byg026`, band-filtered, CONSULT §9) | would drive `ArchEra` (`osm_parser.rs:844-880`) and the pre-1945 masonry hint (`:704-710`); `start_date` is filtered, this key is not: add it |
| entrance node | DAR access point snapped to the outer ring ≤ 25 m, inserted in ring order (`:268-289,293-318`): `entrance=main`, `addr:street/housenumber/postcode`, duplicates under `nordgrund:*`, `nordgrund:sign` from the nearest named OSM POI in the footprint or ≤ 12 m (`:280-286`) | `is_entrance` (`nordgrund.rs:128-134`); preset doors suppressed (`buildings.rs:1134-1148`); stock `doors.rs:5-24` still runs on it (§4.7) |
| `man_made=manhole` node | GeoDanmark Brønddæksel (`:338-349`) | `man_made.rs` HEAD `:536` |
| multipolygon relation | holes (`:326-330`) | `osm_parser.rs:1102-1105`; Overture dedupe ignores relations (`overture.rs:386-390`), moot with `overture=false` (all pilot projects) |

### 3.4 Dedupe against OSM

What the fork does for Overture: `deduplicate_against_osm` drops an Overture way whose centroid falls in the AABB of any parsed building **way** with ≥ 3 nodes (`overture.rs:444-449,386-390`; called `main.rs:543-552`, gated `args.buildings && args.overture && !skip_objects`, `:526-535`). It runs on Overture elements after parse and is not reusable for tiles: tiles are merged by `(type, id)` only, so two overlapping buildings from OSM and GeoDanmark would both render. The emitter therefore dedupes at write time, wholesale: every OSM `building`/`building:part` way whose centroid lies in the coverage box is removed, and every building relation that references a removed way (`:380-397`); OSM's building names are carried over (`:254-256`). This also sidesteps the outline-suppression rule (§3.1) since S3DB parts vanish too. decisions.md L asks the user whether OSM buildings should survive where GeoDanmark has none. Gap: OSM `entrance=*`/`door=*` nodes of removed buildings stay as tagged nodes (258 in the pilot tiles) and `doors.rs:5-24` still builds a stray door column at each; drop tagged entrance/door nodes inside a removed footprint in the emitter.

### 3.5 Writing Meld's tile cache 🟢

| rule | file:line | as built |
|---|---|---|
| tile lives at `<cache root>/osm/osm_g1_z11_{x}_{y}.json` (root `$MELD_CACHE_DIR` else `<data>/cache`); Meld hands the directory straight to `--osm-tile-dir … --osm-tile-z 11`, no merge step | `meld/src/prefetch.py:350-354,666-677`; `arnis_cmd.py:295-298` | `CACHE/osm` (`emit_geodk.py:20,376`) ✓ |
| a building must be self-contained in every z11 tile it touches, byte-identical copies | `osm_parser.rs:1013-1024,216-223` | `tiles_for` on the building bbox; nodes, entrance nodes, way, relation added per tile (`:99-109,331-332,399-403`) ✓ |
| valid = size > 2, last non-space byte `}`, mtime within `osm_cache_ttl_days` (365 default, `0` = never) else re-downloaded over it | `prefetch.py:159-166,584-593,329-334` | `json.dump` ends in `}`; all three pilot projects have `osm_cache_ttl_days: 0` ✓; put `0` in the project template |
| rewrite in place with a temp file + `os.replace`, then reap the `.osmbin` | `prefetch.py:224-229`; `osm_grid.py:98-101,121` | `:405-412` ✓ (the fork would re-bake anyway: content hash on every read, `osm_sidecar.rs:9-17`) |
| `import_pack_folder` never overwrites an existing tile | `meld/src/datapack.py:767-768` | not used ✓ |
| a `.pbf` bake skips tiles ≥ 12 bytes unless `force` | `osm_pack.py:51,80-81,501` | a forced bake would clobber; note in the runbook |
| originals kept for re-runs; prior emitter output dropped by id range | `emit_geodk.py:112-117,382-383,405-408` | `osm-original/` ✓, idempotent ✓ |
| tagged nodes only become features inside the cell bbox; a tile's untagged orphans are harmless | `osm_parser.rs:993-997` | orphan nodes of removed ways stay ✓ |

## 4. Doors, interiors, signs, manholes (item 16): as built at HEAD, and what is left

### 4.1 The feature set 🟢 (`src/element_processing/nordgrund.rs`, flag `--nordgrund none|all|list`, HEAD `args.rs:558-566`, parsed `:701-708`, validated `main.rs:128-131`, exit 2 on a typo)

| feature | trigger | placement | blocks/states | hook |
|---|---|---|---|---|
| `doors` | an outline node with `entrance≠no` or `door` (`:128-134`), on the rasterised wall or one cell off (`:211-224`) | `door_y = start_y_offset + abs_terrain_offset + 1` (HEAD `buildings.rs:5458`), i.e. the building's base, not the local ground | `dark_oak_door` lower/upper, `facing` = outward normal (`:139-164`, the building pass's own rule), `hinge=left`, `open=false`, `powered=false` (`:296-304`), blacklist `Some(&[])` overwrites the wall (`:229-246`) | HEAD `buildings.rs:5441-5463`: after walls, floors, interior; before the roof |
| `torches` | same node | inside cell `(ex−nx, door_y+2, ez−nz)` if free (`:247-261`) | `wall_torch` `facing` = into the room (`:306-310`; correct vanilla sense) | same |
| `signs` | same node | outside cell `(ex+nx, door_y+2, ez+nz)` (`:262-292`) | address: `pale_oak_wall_sign`, lines = street ≤ 15 chars × 2 + number (`:106-117`); board: `pale_oak_wall_hanging_sign` with `nordgrund:sign` (node) or, on non-residential, `nordgrund:sign`/`name` (way), 10 chars × 4 (`:120-126`); the board **replaces** the address sign (decisions.md E) | `place_nordgrund_sign` HEAD `world_editor/mod.rs:1030-1080` |
| `lanterns` | every ceiling of every walled building, 10-block world grid `rem_euclid` (`:316-318`) | one below the ceiling slab; glowstone removed entirely (HEAD `buildings.rs:4711-4712,4747-4770`) | `lantern[hanging=true]` | replaces `x%5==0 && z%5==0` glowstone (`:4732-4759` at 78215bd) |
| `manholes` | `man_made=manhole` node | `y0 = get_absolute_y(x, 0, z)` (road-override aware, `mod.rs:821-838`), only if the cell above is free (`:322-333`) | `waxed_weathered_copper_grate` at `y0` (blacklist `Some(&[])` replaces the road block), `water_cauldron[level=3]` at `y0−1` | `man_made.rs` HEAD `:536`; man_made nodes sort at priority 6 after highways (2), so the road override exists (`osm_parser.rs:1644-1655`; `highways.rs:1756-1758,1941,2051-2053`) |

Determinism: nothing in the module reads randomness (`:3-5`); the halo merge keeps the auth tile's non-air block (`common.rs:1229-1233`) and the first block entity per coordinate (`java.rs:636-653`), which is safe because both editors place the same thing. Meld passes the flag from the `nordgrund` setting (`meld/src/arnis_cmd.py:364-368`, `project.py:27`); project `aarhus-nordgrund` has `nordgrund: "all"`.

### 4.2 Blocking defect: block ids 270–275 🟢 (proved)

HEAD `block_definitions.rs:385-390` adds `270 => "pale_oak_wall_sign" … 275 => "water_cauldron"` directly above the pre-existing `270 => "calcite", 271 => "amethyst_block", 272 => "budding_amethyst", 273 => "basalt", 274 => "smooth_basalt", 275 => "obsidian"` (`:391-396`), and `:1356-1367` declares both const sets on the same ids. A stand-alone `rustc` check (scratchpad `dup_arm.rs`, 3 Sep) prints `warning: unreachable pattern … no value can reach this` and `id 270 -> pale_oak_wall_sign`: the first arm wins. Consequences: `CALCITE`, `AMETHYST_BLOCK`, `BUDDING_AMETHYST`, `BASALT`, `SMOOTH_BASALT` (`src/caves/decoration.rs:509-620,945-955`, `caves/schems.rs:214-215`) and `OBSIDIAN` (`caves/mod.rs:476`) now serialise as sign, hanging sign, torch, grate, `lantern[hanging=true]` (`:580-584`) and `water_cauldron[level=3]` (`:585-589`) whenever `--caves` is on (Meld `caves` setting, `arnis_cmd.py:371-375`; the pilot projects have it off); `cargo clippy --all-targets --all-features -- -D warnings` (`ci-build.yml:26-30`) fails. The golden gate is blind to it by construction: it hashes ids (`common.rs:650-663`), the fixtures have no caves, and the commit's "5/5 byte-identical" is therefore true and irrelevant. Fix: move the six to **450–455** (highest id today 449, `block_definitions.rs:562`; ceiling 512, `:70`; every id needs a `name()` arm or it panics, `:563`), delete the duplicate arms and consts, add `#![deny(unreachable_patterns)]` to the module, and a unit test asserting the seven old names and six new ones by id.

### 4.3 Sign block entities for 26.2

`place_nordgrund_sign` (HEAD `mod.rs:1030-1080`) writes `id`, `front_text{messages: four bare strings, color: black, has_glowing_text: 0}`, an empty `back_text`, `is_waxed 1`, `keepPacked 0`, `x/y/z`, then the block with `facing` + `waterlogged=false`; it checks bbox, flushed region (`is_region_flushed`, `:1316` at 78215bd) and a free cell. This is the REFERENCE §11.2 form ("26.2 wants a bare string … exactly four messages", old-project live readback) rather than the JSON-quoted form of the fork's dead `set_sign` (`mod.rs:1256-1318`) and upstream's `sign_block_entity` (`louis-e/main:src/world_editor/mod.rs:1359-1389`). Danish letters are safe: fastnbt 2.6.1 writes CESU-8 for every string (`Cargo.toml:35`; `fastnbt-2.6.1/src/ser/write_nbt.rs:15-20`). Still open for *this* build 🔴: place, boot 26.2, read one wall sign and one hanging sign back (the research note lists readability and the hanging-sign fit as "open until walked"); the wall hanging sign's `facing` sense and support rules are not in either repo (no `*hanging_sign` anywhere; upstream has only `pale_oak_trapdoor`, `louis-e/main:src/block_definitions.rs:478`). Missing: a Java-only guard (`WorldFormat`, `mod.rs:100-106`; the banner pattern `:995-1015`), or Bedrock/Luanti runs get a Java compound.

### 4.4 What still comes from upstream

- **Synthetic street-facing doors** for buildings without an entrance node: `plan_synthetic_entrance` (`louis-e/main:src/element_processing/buildings.rs:3096-3120`; no door when the segment < 4 cells, `:3152-3154`), call order `:7081-7093`, door species by category `:3072-3092`, double doors on `entrance=main` for Commercial/Office/Hotel `:3296-3301`. It needs the road mask; `generate_buildings` has no `road_mask` parameter (`buildings.rs:4881-4890`) though the call site has it (`data_processing.rs:65-80,535-541`). Affects keyed buildings whose house number lacks a building id (5.4 % in 0751 per the emitter note) and every unkeyed footprint.
- **Keep-clear of door columns** (`louis-e/main …:7089-7092`): the fork's decorations (`buildings.rs:5302-5330`) run *before* the nordgrund pass, which forces the door but only places a torch or sign into a free cell; a quoin or window frame there suppresses the sign silently. Count and log those, or force the sign cell when the occupant is a decoration.
- Not needed: upstream's decal signage (`signage.rs:1067-1077` uses item-frame decals for house numbers; Meld's merge cannot carry them, REFERENCE §11.2). `split_lines` is already ported (`nordgrund.rs:76-103` = `louis-e/main:src/element_processing/signage.rs:981-1009`).

### 4.5 How a node feature is processed

Parse keeps only tagged nodes inside the cell bbox (`osm_parser.rs:993-997`) → one priority sort (`main.rs:562-563`; `entrance 0, building 1, highway 2, …, default 6`, `osm_parser.rs:1644-1655`) → tile assignment including the 64-block halo (`tile.rs:206-216`; `data_processing.rs:707-712`) → per-tile `process_element` dispatch in that order (`data_processing.rs:170-219`, `:730-731`) → the handler finds Y through the editor (`get_absolute_y`/`get_ground_level`, override-aware `mod.rs:821-838`; bridge decks via `node_feature_base_y`, `highways.rs:710-721`; road orientation via `get_nearest_road_block`, `element_processing/mod.rs:140-174`, as the bench does `amenities.rs:145-172`) → writes with the if-absent/whitelist/blacklist semantics (`mod.rs:1601-1606`) → halo merge and coordinate dedup (§4.1) → Java write (`java.rs:1155-1200`). The street lamp is the template (`highways.rs:1254-1260,1158-1172`, `REDSTONE_LAMP lit=true`).

### 4.6 Non-residential classification

Emitter tag first (`nordgrund:residential`, BBR codes 110–190, 510, 540: `emit_geodk.py:50`), else the type list `house|residential|detached|semidetached_house|terrace|farm|cabin|bungalow|villa|apartments|dormitory|allotment_house|yes` (HEAD `buildings.rs:5448-5453`; `yes` counts as residential, so unkeyed footprints never get a board). The board needs a name: node `nordgrund:sign` (nearest named OSM shop/amenity/office/craft/tourism/leisure/healthcare, `emit_geodk.py:112-138,280-286`), else way `nordgrund:sign`/`name`. CVR names (decisions.md 5, licence closed) and the ground-floor-unit and `v/ <person>` rules (decisions.md E) are not in v1.

### 4.7 Fixes to make before the next walk [PROPOSED]

1. Block ids 270–275 → 450–455 (§4.2).
2. `doors.rs` still runs for every entrance node (`data_processing.rs` HEAD `:174` → `doors.rs:20-23`, a ground-relative column with `half` only): on a slope its blocks stay embedded in the foundation pillar (`buildings.rs:2247-2262`, base Y is the max of four corners `:1387-1411`). Skip it when `args.nordgrund().doors` is on; hash-neutral.
3. Manhole vs the ground pass: on steep cells the surface block is force-replaced with a blacklist that does not include the grate (`ground_generation.rs:822-843`; flat cells are if-absent `:844`). Add `WAXED_WEATHERED_COPPER_GRATE` to that blacklist under the feature. This answers the note's "does the ground pass preserve the grate" for the steep case; walk the flat case.
4. Java-only guard in `place_nordgrund_sign` (§4.3).
5. Sign read-back on 26.2 for both sign kinds (§4.3).
6. Emitter: `WALL` strings (§3.3), drop OSM entrance/door nodes inside removed footprints (§3.4), `construction_date`, `lid` assert (§3.2).
7. Lantern density and "all floors" (decisions.md M) are the user's aesthetics; the code keys on world coordinates so any grid pitch stays seam-safe.

## 5. Flags, harness, build, Meld

### 5.1 Flags

| flag | recipe | lines | Meld |
|---|---|---|---|
| `--nordgrund <spec>` (exists) | `String`, `default_value = "none"`, validated at startup; `gui.rs` literal has `nordgrund: "none"` | HEAD `args.rs:558-566,701-708`; `main.rs:128-131`; `gui.rs:1223` | `settings.nordgrund` → `--nordgrund` behind `arnis_supports` (`arnis_cmd.py:364-368`; default `project.py:27`); no web control, no Meld test yet |
| `--dhm-dir <DIR>` (new) | `#[arg(long = "dhm-dir", value_name = "DIR", env = "ARNIS_DHM_DIR")] pub dhm_dir: Option<PathBuf>` (recipe `args.rs:37-41`; clap has the `env` feature, `Cargo.toml:26`); `main.rs` re-exports it as `ARNIS_DHM_DIR` (`:133-145` pattern); `gui.rs` literal `dhm_dir: None` (`:1111`, the trap: every `Args` field must appear there) | | `dhm_dir: ""` in `default_settings` (`project.py:245-252` pattern); `if settings.get("dhm_dir") and arnis_supports(exe, "--dhm-dir")` (`arnis_cmd.py:475-478` pattern); also set `regional_elevation_only: true` for Denmark |
| `--elevation-trust <off|v1>` (new) | `--river-bed` recipe (`args.rs:483-487`); `gui.rs` `"off"` | §2.2 | `elevation_trust: "off"`; passthrough block; `test_reachable_flags.py:29-55` pattern (off by default, on when set, not passed to an old binary) |

Rules that bind all three: not `hide = true` (`args.rs:154-155`) or Meld never sends it (REFERENCE §10.4 item 5; `arnis_cmd.py:166-175`); the help text must end with the additivity sentence (`args.rs:530`); a flag Meld drives with a `true|false` token needs the `--overture` recipe (`args.rs:274-275`; `arnis_cmd.py:330-332`), a plain `SetTrue` bool rejects the token; never spell a flag `--signage` (Meld auto-emits it with `none|basic|full`, `arnis_cmd.py:354-355`, `server.py:4270-4272`). Meld caches `--help` per exe path until restart (`arnis_cmd.py:188-199`), so a swapped binary looks flag-less until Meld restarts. `/api/settings` passes unknown keys through (`server.py:4165-4169`); a checkbox needs three edits in `web/index.html` (`:2429-2436,3317-3320`), optional since Claude drives the API (decisions.md B).

### 5.2 Golden hashes and fixtures

- The gate: `ARNIS_BLOCK_HASH=1 arnis --file … --bbox <bounds> --mode geo-only --no-3d --overture=false --offline` (`scripts/golden_hash.sh:110-115`), fixtures `tests/fixtures/*.osm.gz` with an Overpass `<bounds>` (`:73-77,97-103`) converted by `scripts/osm_xml_to_overpass_json.py` (`:104-107`), five hashes in `tests/golden_hashes.txt:1-6`. It hashes **block ids only** (`common.rs:632-663`): not block-state properties or block entities (`common.rs:287-291`), not biomes (`java.rs:461`), not names (§4.2). Every item-16 block would move it if default-on; `none` keeps 5/5 (commit `b8972b8b`).
- Guards to add: `#![deny(unreachable_patterns)]` + the name test (§4.2); a `WorldEditor` unit test for the sign compound and door properties (the existing `nordgrund.rs` tests `:339-382` cover parsing, wrapping, the grid and the normal only).
- Feature fixtures: let the harness read an optional `tests/fixtures/<name>.args` (flags appended to the command, e.g. `--nordgrund all`) and accept `<name>.json.gz` fixtures (Overpass JSON, so an emitter tile clipped to ~300 m can be one; skip the XML converter and take the bbox from `.args`). Two new manifest rows then pin item 16 on a Danish block; run the harness from Bash with `PATH="$HOME/.cargo/bin:$PATH"` (line 52 builds first; cargo is not on the Bash PATH, STATE.md:41-42).
- A DHM fixture: `--mode geo-terrain --dhm-dir tests/fixtures/dhm --elevation-trust v1 --regional-elevation-only --land-cover=false --master-origin-lat … --master-origin-lng … --elevation-min -20 --elevation-max 175 --ground-level 42`, with four synthetic 100 px @ 10 m tiles (§1.4 decode rule) generated by a script. `--land-cover=false` is mandatory: `land_cover.rs` has no offline gate (`:744-749`); with a master origin set the 7-day sweep does not run (`main.rs:174-176`) and the IQR filter is skipped (`mod.rs:270-272`), matching Meld.

### 5.3 Building on this box

`cargo 1.98.0` / `rustc 1.98.0`, `stable-x86_64-pc-windows-msvc`, at `%USERPROFILE%\.cargo\bin` (STATE.md:41-42; VS 2019 Build Tools carry the only VC x64 tools). `cargo build --release --bin arnis` with default features (gui), which is what CI, the release (`.github/workflows/release.yml:117-126`) and the harness (`golden_hash.sh:49-51`) hash: **4 min 42 s** measured (`data/build-logs/baseline-78215bd.log`, tail). Release has `overflow-checks = true` and `lto = "thin"` (`Cargo.toml:11-13`). Before a commit: `cargo fmt -- --check`, `cargo clippy --all-targets --all-features -- -D warnings` (`ci-build.yml:26-30`, fails today), `cargo test --release --all-targets --all-features` (`:39-45`). Bump `Cargo.toml:3` and `tauri.conf.json:4` together (`release.yml:57-70`); the banner prints `<sha>-dirty` from `build.rs:15-37` and Meld's version probe reads clap's trailing `arnis 3.1.8` line (`arnis_cmd.py:218-223`). Drop the exe next to `meld_launch.py` and restart Meld. Re-pin: STATE.md still says `78215bd`; pin `arnis` at the id-fix commit and Meld at `602449e` [PROPOSED].

## 6. Risks and unknowns

| # | risk | the line that makes it real | status / mitigation |
|---|---|---|---|
| 1 | Cave blocks render as signs/torches/grates/lanterns/cauldrons; CI red | HEAD `block_definitions.rs:385-396,1356-1367`; `caves/decoration.rs:509-620` | 🟢 proved; fix in §4.2 |
| 2 | Golden gate blind to names, properties, block entities, biomes, terrain | `common.rs:632-663,287-291`; `java.rs:461`; `golden_hash.sh:110-115` | 🟢; guards in §5.2 |
| 3 | Missing DHM tile silently becomes AWS terrain or flat ground | `mod.rs:192-216,232-255`; `ground.rs:314-345`; `args.rs:526-536` | index + Err wording + `regional_elevation_only` (§1.4) |
| 4 | Elevation lock clamps basins and reclaimed land to sea level | `postprocess.rs:1335`; `survey.py:2-5`; projects lock `0–180` | §1.6 [PROPOSED] |
| 5 | The four repair stages smooth 0.4 m data | `mod.rs:276,316-326`; `postprocess.rs:99-103,180,208,215` | §2 |
| 6 | Water mask is still ESA 10 m; quays within 2 m of water | `postprocess.rs:388-393,418-421` | raise-only + reclassify (§2.2); DTM zero-burn mask later |
| 7 | Floor slip at cell edges | `mod.rs:106-107`; `coords.py:206-213` | 🟡; anchored sampling retires it for DHM (§1.4) |
| 8 | `--prewarm-elevation` full-samples a local provider | `mod.rs:425-429`; `prefetch.py:478-491` | `dhm_dk` arm (§1.4) |
| 9 | `--elevation-map` on a country bbox decodes ~45k tiles | `elevation_map.rs:36-46` | v1 refuses > 64 squares |
| 10 | 7-day cache sweep | `cache.rs:6-7,211-221`; `main.rs:174-176` | store outside `arnis-tile-cache` |
| 11 | Sign NBT form and hanging-sign states on 26.2 unverified on this build | HEAD `mod.rs:1030-1080`; REFERENCE §11.2 | 🔴 read back one of each |
| 12 | Stray/duplicate doors from `doors.rs` and orphan OSM entrance nodes | `data_processing.rs` HEAD `:174`; `doors.rs:20-23` | §4.7 items 2 and 6 |
| 13 | Grate replaced on steep cells | `ground_generation.rs:822-843` | §4.7 item 3 |
| 14 | Signs silently skipped where a decoration occupies the cell | `buildings.rs:5302-5330`; `nordgrund.rs:251,1049-1050` | count and log (§4.4) |
| 15 | Emitter material strings unrecognised (`timber_framing`, `eternit`, `plastic`) | `block_definitions.rs:2017-2078` | fix `WALL` (§3.3) |
| 16 | Enriched tile re-downloaded after the TTL; forced `.pbf` bake clobbers | `prefetch.py:584-593,329-334`; `osm_pack.py:501` | TTL 0 already in the projects; runbook note |
| 17 | Node ids exceed `2^43` if `id_lokalId` ≥ 3.0·10⁹ | `emit_geodk.py:307` | assert (§3.2) |
| 18 | `level.dat` keeps the 1.21.x template version while chunks carry 4903 | `world_utils.rs:350-357,305-306` | CLAUDE.md read-back check vs code: reconcile (STATE.md item 1) |
| 19 | ETRS89 vs WGS84 ≈ 0.9 m drift by 2026 | `ign_spain.rs:15-16`; `emit_geodk.py:22-23` | consistent inside our data; OSM offset ≤ 1 m, accepted |
| 20 | Border cells: foreign land inside a DHM cell's halo | §1.4 `accepts`/index policy | user's call once a border cell is walked |
| 21 | Business names: OSM POIs only; CVR/DAR ground-floor rule not built | `emit_geodk.py:280-286`; decisions.md E | later, needs the Adresse hop (CONSULT §9) |
| 22 | STATE.md and the task pin are two commits behind | `git log` | re-pin after §4.2 |
