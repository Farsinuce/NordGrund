# decisions.md

The register of calls for NordGrund. `[USER <date>]` is the user's own words, quoted, or their own
hand edit to a PIVOT file, cited by section. `[PROPOSED]` is Claude's suggestion and is not
settled. Close items in place with one line; never renumber. File name and format are [PROPOSED]
(PRIMER §6 asks only for "the new project's own decisions file").

## Settled by the user

1. [USER 29 Aug 2026] The pivot: fork `Teddy563/arnis` and `Teddy563/meld`, *"molding the code
   to our liking"*; base on the Meld fork and cherry-pick upstream; 1:1; one country per server;
   Denmark first; the old repo is the a vibe coded archive (PRIMER §6), which we usually want to try to avoid having to use. Meld's licence: assume
   Apache-2.0 and do not relitigate (said in chat, paraphrased in REFERENCE §14).
   [PROPOSED] Upstream features are hand-ports in practice: a simulated cherry-pick of
   `roof:height` conflicted in 18 hunks (PRIMER §2). Country two: the 29 Aug memory note has
   Iceland, PRIMER §6's 30 Aug line has Norway. Ask which.
2. [USER 30 Aug 2026] Copy as little as possible from the old repo: *"littered with non-reviewed
   vibe coded spaghetti-code/assumptions... I'd rather start fresh"*. Only the gitignored files in
   REFERENCE §18 come across.
3. [USER 30 Aug 2026] The old LiDAR roof fitter `roofform.py`: *"not certain whether we want this,
   as it doesn't give as visually pleasing results as Arnis"*. Reference only; rewrite fresh if
   measured roofs win an A/B. REFERENCE §18.
4. [USER 30 Aug 2026] The wish list under REFERENCE §16 "Extra custom features" is user-written:
   manholes with a cauldron below, ground-floor lanterns, a torch inside every entrance, pale oak
   street-and-number signs, hanging name signs on non-residential buildings.
5. [USER 1 Sep 2026, hand edits] Licences closed for this hobby project:
   - Meld's tree and cave packs: *"we assume it's permissive for our hobby project, and that's
     fine"* (REFERENCE §14).
   - CVR names on signs despite reklamebeskyttelse: *"completely fine for this hobby project"*
     (CONSULT §9).
   - The Danmarks Kirker plans: *"we assume it's okay for our hobby project"* (CONSULT §10).
6. [USER 1 Sep 2026] Spelling: *"our new NordGrund workspace"*, and the folder and workspace file
   are `NordGrund`. PRIMER line 8 (30 Aug) says `Nordgrund`; fix it to match [PROPOSED].

## Awaiting the user

- A. Closed 2 Sep 2026 [USER 2 Sep 2026]: *"we just fork it and our repo will be public."* Done the same
  day under the `Farsinuce` account: public forks `Farsinuce/arnis` (of Teddy563/arnis, pinned
  `78215bd` = v3.1.8) and `Farsinuce/meld` (of Teddy563/meld, pinned `5c1353e` = v1.9.8), and the
  public enrichment repo `Farsinuce/NordGrund` (this workspace, docs included). The `louis-e`
  remote is on the Arnis clone.
- B. Closed in place 1 Sep 2026 [PROPOSED]: Claude drives Meld through `project.json` and its
  local JSON API (REFERENCE §10.5); the user's step is the walk. Say so if you want it otherwise.
- C. In-game coordinates: origin-relative for the pilot [PROPOSED (a)]; a real projection is
  decided only after walking (PRIMER §6). [PROPOSED: pick the pilot origin freely; Denmark's
  production origin is set once, in a fresh Meld project, together with the projection call.]
- D. Carried from the old project, recorded 10–12 Aug 2026 as user decisions but never reviewed.
  Each is the [PROPOSED] default until you say otherwise:
  - target Minecraft 26.3 and generate once, then freeze (PRIMER §1 says *"so far"*);
  - survival, every placed block is loot (12 Aug, no user tag; PRIMER §1);
  - a separate resource dimension with a weekly reset OR we use Meld's underground caves feature;
  - game modes never mix in one world;
  - warps for the 286 towns over 2,500 inhabitants in three claim tiers;
  - mining anywhere outside a protected claim (the 10 Aug "No block-breaking below the surface"
    was reversed to this on 21 Aug 2026 in the old register, row 24);
  - no caves (or should we do Meld caves?)
- E. Pre-pivot design calls not covered by items 4 and 5, each with the old recorded value as the
  [PROPOSED] default: real street surfaces from Befæstelseskort classes rather than uniform
  asphalt; a lantern beside every entrance door outside (you wrote an inside torch, item 4) [USER SAYS] Since lanterns can not be placed on walls, I prefer the solution with the torch on the inside.; sea at
  DVR90 0; biomes from Danish sources, not OSM; shop-sign gating (ground-floor unit only, refuse
  `v/ <person>` names, the board replaces the address sign). Re-confirm each before building it.
- F. PRIMER §3's day-one list was corrected 1 Sep 2026 against Meld `5c1353e` [PROPOSED]; re-review
  it.
- G. DAWA closes 1 Oct 2026 10:00 (CONSULT §11 item 1). [PROPOSED: archive the 829 MB
  adgangsadresse CSV in the first session; under the 10 GB rule it needs no call.]
- H. `manifest.json`: REFERENCE §17 says copy it, §18 says copy only the three gitignored files.
  Consult it in place until told otherwise [PROPOSED].
- I. [PROPOSED 2 Sep 2026] Height profile, used by the pilot: vanilla −64..319, `ground_level` 62,
  elevation lock pinned by hand at 0–180 m, so in-game Y = 62 + metres (sea at Y 62, Møllehøj at
  Y 233) and 126 blocks stay below sea level for survival mining. Meld's default (−56, survey lock)
  leaves 8. Trade-off: with the lock's floor at 0 m every sea-floor sample below 0 m clamps to Y 62,
  so bays have only the fork's carved depth. Ratify or change before the first production cell
  (first merge wins, REFERENCE §10.5).
- J. [PROPOSED 2 Sep 2026] Settings base for the pilot: Meld's shipped `presets/default.json` (the
  maintainer's tuned 1:1 look: interiors on, all schematic props off, tree sizes big 70 / tall 50)
  with PRIMER §3 on top. Raw Meld project defaults differ (interiors off, every prop on). Say if
  you want the raw defaults or props for the next run. The full table is `tools/meld_pilot.py`.
- K. [PROPOSED 2 Sep 2026] The determinism gate is block-level identity (`tools/world_diff.py`),
  not region-file hashes: the fork writes chunk palettes in varying order, so identical worlds hash
  differently (research/pilot-run-2026-09-02.md). PRIMER §3 ("diff region-file hashes") and §4
  ("hash identically") are yours to amend by hand.
