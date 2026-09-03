#!/usr/bin/env python3
"""Count the NordGrund feature blocks in a generated world, read sign texts back from the chunk
NBT, and measure the door hit rate at DAR access points.

    python tools/probe_features.py <world_dir> [--dar data/derived/dar_0751.csv] [--sample 200]

Reads region files directly (never writes). Exit 1 when a feature that should be present is absent.
"""
from __future__ import annotations
import argparse, collections, csv, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "meld"))
from world_check import iter_chunks
from world_diff import _decode

FEATURE_BLOCKS = ("minecraft:dark_oak_door", "minecraft:wall_torch", "minecraft:pale_oak_wall_sign", "minecraft:pale_oak_wall_hanging_sign",
                  "minecraft:lantern", "minecraft:waxed_weathered_copper_grate", "minecraft:water_cauldron", "minecraft:glowstone")


def region_dir(world: str) -> str:
    for d in (os.path.join(world, "region"), os.path.join(world, "dimensions", "minecraft", "overworld", "region")):
        if os.path.isdir(d):
            return d
    sys.exit(f"no region dir under {world}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("world")
    ap.add_argument("--dar", default=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "derived", "dar_0751.csv"))
    ap.add_argument("--sample", type=int, default=200)
    ap.add_argument("--origin", nargs=2, type=float, default=(56.14890406036652, 10.197180313164804))
    a = ap.parse_args()
    rd = region_dir(a.world)
    files = sorted(f for f in os.listdir(rd) if f.endswith(".mca"))
    chunks_with = collections.Counter()
    blocks = collections.Counter()
    sign_texts = []
    hanging_texts = []
    be_kinds = collections.Counter()
    columns = {}          # (x, z) -> {y: block} only for door probing, filled lazily per region
    for fn in files:
        for cx, cz, root, _ in iter_chunks(os.path.join(rd, fn)):
            seen = set()
            for s in root.get("sections", []):
                bs = s.get("block_states")
                if bs is None:
                    continue
                pal = [str(e.get("Name", "")) for e in bs["palette"]]
                interesting = [p for p in pal if p in FEATURE_BLOCKS]
                if not interesting:
                    continue
                dec = _decode(tuple(pal), tuple(int(v) for v in bs.get("data", [])))
                cnt = collections.Counter(dec)
                for p in interesting:
                    blocks[p] += cnt.get(p, 0)
                    seen.add(p)
            for p in seen:
                chunks_with[p] += 1
            for be in root.get("block_entities", []):
                bid = str(be.get("id", ""))
                be_kinds[bid] += 1
                if bid in ("minecraft:sign", "minecraft:hanging_sign"):
                    ft = be.get("front_text", {})
                    msgs = [str(m) for m in ft.get("messages", [])]
                    (hanging_texts if bid == "minecraft:hanging_sign" else sign_texts).append((int(be["x"]), int(be["y"]), int(be["z"]), msgs))
    total_chunks = sum(1 for fn in files for _ in iter_chunks(os.path.join(rd, fn)))
    print(f"world {a.world}: {len(files)} regions, {total_chunks} chunks")
    print("feature blocks (count / chunks containing):")
    for p in FEATURE_BLOCKS:
        print(f"  {p:42s} {blocks[p]:8d} / {chunks_with[p]:6d}")
    print("block entities:", dict(be_kinds.most_common(8)))
    print(f"wall signs with text: {len(sign_texts)}; hanging signs: {len(hanging_texts)}")
    for x, y, z, m in sign_texts[:6]:
        print(f"  sign @({x},{y},{z}): {m}")
    for x, y, z, m in hanging_texts[:6]:
        print(f"  hanging @({x},{y},{z}): {m}")
    bad = [t for t in sign_texts + hanging_texts if len(t[3]) != 4 or any(s.startswith('"') for s in t[3])]
    print(f"signs with a non-4-line or JSON-quoted text: {len(bad)}")

    # door hit rate at DAR access points (central tile), like the world #2 probe
    hits = 0
    probed = 0
    if os.path.exists(a.dar):
        from src.coords import block_x, block_z
        from pyproj import Transformer
        T = Transformer.from_crs("EPSG:25832", "EPSG:4326", always_xy=True)
        olat, olon = a.origin
        rows = [r for r in csv.DictReader(open(a.dar, encoding="utf-8")) if 573800 <= float(r["E"]) <= 575000 and 6222800 <= float(r["N"]) <= 6224000 and r["building_id"]]
        rows.sort(key=lambda r: r["husnummer_id"])
        sample = rows[::max(1, len(rows) // a.sample)][:a.sample]
        cache = {}

        def column(x, z):
            rx, rz = x // 512, z // 512
            if (rx, rz) not in cache:
                p = os.path.join(rd, f"r.{rx}.{rz}.mca")
                cache[(rx, rz)] = {(cx, cz): root for cx, cz, root, _ in iter_chunks(p)} if os.path.exists(p) else {}
            root = cache[(rx, rz)].get((x // 16, z // 16))
            if root is None:
                return {}
            out = {}
            for s in root["sections"]:
                bs = s.get("block_states")
                if bs is None:
                    continue
                pal = [str(e.get("Name")) for e in bs["palette"]]
                dec = _decode(tuple(pal), tuple(int(v) for v in bs.get("data", [])))
                y0 = int(s["Y"]) * 16
                for dy in range(16):
                    out[y0 + dy] = dec[dy * 256 + (z % 16) * 16 + (x % 16)]
            return out
        for r in sample:
            lon, lat = T.transform(float(r["E"]), float(r["N"]))
            x, z = block_x(lon, olat, olon, 1.0), block_z(lat, olat, 1.0)
            probed += 1
            found = False
            for dx in (-1, 0, 1):
                for dz in (-1, 0, 1):
                    if any("door" in b for b in column(x + dx, z + dz).values()):
                        found = True
                        break
                if found:
                    break
            hits += found
        print(f"DAR access points probed: {probed}; a door within 1 block: {hits} ({100 * hits / probed:.0f}%)" if probed else "no DAR probe")
    ok = blocks["minecraft:dark_oak_door"] > 0 and blocks["minecraft:pale_oak_wall_sign"] > 0 and blocks["minecraft:wall_torch"] > 0 and blocks["minecraft:lantern"] > 0 and blocks["minecraft:waxed_weathered_copper_grate"] > 0 and not bad
    print("RESULT:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
