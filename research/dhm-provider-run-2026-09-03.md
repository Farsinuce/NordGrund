# Work item 3 on a world: the DHM provider and the repair gate, 3 Sep 2026

World #4, project `aarhus-dhm`, the same four Aarhus cells, same origin, same seed, same OSM
tiles, same `--nordgrund all` features as world #3. The only differences are the elevation source
and the repair stages. Built by Opus 5; not yet walked.

## The run 🟢

```
tools\meld_pilot.py --name aarhus-dhm --nordgrund all --dhm data\raster --elevation-trust v1
```

which sets Meld's `dhm_dir`, `elevation_trust` and `regional_elevation_only` together, giving the
per-cell command line `--dhm-dir … --elevation-trust v1 --regional-elevation-only`. Every cell
logged `Selected elevation provider: dhm_dk`, all four merged, `cell_health` empty, no failures.
The 26.2 server boots it with 0 corruption signals.

⚠️ Cosmetic: the selector prints `dhm_dk (0m resolution)` because its shared format string is
`{:.0}m` and our native resolution is 0.4. Harmless, but it reads wrong in a log.

**Coverage.** The four seam-expanded cells need 25 squares. Denmark publishes 24: `6221_576` is
open water in Aarhus Bay and `GetRasterFile` 404s for it. It is declared in
`data/raster/dhm_sea.txt` (tracked master copy: `tools/dhm_sea_dk.txt`) and read as 0.000 m. With
the square neither present nor declared, cell `0,-1,4` fails closed rather than rendering the bay
as something plausible — which is the behaviour the item was asked for.

## What changed on the ground 🟢

Ground column heights, world #3 (Mapterhorn + the full repair pipeline) versus world #4
(DHM 0.4 m + `--elevation-trust v1`), over three regions, n = 786,432 columns:

| | value |
|---|---|
| identical | 62.6 % |
| differ by ≥ 2 blocks | 8.8 % |
| differ by ≥ 5 blocks | 0.6 % (4,686 columns) |
| median / mean difference | 0 / +0.08 blocks |
| extremes | −23 … +23 blocks |
| chunks with ≥ 2 blocks of relief | 51,025 → **52,146** |

Of the columns that move by 5 blocks or more, the DHM world is **lower on 3,017 and higher on
1,669**, and they cluster: (192, −512), (192, −128), (320, −128), (704, −192), (320, −64). Those
are the Aarhus Å valley through the centre and the railway cutting south of the station — exactly
the shapes the 30 m built-up Gaussian and the 25 m coastal pull-down exist to flatten. So the gate
is doing what it was written to do, and the visible payoff of item 3 is the gate, not the extra
resolution (the provider itself agrees with Mapterhorn to a median of 0.00 m,
`elevation-mapterhorn-vs-dhm-2026-09-03.md`).

Landmark surface Y, world #3 → world #4: origin 94 → 92, tile centre 95 → 95, Aarhus H 86 → 87,
Domkirken 80 → 80, ARoS 111 → 113, Dokk1 harbour front 90 → 91.

## The §16 features are unaffected 🟢

`tools/probe_features.py` on world #4: 958,550 door blocks, 16,313 wall torches, 15,737 address
signs, 1,287 hanging signs, 45,174 lanterns, 12,198 copper grates, 12,412 water cauldrons, 473
glowstone. 11,635 sign and 1,073 hanging-sign block entities, none malformed. Bytes per chunk
4,365 (world #3: 4,357).

## Determinism across the new sampling path 🟢

Cell `0,0,4` regenerated (40 s) and compared block by block against its first render:
**16,384 of 16,384 chunks identical** (1,365 differ in palette order only, as always). So sampling
by absolute block coordinate through the local GeoTIFFs is reproducible, which is the property the
whole anchored-fetch design exists for.

## What this does NOT yet show 🔴

- **Harbour depth.** The manual lock still starts at 0 m, so every sea-floor sample below zero
  clamps to sea level: the DHM's real −14.8 m basins are still invisible. That is the lock, not the
  provider (decisions.md O proposes lock −20…175 m with `ground_level` 42).
- **A walk.** Every number here is read from the region files. Whether the kept relief reads as
  better or merely noisier is the user's judgement, at `data\server-dhm`, port 25569.
