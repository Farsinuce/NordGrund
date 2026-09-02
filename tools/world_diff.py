#!/usr/bin/env python3
"""Block-level diff of two region folders: block states, biomes, block entities and heightmaps
per chunk (light data ignored, it is server-computed). Palette ORDER is ignored: sections whose
raw palette/data differ are decoded block by block, so only a real block change counts.
    python tools/world_diff.py <regionA> <regionB> [r.x.z.mca ...]"""
from __future__ import annotations
import math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from world_check import iter_chunks

def _decode(pal, data, n=4096, min_bits=4):
    """Resolve packed palette indices to entries (1.16+ packing: no entry spans two longs)."""
    if len(pal) == 1: return (pal[0],) * n
    bits = max(min_bits, math.ceil(math.log2(len(pal)))); per = 64 // bits; mask = (1 << bits) - 1; out = []
    for L in data:
        L = int(L) & 0xFFFFFFFFFFFFFFFF
        for k in range(per):
            if len(out) >= n: break
            out.append(pal[(L >> (k * bits)) & mask])
    return tuple(out)

def sig(root):
    secs = {}
    for s in root.get("sections", []):
        y = int(s.get("Y", 0)); bs = s.get("block_states"); bio = s.get("biomes")
        pal = [(str(e.get("Name", e.get("id", ""))), tuple(sorted((k, str(v)) for k, v in (e.get("Properties", e.get("properties", {})) or {}).items()))) for e in (bs.get("palette", []) if bs is not None else [])]
        data = tuple(int(v) for v in (bs.get("data", []) if bs is not None else []))
        bpal = tuple(str(b) for b in (bio.get("palette", []) if bio is not None else [])); bdata = tuple(int(v) for v in (bio.get("data", []) if bio is not None else []))
        secs[y] = (tuple(pal), data, bpal, bdata)
    bes = sorted((int(b.get("x", 0)), int(b.get("y", 0)), int(b.get("z", 0)), str(b.get("id", ""))) for b in root.get("block_entities", []))
    hm = {k: tuple(int(v) for v in root["Heightmaps"][k]) for k in ("MOTION_BLOCKING", "WORLD_SURFACE") if k in root.get("Heightmaps", {})}
    return secs, bes, hm

def main():
    a, b = sys.argv[1], sys.argv[2]
    names = sys.argv[3:] or sorted(set(os.listdir(a)) & set(os.listdir(b)))
    tot = same = diff = 0; missing = 0; examples = []; palette_only = 0
    for n in names:
        A = {(cx, cz): sig(r) for cx, cz, r, _ in iter_chunks(os.path.join(a, n))}
        B = {(cx, cz): sig(r) for cx, cz, r, _ in iter_chunks(os.path.join(b, n))}
        for k in sorted(set(A) | set(B)):
            tot += 1
            if k not in A or k not in B: missing += 1; examples.append((n, k, "missing on one side")); continue
            if A[k] == B[k]: same += 1
            else:
                diff += 1
                sa, ba, ha = A[k]; sb, bb, hb = B[k]
                why = []; nblk = 0
                for y in sorted(set(sa) | set(sb)):
                    if sa.get(y) != sb.get(y):
                        pa, da, bpa, bda = sa.get(y, ((), (), (), ())); pb, db, bpb, bdb = sb.get(y, ((), (), (), ()))
                        blk = sum(1 for u, v in zip(_decode(pa, da), _decode(pb, db)) if u != v) if pa and pb else 4096
                        bio_d = sum(1 for u, v in zip(_decode(bpa, bda, 64, 1), _decode(bpb, bdb, 64, 1)) if u != v) if bpa and bpb else (0 if bpa == bpb else 64)
                        nblk += blk + bio_d
                        if blk or bio_d: why.append(f"sec{y}:{blk} blocks,{bio_d} biome cells")
                if ba != bb: why.append("block_entities"); nblk += 1
                if ha != hb: why.append("heightmaps"); nblk += 1
                if nblk == 0:
                    same += 1; diff -= 1; palette_only += 1; continue
                if len(examples) < 12: examples.append((n, k, " ".join(why)[:160]))
    print(f"regions compared: {len(names)}  chunks: {tot}  identical: {same} (of which palette-order-only: {palette_only})  really different: {diff}  missing: {missing}")
    for e in examples: print("  ", e)
    return 0 if diff == 0 and missing == 0 else 1

if __name__ == "__main__":
    sys.exit(main())
