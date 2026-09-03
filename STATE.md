# STATE.md

Where the work is right now. Rewritten in place at the end of every session, never appended.
Kept short. File name and format are [PROPOSED].

## 3 Sep 2026

**Read `research/session-2026-09-03-handover.md` first.** It is the review document for this
session: what was built, what was measured, what is proposed and what is open. This file is the
short version.

- **The pivot is confirmed by a walk.** [USER 3 Sep 2026] *"the arnis/meld server-pilot looks MUCH
  better than our server-build9"* (decisions.md 7). Work item 1 is closed.
- **Three worlds exist, one origin, same coordinates in each.** Walk them at:
  `data\server-pilot` :25565 (plain Arnis+Meld), `data\server-build9` :25566 (the old baseline),
  `data\server-geodk` :25567 (work item 4: GeoDanmark footprints + BBR attributes + DAR doors),
  `data\server-nordgrund` :25568 (that plus the §16 features). **#2 and #3 have not been walked.**
- **Forks:** branch `nordgrund` in both, pushed. `Farsinuce/arnis` carries the §16 features, the
  `addr:*` parser exception and work item 3; `Farsinuce/meld` carries the settings passthrough.
  `meld\arnis.exe` is our build of that branch (`--version` prints the commit).
- **Work item 3 (DHM provider + repair gate) is code-complete and unit-tested but has never
  rendered a world.** Run it next: `tools\meld_pilot.py --name aarhus-dhm --nordgrund all
  --dhm data\raster --elevation-trust v1`, then A/B the harbour front against world #3. Read
  handover §5 first: the height profile (decisions.md I) should be settled before that run,
  because the first merge wins it.
- **Adversarial review of the fork code found 10 real defects, all fixed** (handover §4). The
  worst: our new block ids shadowed the fork's cave blocks, which the golden gate structurally
  cannot catch because it hashes ids, not names.
- **Awaiting the user:** the walk; decisions.md F, I, K, L, M.
- **Machine** (3 Sep 2026): Python 3.12.9, Rust 1.98.0 at `%USERPROFILE%\.cargo\bin` (not on the
  Bash tool's PATH), JDK 25.0.4, 16 threads, 32 GB, D: ~190 GB free. Meld: 4 workers × 4 threads.
- **Time-critical:** DAWA closes 1 Oct 2026 (`decisions.md` G); the 829 MB address CSV is still
  not archived.
- **Pins:** arnis base `78215bd` (v3.1.8), meld base `5c1353e` (v1.9.8), `louis-e/arnis` main was
  `e431474` on 2 Sep 2026. 35 source files pinned in `manifest.json` (25 DHM tiles, GeoDanmark,
  BBR, DAR for kommune 0751).
