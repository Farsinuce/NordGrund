#!/usr/bin/env python3
"""The Aarhus pilot recipe against a running headless Meld (5c1353e) + fork v3.1.8 (78215bd).
Reproduces the 2 Sep 2026 run: PRIMER §3 configuration, origin at the centre of tile 6223_574 so a
north-south and an east-west cell border cross the tile, four 2048-block cells, then queue + wait.

    python tools/meld_pilot.py [--name aarhus-pilot] [--dry-run]

Order matters: scale BEFORE origin (the origin snaps to the region grid using the project scale);
seed rides on /api/settings but is stored on the elevation block; the manual lock replaces the
survey so Y = ground_level + metres exactly. Idempotent: re-running on an existing project only
re-applies settings and queues the not-yet-merged cells.
"""
from __future__ import annotations
import argparse, os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from meld_api import Meld, dump

PILOT = {"west": 10.191045, "south": 56.146132, "east": 10.207418, "north": 56.155271}   # 6223_574 in WGS84
CENTRE = (56.150701, 10.199230)                                                           # E 574500 / N 6223500
SEED = 6223574
SETTINGS = {
    # PRIMER §3 (corrected 1 Sep 2026)
    "scale": 1.0, "buildings": True, "overture": False, "snow_mode": "off", "bake_lighting": False,
    "caves": False, "mc_version": "26.2", "tile_invariant_rendering": True, "seed": SEED,
    "terrain": True, "elevation_mode": "global", "vertical_exaggeration": 1.0, "osm_cache_ttl_days": 0,
    # height profile, decisions.md I [PROPOSED]: vanilla -64..319, Y = 62 + metres
    "ground_level": 62, "disable_height_limit": False, "world_min_y": "", "world_max_y": "",
    "height_headroom": 32, "height_underroom": 16,
    # Meld's shipped "Default" preset where it differs from the project defaults, decisions.md J [PROPOSED]
    "interior": True, "roof": True, "land_cover": True, "fill_ground": True, "trees": True, "tree_realm": "auto",
    "tree_size_weights": {"small": 100, "medium": 100, "big": 70, "tall": 50, "giant": 0},
    "props": {k: False for k in ("boat", "car", "crane", "excavator", "fountain", "helicopter", "lighthouse",
                                 "playground", "starship", "tombstone", "tractor", "windturbine")},
    "generate_3d_models": False, "road_detail_level": "auto", "signage": "none", "map_item": False,
    # opt-in output changers stay off (REFERENCE §10.4 item 6)
    "road_grade": False, "river_bed_v1": False, "canonical_regions": False,
    # cells and workers for a 16-thread / 32 GB machine (/api/recommend)
    "job_size_regions": 4, "seam_buffer_chunks": 8, "prefetch_margin_m": 256,
    "max_workers": 4, "min_threads_per_worker": 4, "governor_mode": "off", "worker_autoscale": False,
    "prefetch_enabled": True, "prefetch_terrain": True, "offline_elevation": False,
    "gamemode": "creative", "world_time": 6000, "prune_cell_after_merge": True,
    "export_format": "none", "native_region_format": "mca",
}
LOCK = {"min_m": 0, "max_m": 180, "seed": SEED}    # Denmark-wide: Møllehøj 171 m -> Y 233

def main() -> int:
    ap = argparse.ArgumentParser(); ap.add_argument("--name", default="aarhus-pilot"); ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(); m = Meld()
    projects = m.get("/api/projects")
    slugs = {p["slug"]: p for p in projects["projects"]}
    if a.name in slugs:
        if projects["active"] != a.name: print(m.post("/api/projects/switch", {"slug": a.name}))
    else:
        print("new project:", m.post("/api/projects/new", {"name": a.name}))
    print("scale first:", m.post("/api/settings", {"scale": SETTINGS["scale"]}).get("scale"))
    st = m.get("/api/state")
    if st["origin"].get("lat") is None:
        print("origin:", dump(m.post("/api/origin", {"lat": CENTRE[0], "lon": CENTRE[1]})))
    else:
        print("origin already locked:", st["origin"])
    r = m.post("/api/settings", SETTINGS); back = m.get("/api/settings")
    bad = {k: (v, back.get(k)) for k, v in SETTINGS.items() if k != "seed" and back.get(k) != v}
    if bad or r.get("seed") != SEED:
        print("SETTINGS MISMATCH", bad, "seed", r.get("seed")); return 1
    print("lock:", dump(m.post("/api/elevation/manual", LOCK)))
    g = m.post("/api/grid", {"bbox": PILOT, "mode": "replace"}); print("cells:", g["count"], [c["cell_key"] for c in g["cells"]])
    st = m.get("/api/state"); print("state:", st["origin"], st["elevation"], st["grid"])
    if a.dry_run: return 0
    print("queue:", dump(m.post("/api/queue", {})))
    t0 = time.time(); idle = 0
    while True:
        time.sleep(15); s = m.get("/api/status"); run = s["run"]; busy = [w for w in s["workers"] if w.get("running")]
        fin = (not run.get("active")) and (not s["prefetch"].get("active")) and not busy
        idle = idle + 1 if fin else 0
        print(f"[{(time.time()-t0)/60:5.1f} min] phase={run.get('phase')} done={run.get('done')}/{run.get('total')} failed={run.get('failed')} "
              f"prefetch={s['prefetch'].get('phase')} busy={[(w['cell_key'], w.get('progress')) for w in busy]} grid={s['grid']}", flush=True)
        if idle >= 2: break
        if time.time() - t0 > 4 * 3600: print("TIMEOUT"); return 2
    print("cell_health:", s.get("cell_health"), "cell_fail:", s.get("cell_fail"))
    ok = all(v == "merged" for v in s["grid"].values())
    print("master world:", m.get("/api/state")["master_world"]); print("RESULT:", "PASS" if ok else "FAIL")
    return 0 if ok else 1

if __name__ == "__main__":
    sys.exit(main())
