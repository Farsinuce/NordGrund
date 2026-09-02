# STATE.md

Where the work is right now. Rewritten in place at the end of every session, never appended.
Kept short. File name and format are [PROPOSED].

## 3 Sep 2026 (session of 2–3 Sep)

- **Workspace:** this folder is the public repo `Farsinuce/NordGrund`. Forks cloned and pinned:
  `arnis\` = `Farsinuce/arnis` at `78215bd` (v3.1.8, remotes `upstream` = Teddy563, `louis-e`),
  `meld\` = `Farsinuce/meld` at `5c1353e` (v1.9.8). Pinned binary `meld\arnis.exe` (release asset,
  sha256 `09d326dc…5544`). Meld venv `data\venv-meld`. Tools in `tools\`, numbers in `research\`.
- **Work item 1 is generated, not yet walked.** Project `aarhus-pilot`: four 2048-block cells whose
  borders cross at the centre of tile 6223_574 (x = 0 and z = 0 in game). 78 s to generate, 288 MB,
  65,536 chunks at DataVersion 4903, read-back PASS, block-identical across three generations of
  one cell, boots clean on 26.2. All numbers: `research/pilot-run-2026-09-02.md`.
- **Walk:** `data\server-pilot` (port 25565, world `meld-pilot`, a copy) and `data\server-build9`
  (port 25566, `denmark-test`, a hash-verified copy of build 9). Launch lines in CLAUDE.md.
- **Meld runs headless** (CLAUDE.md, Commands); the API token is in `data\meld-data\session.json`.
  `tools\meld_pilot.py` is the whole recipe; scale must be set before the origin.
- **Found, to act on:**
  1. The fork stamps `level.dat` DataVersion 4189 (1.21.4) whatever `--mc-version` says; chunks
     are right. The server rewrites it on first load. Small fork patch; add to the §5 shortlist.
  2. Region-file bytes are not reproducible (chunk palettes written in varying order); the world
     is. Gate on `tools\world_diff.py`, not file hashes; a palette-sort patch would restore hashes.
  3. Meld logs `[Export] post-merge hook warning: unsupported operand type(s) for /: 'str' and
     'str'` on every merge (export off, harmless). Upstream bug to report or patch.
  4. Biomes: taiga in 36 % of chunks, desert 2.5 %; glowstone in 33 % of chunks (interiors).
     Expected (CLAUDE.md, PRIMER §1); work items 8–9.
- **Awaiting the user:** the walk (PRIMER §4); decisions.md F (re-review PRIMER §3) and the new
  [PROPOSED] items I (height profile), J (settings base), K (determinism gate wording).
- **Next:** work item 2 (the harness: `tools\` is the seed), the `level.dat` patch, then item 3.
- **Machine** (verified 2 Sep 2026): Python 3.12.9; Rust stable at `%USERPROFILE%\.cargo\bin`
  (not on PATH in the Bash tool); JDK 25.0.4 at `C:\Program Files\Java\jdk-25.0.4`; 16 threads,
  32 GB, D: 194 GB free. Meld's `/api/recommend`: 4 workers × 4 threads.
- **Time-critical:** DAWA closes 1 Oct 2026 (`decisions.md` G).
- **Pins:** as above; `louis-e/arnis` main was `e431474` when fetched on 2 Sep 2026.
