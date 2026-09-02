#!/usr/bin/env python3
"""Read-back checks for a generated Java world (CLAUDE.md, Day-one checklist).

    python tools/world_check.py <world_dir> [--expect-dataversion 4903] [--sample N]

Reads level.dat and every region file directly (Anvil container + NBT via nbtlib) and reports:
DataVersion, chunk count, bytes per chunk, ground flatness (heightmap spread), biome palettes,
building-ish blocks (doors, glass) and the most common non-natural blocks. Never writes.
Exit 1 when a hard check fails (DataVersion mismatch, flat ground, no biomes >1, no buildings).
"""
from __future__ import annotations
import argparse, collections, gzip, io, os, struct, sys, zlib
import nbtlib

NATURAL = {"minecraft:air", "minecraft:stone", "minecraft:dirt", "minecraft:grass_block", "minecraft:water",
           "minecraft:bedrock", "minecraft:sand", "minecraft:gravel", "minecraft:deepslate", "minecraft:cave_air",
           "minecraft:short_grass", "minecraft:grass", "minecraft:tall_grass", "minecraft:oak_leaves",
           "minecraft:oak_log", "minecraft:spruce_leaves", "minecraft:spruce_log", "minecraft:birch_leaves",
           "minecraft:birch_log", "minecraft:podzol", "minecraft:coarse_dirt", "minecraft:clay", "minecraft:snow",
           "minecraft:fern", "minecraft:dandelion", "minecraft:poppy", "minecraft:moss_block", "minecraft:mud",
           "minecraft:sandstone", "minecraft:stone_bricks"}  # stone_bricks excluded from 'building' because Arnis roads use them? keep as natural-ish
BUILDING_HINTS = ("door", "glass")

def parse_nbt(raw: bytes):
    return nbtlib.File.parse(io.BytesIO(raw))

def _root(f):
    """nbtlib 2.x File IS the root compound (level.dat keys: Data; chunk keys: DataVersion...);
    nbtlib 1.x wrapped it under the root name. Handle both."""
    if "Data" in f or "DataVersion" in f:
        return f
    if len(f) == 1:
        return next(iter(f.values()))
    return f

def read_level_dat(world: str) -> dict:
    p = os.path.join(world, "level.dat")
    f = nbtlib.load(p)                      # gzip auto-detected
    data = _root(f)["Data"]
    out = {"DataVersion": int(data.get("DataVersion", -1)), "LevelName": str(data.get("LevelName", "")),
           "GameType": int(data.get("GameType", -1))}
    ver = data.get("Version")
    if ver is not None:
        out["Version.Name"] = str(ver.get("Name", "")); out["Version.Id"] = int(ver.get("Id", -1))
    return out

def iter_chunks(mca_path: str):
    """Yield (cx, cz, nbt_root, stored_bytes) for every chunk in a region file."""
    with open(mca_path, "rb") as fh:
        blob = fh.read()
    if len(blob) < 8192:
        return
    for i in range(1024):
        off_sec = int.from_bytes(blob[i*4:i*4+3], "big"); n_sec = blob[i*4+3]
        if off_sec == 0 or n_sec == 0:
            continue
        start = off_sec * 4096
        length, comp = struct.unpack(">IB", blob[start:start+5])
        payload = blob[start+5:start+4+length]
        if comp == 2: raw = zlib.decompress(payload)
        elif comp == 1: raw = gzip.decompress(payload)
        elif comp == 3: raw = payload
        else: raise ValueError(f"{mca_path}: chunk {i} uses compression {comp} (unsupported here)")
        root = _root(parse_nbt(raw))
        yield int(root.get("xPos", i % 32)), int(root.get("zPos", i // 32)), root, n_sec * 4096

def unpack_heightmap(longs, n=256, bits=9):
    vals = []; per_long = 64 // bits; mask = (1 << bits) - 1
    for L in longs:
        L = int(L) & 0xFFFFFFFFFFFFFFFF
        for k in range(per_long):
            if len(vals) >= n: break
            vals.append((L >> (k * bits)) & mask)
    return vals

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("world"); ap.add_argument("--expect-dataversion", type=int, default=4903)
    ap.add_argument("--sample", type=int, default=0, help="only read the first N region files (0 = all)")
    a = ap.parse_args()
    fails = []
    lv = read_level_dat(a.world)
    print(f"level.dat: {lv}")
    if lv["DataVersion"] != a.expect_dataversion:
        fails.append(f"DataVersion {lv['DataVersion']} != expected {a.expect_dataversion}")
    region_dir = os.path.join(a.world, "region")
    if not os.path.isdir(region_dir):            # e.g. a world whose overworld regions sit elsewhere
        for d, _, fs in os.walk(a.world):
            if any(f.endswith(".mca") for f in fs) and "entities" not in d and "poi" not in d:
                region_dir = d; break
    print(f"region dir: {region_dir}")
    files = sorted(f for f in os.listdir(region_dir) if f.endswith(".mca"))
    if a.sample: files = files[:a.sample]
    chunks = 0; stored = 0; hm_min = 10**9; hm_max = -10**9; hm_spread_chunks = 0; full = 0
    biome_multi = 0; biome_names = collections.Counter(); building_chunks = 0
    block_chunks = collections.Counter(); dv = collections.Counter(); status = collections.Counter()
    for fn in files:
        for cx, cz, root, nbytes in iter_chunks(os.path.join(region_dir, fn)):
            chunks += 1; stored += nbytes
            dv[int(root.get("DataVersion", -1))] += 1; status[str(root.get("Status", "?"))] += 1
            if str(root.get("Status", "")).endswith("full"): full += 1
            hm = root.get("Heightmaps", {})
            arr = hm.get("MOTION_BLOCKING") or hm.get("WORLD_SURFACE")
            if arr is not None and len(arr) > 0:
                v = unpack_heightmap(arr); lo, hi = min(v), max(v)
                hm_min = min(hm_min, lo); hm_max = max(hm_max, hi)
                if hi - lo >= 2: hm_spread_chunks += 1
            names = set(); bset = set()
            for sec in root.get("sections", []):
                bs = sec.get("block_states"); bio = sec.get("biomes")
                if bs is not None:
                    for e in bs.get("palette", []):
                        names.add(str(e.get("Name", e.get("id", "?"))))
                if bio is not None:
                    pal = [str(x) for x in bio.get("palette", [])]
                    bset.update(pal)
            if len(bset) > 1: biome_multi += 1
            for b in bset: biome_names[b] += 1
            if any(h in n for n in names for h in BUILDING_HINTS): building_chunks += 1
            for n in names:
                if n not in NATURAL: block_chunks[n] += 1
    print(f"region files: {len(files)}   chunks: {chunks}   stored bytes/chunk: {stored/chunks if chunks else 0:.0f}")
    print(f"chunk DataVersions: {dict(dv)}   statuses: {dict(status)}")
    print(f"heightmap (world Y = value-64): min {hm_min-64} max {hm_max-64}; chunks with >=2 blocks of relief: {hm_spread_chunks}/{full} full chunks")
    print(f"chunks with >1 biome in a palette: {biome_multi}/{chunks}; biomes seen (chunks): {dict(biome_names.most_common(12))}")
    print(f"chunks with door/glass blocks (buildings): {building_chunks}/{chunks}")
    print("most common non-natural blocks (chunks containing):")
    for n, c in block_chunks.most_common(25): print(f"  {c:6d}  {n}")
    if chunks == 0: fails.append("no chunks")
    if full and hm_spread_chunks < full * 0.2: fails.append(f"ground looks flat: only {hm_spread_chunks}/{full} full chunks have relief")
    if biome_multi == 0: fails.append("no chunk has a biome palette with more than one entry")
    if building_chunks == 0: fails.append("no chunk contains door/glass blocks")
    if lv["DataVersion"] != a.expect_dataversion or (dv and set(dv) != {a.expect_dataversion}):
        fails.append(f"chunk DataVersions {dict(dv)} not all {a.expect_dataversion}")
    print("RESULT:", "PASS" if not fails else "FAIL: " + "; ".join(fails))
    return 0 if not fails else 1

if __name__ == "__main__":
    sys.exit(main())
