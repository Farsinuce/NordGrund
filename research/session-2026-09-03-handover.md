# Session handover, 2–3 Sep 2026 — for review

Written for the next session (Fable, after the usage limit resets). It covers PRIMER §5 work
items 1, 3 and 4 plus the REFERENCE §16 wish list. Everything claimed here has an artefact on
disk or a commit; where something is untested it says so. Marks: 🟢 measured, 🟡 derived,
🔴 open. **Model note:** items 1, 4 and §16 were built by Fable 5.1; the last stretch (item 3, the
elevation provider and the repair gate, and the review fixes from `4a16f690` on) was built by
Opus 5 after the Fable limit was reached. Judge it accordingly.

## 1. What the user asked, and what exists now

| ask | state | walk it at |
|---|---|---|
| Work item 1: stand up Meld + the fork unmodified, generate the Aarhus pilot | **done, walked, accepted** — [USER 3 Sep 2026] *"the arnis/meld server-pilot looks MUCH better than our server-build9"* (decisions.md 7) | `data\server-pilot`, port 25565 |
| Work item 4: enrichment emitter v1 (GeoDanmark footprints + BBR attributes) | **done, generated, not yet walked** | `data\server-geodk`, port 25567 |
| REFERENCE §16 wish list (doors, torches, address signs, name boards, lanterns, manholes) | **done, generated, reviewed, fixed, not yet walked** | `data\server-nordgrund`, port 25568 |
| Work item 3: national elevation provider + the repair-stage gate | **code done, unit-tested, NOT yet run on a world** 🔴 | — |
| baseline for comparison | build 9, untouched copy | `data\server-build9`, port 25566 |

Launch any of them (all creative, flight on, offline mode, `generate-structures=false`):

```
cd D:\ai\NordGrund\data\server-nordgrund
& "C:\Program Files\Java\jdk-25.0.4\bin\java.exe" -Xmx3G -Xms1G -Dfile.encoding=UTF-8 -jar server.jar nogui
```

All four worlds share one origin, so the same coordinates work in each: seam cross and spawn at
(0, 0); tile centre (127, −201); Aarhus H (460, −122); Domkirken (832, −879); ARoS (125, −568);
Dokk1 (1018, −512); Den Gamle By (−384, −1013); Marselisborg Slot (453, 1481). Sea level is Y 62.

## 2. Repos, branches and pins

| repo | branch | head | contents |
|---|---|---|---|
| `Farsinuce/NordGrund` (this workspace, public) | `main` | pushed | docs, `decisions.md`, `tools/`, `research/`, `manifest.json` |
| `Farsinuce/arnis` (public fork of Teddy563/arnis) | **`nordgrund`** (base `78215bd` = v3.1.8) | see below | the §16 features, the parser exception, item 3 |
| `Farsinuce/meld` (public fork of Teddy563/meld) | **`nordgrund`** (base `5c1353e` = v1.9.8) | `602449e` | one commit: the `nordgrund` setting passthrough |

Arnis `nordgrund` commits, oldest first:

1. `3f47e6f9` parser keeps `addr:street`, `addr:housenumber`, `addr:postcode` (everything else in
   `addr:*` stays filtered), with a unit test.
2. `b8972b8b` the §16 features behind `--nordgrund`.
3. `d67beaf0` signs/torches may replace the building's own facade relief; no `minecraft:bed` block
   entities for DataVersion ≥ 4903.
4. `4a16f690` the adversarial review's fixes (below).
5. *(this session's last commit)* work item 3: the DHM provider, `--dhm-dir`,
   `--elevation-trust`, the prewarm preflight, the block-id regression tests, air-only lanterns.

The binary in `meld\arnis.exe` is our build of that branch, not the pinned release. `--version`
prints the short commit. Record its sha256 in `STATE.md` whenever it changes.

## 3. What was verified, with numbers 🟢

### The three generated worlds (each 4 cells, 64 regions, 65,536 chunks, ~78 s)

| | #1 `aarhus-pilot` | #2 `aarhus-geodk` | #3 `aarhus-nordgrund` |
|---|---|---|---|
| buildings from | OSM (10,628 ways in the cells) | GeoDanmark (18,691 footprints) | same as #2 |
| stored bytes/chunk | 4,392 | 4,316 | 4,357 |
| chunks with a door or glass | 33,499 | 34,264 | 34,264 |
| DataVersion (chunks) | 4903 | 4903 | 4903 |
| corruption signals on a 26.2 boot | 0 | 0 | 0 |

World #3 feature counts (`tools/probe_features.py`): 953,949 dark-oak door blocks, 16,326 wall
torches, 15,658 pale-oak wall signs, 1,297 hanging signs, 56,091 lanterns, 12,202 copper grates,
12,398 water cauldrons, and glowstone down to 476 blocks (from 21,290 in #1). Block entities:
11,632 signs, 1,074 hanging signs, 0 beds. At the 369 emitted entrance nodes inside the cells:
**a door within one block on 100 %**, a sign on 93 %, a torch on 98 %.

Live 26.2 server readback (`data get block`, chunks force-loaded): a wall sign returns
`["Carl Blochs", "Gade", "42", ""]` and a hanging sign `["Godsbanens", "Åbne", "Værksteder", ""]` —
bare strings, four messages, Danish letters intact, no serialization error. This settles
REFERENCE §11.2's open question for 26.2.

### Determinism

Regenerating one cell twice gave **block-identical** output (16,384/16,384 chunks) while the
region files' sha256 differed: the fork writes chunk palettes in varying order. The gate is
`tools/world_diff.py` (decodes and compares blocks, biomes, block entities, heightmaps), not file
hashes. PRIMER §3 and §4 still say "hash identically" and are yours to amend (decisions K).

### Elevation, the "measure first" rider

Mapterhorn's Danish z16 tiles versus the DHM 0.4 m tiles over 25 km², n = 35,762 samples: median
difference 0.00 m, 96.5 % within 0.5 m, 1.0 % beyond 2 m (building edges, not datum). Full table
in `research/elevation-mapterhorn-vs-dhm-2026-09-03.md`. **So item 3 buys a pinned vintage, no
tile server, real harbour depths and the repair gate — not a visible fidelity jump.** The visible
part is the gate.

## 4. The adversarial review of the fork code 🟢

Three reviewers over the diff (Rust correctness, Minecraft 26.2 correctness, determinism), two
skeptics per finding: 10 confirmed, 3 refuted. All 10 are fixed on the branch. The one that
matters most:

> **Block ids 270–275 were already the fork's `calcite`, `amethyst_block`, `budding_amethyst`,
> `basalt`, `smooth_basalt` and `obsidian`.** Rust's `match` takes the first arm, so my six new
> arms renamed the cave blocks in every `--caves` world — with `--nordgrund` absent. The golden
> gate could not see it because it hashes block **ids**, not names, and the file's `#![allow(unused)]`
> swallowed the `unreachable_patterns` warning.

Fixed by moving our blocks to ids 450–455, adding `#![deny(unreachable_patterns)]` to that file,
and adding three regression tests that assert the cave blocks keep their names and that our ids
stay in their own range. The other nine: a wall hanging sign attaches at its side, so its `facing`
runs along the wall, not out of it; the single-floor lantern hung one block too low with air above
it; a closed ring's repeated first node placed two doors at corners; entrance cells inside a
building passage got a door across the road; floors with no 10-grid point got no lantern; torches
and signs needed a wall to hang on; lanterns must be written air-only so they never replace a wall;
clippy under `-D warnings`. Refuted: the bbox clipper erasing node tags (buildings never reach that
path in tile-invariant mode).

**Method note worth keeping:** the golden-hash gate proves ids, not names or block states. A change
that only alters `Block::name()` or `properties()` passes it. Reviewing the diff caught what the
gate structurally cannot.

## 5. Work item 3 as built (Opus 5, needs review and a run) 🔴

New file `src/elevation/providers/dhm_dk.rs` plus two flags:

- `--dhm-dir <DIR>`: a directory of `DHM_TERRAEN_1km_<northing-km>_<easting-km>.tif`. Absent, the
  provider reports no coverage and provider selection is exactly as before (unit-tested).
- `--elevation-trust off|v1`: `v1` skips the 5×5 anomaly median (which erases any edge over 6 m:
  quay walls, cliff tops, silo edges), sets the built-up Gaussian to σ = 0 and the coastal pull to
  0, and makes water levelling **raise-only** so basins still fill while shoreline cells keep their
  measured height. Versioned like `--river-bed`: a retune ships as `v2`.

Design points a reviewer should check:

1. **Sampling by absolute coordinate.** A new additive trait method `fetch_raw_anchored` carries a
   `GridAnchor { origin_lat, origin_lng, scale, min_x, min_z }`, supplied only when a master origin
   is set and the grid was not capped. Node (gx, gy) is block (min_x + gx, min_z + gy), and the
   block **centre** maps to one (E, N) that any Meld cell computes identically. Every other
   provider keeps the default, which forwards to `fetch_raw` unchanged. The +0.5 block-centre
   convention differs from the fork's existing providers, which sample the node's north-west
   corner: deliberate, and worth a second opinion.
2. **UTM.** Hand-written Krüger series, WGS84/GRS80 → EPSG:25832, no new crate. Unit-tested against
   pyproj 3.7.2 at five Danish points to under a millimetre.
3. **Bilinear**, via the fork's own NaN-aware `blend_finite_samples`, following pixels into the
   neighbouring square at a tile edge (tested: a plane continues across the boundary with no step).
4. **Fail closed.** A square that is neither on disk nor listed in an optional `dhm_sea.txt` is an
   error whose text contains `offline: ` and `not cached`, which is what makes Meld mark the cell
   `elevation-not-baked`. ⚠️ The fork still falls back to AWS on `Err` unless
   `--regional-elevation-only` is set, so **the Meld project must set `regional_elevation_only`**
   for the fail-closed path to hold. That pairing is not yet in `tools/meld_pilot.py`.
5. **Preflight.** `--prewarm-elevation` now surveys the squares and fails listing the missing ones,
   so Meld's terrain bake is the preflight for a frozen build.
6. **`dhm_sea.txt`.** The pilot needs 25 squares and Denmark publishes only 24: `6221_576` is open
   water in Aarhus Bay and `GetRasterFile` 404s for it (verified 3 Sep 2026). Such squares are
   declared in `data/raster/dhm_sea.txt` and read as 0.000 m, which is what the DTM burns the sea
   to anyway. ⚠️ A 404 means "no Danish terrain published here": open sea around the coast, but
   FOREIGN LAND at the German border and in the Sound. A national run needs that distinction — a
   border square wants a neighbour's DEM, not a zero.

Independently verified while building it: the five projection test vectors match pyproj 3.7.2 to
under a millimetre (re-run directly, not taken from the design brief), and the block-centre pixel
maths matches rasterio's own sampler at three pilot coordinates.

Status: compiles, clippy clean, 7 provider unit tests pass, full suite passes, golden gate 5/5
unchanged. **Not yet run on a world.** The next session should generate world #4 with
`--dhm-dir data\raster --elevation-trust v1 --regional-elevation-only` and A/B the harbour front
against world #3, which is where the gate should show.

⚠️ Before that run, note `research/fork-design-brief-2026-09-03.md` §1.6: with the manual lock at
0–180 m every sea-floor sample below 0 m clamps to sea level, so the DHM's real harbour depths
(down to −14.8 m in the pilot area) never appear. Its proposal is `--elevation-min -20
--elevation-max 175` with `ground_level 42`, keeping Y = 62 + metres. **First merge wins the height
profile**, so this is a decision to take before the first production cell, not after.

## 6. Tools written this session (all in `tools/`, all run from the repo root)

| tool | what it does |
|---|---|
| `datafordeler.py` | Datafordeler FileDownloads client; picks the newest generation, verifies md5, pins every file in `manifest.json` |
| `dar_chain.py` | DAR address chain for one kommune → `data/derived/dar_0751.csv` (114,347 rows, 94.6 % with a GeoDanmark building id) |
| `emit_geodk.py` | the enrichment emitter: GeoDanmark + BBR + DAR + manholes → Meld's z11 OSM tiles |
| `meld_api.py`, `meld_pilot.py`, `meld_wait.py` | drive Meld headless; `meld_pilot.py` is the whole pilot recipe |
| `world_check.py` | read-back gate on a generated world |
| `world_diff.py` | block-level diff of two region folders (palette order ignored) |
| `probe_features.py` | counts the §16 feature blocks, reads sign texts back, measures the door hit rate |
| `mcserver_check.py` | boots a real 26.2 server on a copy, scans for corruption, hashes regions before and after |

Pinned source data in `data/` (gitignored, 35 files in `manifest.json`): 25 DHM Terræn tiles,
GeoDanmark buildings and manhole covers for kommune 0751, BBR buildings/units/floors/stairwells,
DAR access points, house numbers and street names.

## 7. What needs the user, in priority order

1. **Walk worlds #2 and #3** and judge them against #1 (PRIMER §4). Everything after this depends
   on that judgement.
2. **decisions.md I** — the height profile, now with the harbour-depth question from §5 above.
   This is the one that gets expensive to change later.
3. **decisions.md L and M** — the emitter's tag choices and the §16 block choices. Both are
   aesthetics, which are the user's call; each feature is a separate `--nordgrund` switch.
4. **decisions.md F, K** — re-review PRIMER §3, and the determinism wording.

## 8. Known open items 🔴

- Item 3 has never rendered a world (§5).
- The pairing of `--dhm-dir` with `--regional-elevation-only` is not yet in the recipe.
- Meld logs `[Export] post-merge hook warning: unsupported operand type(s) for /: 'str' and 'str'`
  on every merge with export off. Harmless here, upstream bug, not located.
- The fork copies a 1.21.4 template `level.dat` whatever `--mc-version` says; chunks are right and
  the 26.2 server rewrites the file on first load. Small patch, not done.
- Outside the four cells the world is the template's superflat grass plane at Y −62, so every cell
  edge is a ~124-block cliff. Meld never passes the fork's `--void`. One setting to add before a
  production run, or a world border.
- The emitter's business names come from OSM shops and amenities near a door, not from CVR. The
  CVR→DAR chain (CONSULT §9) is the real source and is not built.
- Biomes: taiga on 36 % of chunks, desert on 2.5 %, as REFERENCE §9.1 predicted. Work items 8–9.
