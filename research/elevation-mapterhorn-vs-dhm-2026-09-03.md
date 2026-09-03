# Mapterhorn z16 vs DHM Terræn 0.4 m, pilot area, 3 Sep 2026

The "measure first" step of PRIMER §5 work item 3 (REFERENCE §15). Artefacts: the 25 DHM Terræn
1 km tiles under `data\raster\` (rows 6221–6225, columns 572–576, pinned in `manifest.json`, all
fetched 3 Sep 2026 via `GetRasterFile`) and the 240 Mapterhorn z16 terrarium tiles the pilot run
cached under `data\meld-cache\arnis-tile-cache\mapterhorn\`. Method: 1,500 random DHM cells per
tile (n = 35,762 with a cached Mapterhorn tile), DHM cell value vs bilinear Mapterhorn at the
cell centre (EPSG:25832 → WGS84 → Web Mercator z16, 512 px tiles ≈ 0.66 m/px here).

| set | n | median | p05 | p95 | within 0.5 m | within 1 m | over 2 m | max |
|---|---|---|---|---|---|---|---|---|
| all | 35,762 | +0.00 | −0.19 | +0.10 | 96.5 % | 98.1 % | 1.0 % | 13.9 m |
| land | 29,785 | +0.00 | −0.24 | +0.12 | 95.8 % | 97.7 % | 1.1 % | 13.9 m |
| sea (DHM = 0.0) | 5,977 | +0.00 | +0.00 | +0.00 | 99.8 % | 99.9 % | 0.0 % | 3.5 m |

- 🟢 Mapterhorn's Danish tiles are the DHM: the same hydro-flattening, the same sea burn to 0.0.
  The cells over 2 m apart have a median DHM height of 6.5 m and only 6.8 % are near water:
  building edges, i.e. resampling plus vintage (Mapterhorn's ingest vs today's lot), not datum.
- 🟢 DHM Terræn files: EPSG:25832, 2500 × 2500 float32, 0.4 m, deflate, untiled strips, nodata
  −9999, transform origin at the tile's NW corner (E 574000, N 6224000 for 6223_574). Sea is
  exactly 0.0 (67 % of 6221_575). Harbour basins are BELOW zero: min −14.81 m in 6223_575,
  −10.64 in 6222_575 — real dredged depth in the terrain model, which the pilot's manual lock at
  0 m clamps to sea level (decisions.md I).
- 🟡 Verdict: the provider (work item 3) buys a pinned vintage, no tile server, and native 0.4 m
  sampling, not a visible fidelity jump on this terrain. Its worth is the pattern for the other
  Nordic rasters and the frozen-build discipline. Quays and building edges are where any
  difference will show; walk the harbour front on the A/B.
