# CLAUDE.md

**NordGrund - Hele Norden bygget på geodata.** The Nordic countries in Minecraft at 1:1, one country
per server, Denmark first, on our forks of Arnis and Meld plus an enrichment layer of our own
(PIVOT-PRIMER §2). Claude writes the code. The user walks the world, edits tables and ratifies.

This file is routing plus the rules a fresh session would otherwise break. The growth rule at the end applies from the first session; the user ratifies it at the first review.

## Read this first

| when | read |
|---|---|
| every session | [PIVOT-PRIMER.md](PIVOT-PRIMER.md): goal §1, stack §2, day-one configuration §3, acceptance test §4, work items §5, decided vs open §6, glossary §7. Then `STATE.md` and `decisions.md`. |
| touching the fork, Meld, elevation, versions, formats, licensing, Danish data, the old repo | [PIVOT-REFERENCE.md](PIVOT-REFERENCE.md) §8–19: §8 first (the three facts that matter most), §13 conventions, §18 what to copy, §19 beware of old data |
| before designing any pass | the matching section of [PIVOT-CONSULT.md](PIVOT-CONSULT.md) §1–10, facts and measurements only. §11 is time-critical: check it every session until its items are closed. |

The old repo is `d:\ai\KlodsDanmark` (github.com/Farsinuce/KlodsDanmark, private). In general, it should NOT be used, as its documentation is vibe coded without human review, and it has drifted. If we desperately need to access it, Read CONSULT first; open one of its `research/` records only when REFERENCE or CONSULT
names it. Copy as little as possible (decisions.md 2): only the files under *Precious*.

The PIVOT files were written by Claude and are edited by the user by hand. CONSULT cites upstream only, at `7f8236f`, `3918513` and `c7b5f19`. Re-grep at our fork's
base commit before trusting any line number: first-pass AI reads of Arnis ran a 25–53% claim-error
rate (CONSULT header).

## How the user works (auto-memory holds the reasons; this copy travels with the repo)

- **Walking the world is the yardstick** (PRIMER §1). After a code clean-up closed most open bugs
  behind a green harness: *"NOWHERE near what I had hoped for"* (12 Aug 2026). Say beforehand when
  a change shows nothing new on screen. Lead every report with what the world looks like now.
- **Aesthetics are theirs, but never hand them a blank form** (PRIMER §1): *"Of course I want
  something pre-filled with good suggestions. I just want the ability to change it if e.g. 'gravel'
  is suggested for roads, when I know I want 'grey_concrete'"* (12 Aug 2026). Deliver the whole
  table, a concrete block per row.
- **Thorough over expedient**: *"We need proper master data"* (11 Aug 2026). A long-lived hobby
  project, not a deadline. Name a shortcut as a shortcut in the same breath, with what replaces it.
- **Disagree openly**: *"If you ever disagree with an approach that I suggest, don't hold back.
  Avoid sycophancy"* (15 Aug 2026). Give the recommendation you believe, with the evidence, before
  doing work on the weaker premise.
- **Be concise.** Said outright on 17 Aug 2026. Lead with what changed or what is wrong. Name the
  file and what changed; do not re-summarise an edit in chat. This governs prose, not rigour.
- **Until the production run, test data is disposable**: *"We're just testing here. If we need to
  download new files or refresh a token after Sunday, we'll just do so, no sweat"* (11 Aug 2026).
  Expiries and rollovers are facts with a recovery path, not deadlines. *Precious* is the exception.
- **Griefing is handled.** They hosted a copy of the state's 2014 Denmark world for about a year,
  ~8,000 unique players, with WorldGuard and GriefPrevention. The state's own project had died of
  banning building and chat, not of griefers. Do not relitigate griefing.
- **Downloads:** check the size first. Under 5-6 GB per file, just take it. Over, ask.
- **Docs: lean, plain English** (REFERENCE §13): *"we want clean, concise
  documentation overall"* (21 Aug 2026); no PhD jargon.

## Decisions

Only calls in the user's own words, or their own hand edits to a PIVOT file cited by section, are
settled. The old repo's "user" tags, `status = "user"` rows and `decisions.md` are provisional, not
settled: *"It was all just vibe coded"* [USER 30 Aug 2026]. Measurements with an artefact still
count. The register is `decisions.md` in this workspace. Tag `[USER <date>]` with the quote, or
`[PROPOSED]`. A `[PROPOSED]` call is never cited back as a veto: if one blocks a recommendation,
re-ask. The Meld, tree/cave-pack, CVR-name and Danmarks Kirker licence questions are closed by the
user (decisions.md 1 and 5); do not reopen them. Still 🔴: ODbL share-alike if the enriched cache
is ever distributed (REFERENCE §14) and Norway FKB (CONSULT §11 item 2).

## Conventions

REFERENCE §13 binds. In short: measure with sample size and date, and mark 🟢 verified / 🟡
derived / 🔴 open. Fail closed, and prove every check and every error branch. Key every random or
fitted decision on stable feature IDs or world coordinates. Pin one fork commit and one Meld
commit per country campaign. Never junction a data directory into a git worktree. Fork changes:
PRIMER §2 (additive, behind flags, hand-ported) and REFERENCE §10.4 item 5 (a new flag must appear
in `arnis --help`). Verification: PRIMER §4 and REFERENCE §12 (a green exit is not a verified
world; track bytes per chunk). Credentials: REFERENCE §17. Added here [PROPOSED]: before designing
any rendering pass, read how Teddy563/arnis and louis-e/arnis do it and cite file:line at the
pinned commit.

## The workspace [PROPOSED, the user's call]

Regenerated from the real tree on 3 Sep 2026. The root is the public repo `Farsinuce/NordGrund`
(PRIMER §2's enrichment repo, holding the docs); forks and data are clones and regenerables, gitignored.

```
d:\ai\NordGrund\   this file, decisions.md, STATE.md, the PIVOT files, tools\, research\
  arnis\  meld\    our forks: Farsinuce/arnis at 78215bd (v3.1.8, remotes upstream=Teddy563, louis-e)
                   and Farsinuce/meld at 5c1353e (v1.9.8). meld\arnis.exe is the pinned release
                   binary, placed by hand (sha256 in STATE.md); keep data\meld-data\bin\ empty
  tools\           meld_api.py, meld_pilot.py (the pilot recipe), meld_wait.py, world_check.py, world_diff.py, mcserver_check.py
  data\            gitignored: meld-data\ (MELD_DATA_DIR), meld-cache\ (MELD_CACHE_DIR), venv-meld\, downloads\, server-pilot\, server-build9\
```

Start every session at the workspace root: a parent CLAUDE.md loads from a subdirectory, but a
session started inside `arnis\` keys its auto-memory on that clone. Never `@`-import a PIVOT file:
imports expand at every launch and the three files are over 100 KB. Per-fork rules can go in
`.claude\rules\` with a `paths:` header, loaded only when a matching file is read.

**Commands** (each pasted from a run that worked on 2–3 Sep 2026; PowerShell, from the root):

```
$env:MELD_DATA_DIR="D:\ai\NordGrund\data\meld-data"; $env:MELD_CACHE_DIR="D:\ai\NordGrund\data\meld-cache"; $env:PYTHONUTF8="1"
data\venv-meld\Scripts\python.exe meld\meld_app.py --no-tray --no-open --no-statusbar   # headless :5630; API token in data\meld-data\session.json (tools\meld_api.py)
data\venv-meld\Scripts\python.exe tools\meld_pilot.py --dry-run                        # or without, to generate; then tools\world_check.py <world>
data\venv-meld\Scripts\python.exe tools\mcserver_check.py data\server-pilot            # boots, scans, stops
cd data\server-pilot; & "C:\Program Files\Java\jdk-25.0.4\bin\java.exe" -Xmx3G -Xms1G -Dfile.encoding=UTF-8 -jar server.jar nogui
```

**Precious** (REFERENCE §18's three gitignored files; everything else is regenerable, §13). `.gitignore`
lists `.env`; it is not copied yet. The build-9 world is also in the old repo's
tracked `archive.7z` (commit 4c8fae2), identical to `testserver\denmark-test` on 1 Sep 2026; walk a
copy, never that one, because loading dirties chunks.

## Day-one checklist

PRIMER §3 is the runbook. It lists the flags and Meld settings that fail silently on the first run
and was re-verified 1 Sep 2026 against Meld `5c1353e`: four Meld defaults (scale, buildings, bake
lighting, snow) are wrong for us. Check the command line Meld builds (`src/arnis_cmd.py`) and its
settings against §3 before the first cell, and again after every fork or Meld merge. Meld's
settings are a JSON blob under `project.json` and a local API, so Claude drives it without the
browser (decisions.md B). Not in §3:

| set | to | or else, silently | ref |
|---|---|---|---|
| height profile (Meld `world_min_y`, `world_max_y`, `ground_level`, `height_headroom`, `height_underroom`) | pinned before the first merge | first merge wins; later cells lose content on load | REFERENCE §10.5 |
| `--road-grade`, `--river-bed` (Meld `road_grade`, `river_bed_v1`, both off) | decided before the first production cell | mid-project toggles mismatch cells | §10.4 |
| `--offline` cache miss | treat `cell_health.json` "elevation-not-baked" as FAILED | a missing tile becomes flat ground; a `.missing` marker writes ocean | §9.2 |
| bbox per run | Meld cells, never a country box | may be capped at 16384² and upsample | §9.2 |
| master origin | one per country, set once; the pilot's own is fine (decisions.md C) | the cross-run guard checks only scale and origin | §9.4, §10.5 |

Read back before walking, beyond PRIMER §3's own checks (`tools\world_check.py` does them): every
chunk carries the target's DataVersion (4903 for 26.2; the fork stamps `level.dat` 4189 until the
first server load, STATE.md); the ground is not flat; the 1 km pilot spans 1,000 blocks; buildings
exist and the logged command line has no `--no-buildings`; at least one chunk has a biome palette
with more than one entry (CONSULT §4: biome failure is invisible at both ends). Never run
`--forceUpgrade` or "Optimize World" (REFERENCE §12).

Expect, do not fix, in the pilot:

- Woodland may come out taiga, or a whole cell one biome (REFERENCE §9.1, CONSULT §4).
- X/Z are origin-relative, not grid coordinates (§9.4; open, PRIMER §6).
- Roughly a third of build 9's buildings: OSM is the only footprint source for now (CONSULT §7).
- Region-file hashes differ between identical runs (palette order); compare with `tools\world_diff.py`.
- Beyond the generated cells: a flat grass plane at Y −62 and a cliff (Meld never passes `--void`).

## How this file may grow or be revised

- Hard cap 200 lines, Claude Code's own guidance. Over 150, cut before adding.
- A line goes in only if it changes how the next session behaves and will still be true after the
  next work item lands. Progress, counts and machine facts go to `STATE.md` (rewritten in place,
  never appended, kept short). Calls go to `decisions.md`. Numbers go to `research/`.
- When a PRIMER §5 work item is done, first delete what it made stale here, then add at most a
  pointer. The workspace section is regenerated whole from the real tree and real runs.
- Facts about the user change only on their word, quoted. Never let `/init` or any tool rewrite
  this file whole. Ask the user to re-review it whenever a section is regenerated, then date the
  "User review" line at the top.
- When our project is well-established, we should completely rewrite this CLAUDE.md. Right now it focuses on starting a new project, but eventually we want it be a foundation for our then-ongoing project, which begs a rewrite.
