#!/usr/bin/env python3
"""Enrichment emitter v1 (PRIMER §5 work item 4): GeoDanmark building footprints + BBR attributes
-> OSM-shaped elements written into Meld's z11 OSM tile cache, replacing OSM buildings inside the
coverage box. Deterministic: every id derives from GeoDanmark id_lokalId; no randomness.

    python tools/emit_geodk.py --bbox E0 N0 E1 N1 [--write] [--height eave|none]
                               [--entrances data/derived/dar_0751.csv] [--manholes]

Coverage bbox is EPSG:25832 metres. Dry run prints statistics; --write rewrites the tiles under
MELD_CACHE_DIR/osm (originals saved once under osm-original/, .osmbin sidecars deleted).
Fail-closed: an unmapped BBR code aborts with the code list (REFERENCE §13).
"""
from __future__ import annotations
import argparse, collections, csv, glob, json, math, os, shutil, sys, zipfile
import numpy as np, rasterio
from pyproj import Transformer
from shapely import wkt as shp_wkt
from shapely.geometry import Point, Polygon, LineString
from shapely.ops import nearest_points

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.environ.get("MELD_CACHE_DIR", os.path.join(ROOT, "data", "meld-cache"))
T_LL = Transformer.from_crs("EPSG:25832", "EPSG:4326", always_xy=True)
T_UTM = Transformer.from_crs("EPSG:4326", "EPSG:25832", always_xy=True)
WAY_BASE, NODE_BASE, REL_BASE, NODE_STRIDE = 1 << 40, 1 << 41, 1 << 42, 2048
ENT_BASE, MH_BASE = 1 << 43, 1 << 44

# BBR byg021 (BygningensAnvendelse) -> OSM building=* value the fork's class table can read.
# Every code seen in kommune 0751 (3 Sep 2026) is listed; a new code aborts the run (fail-closed).
USE = {
 "110": "farm", "120": "detached", "121": "semidetached_house", "122": "detached", "130": "terrace", "131": "terrace",
 "132": "semidetached_house", "140": "apartments", "150": "dormitory", "160": "residential", "185": "house", "190": "residential",
 "210": "farm_auxiliary", "211": "barn", "212": "barn", "213": "barn", "214": "barn", "215": "barn", "216": "greenhouse", "217": "farm_auxiliary", "218": "farm_auxiliary", "219": "farm_auxiliary",
 "220": "industrial", "221": "industrial", "222": "industrial", "223": "warehouse", "229": "industrial",
 "230": "service", "231": "service", "232": "service", "233": "service", "234": "service", "239": "service",
 "240": "garage", "241": "parking", "242": "transportation", "243": "transportation", "244": "transportation", "249": "transportation",
 "310": "commercial", "311": "warehouse", "312": "retail", "313": "retail", "314": "office", "315": "retail", "316": "retail", "319": "commercial",
 "320": "hotel", "321": "hotel", "322": "hotel", "323": "retail", "324": "commercial", "325": "commercial", "329": "commercial",
 "330": "office", "331": "office", "332": "office", "333": "office", "334": "office", "339": "commercial", "390": "commercial",
 "410": "civic", "411": "civic", "412": "civic", "413": "civic", "414": "church", "415": "civic", "416": "civic", "419": "civic",
 "420": "civic", "421": "civic", "422": "civic", "429": "civic", "430": "school", "431": "school", "432": "school", "433": "university", "439": "school",
 "440": "hospital", "441": "hospital", "442": "hospital", "443": "hospital", "449": "hospital", "450": "kindergarten", "451": "kindergarten", "452": "kindergarten", "453": "kindergarten", "459": "kindergarten", "490": "civic",
 "510": "house", "520": "hotel", "521": "hotel", "522": "hotel", "523": "hotel", "529": "hotel", "530": "sports_hall", "531": "sports_hall", "532": "sports_hall", "533": "sports_hall", "534": "grandstand", "535": "sports_hall", "539": "sports_hall",
 "540": "allotment_house", "585": "hut", "590": "hut",
 "910": "garage", "920": "carport", "930": "shed", "940": "greenhouse", "950": "roof", "960": "conservatory", "970": "farm_auxiliary", "990": "ruins", "999": "yes",
 "None": "yes",   # BBR row without a use code: policy, counted under stats as keyed/yes
}
RESIDENTIAL = {"110", "120", "121", "122", "130", "131", "132", "140", "150", "160", "185", "190", "510", "540"}
WALL = {"1": "brick", "2": "concrete", "3": "eternit", "4": "timber_framing", "5": "wood", "6": "concrete", "8": "metal", "10": "eternit", "11": "plastic", "12": "glass", "80": None, "90": None}
ROOF = {"1": ("tar_paper", "black"), "2": ("tar_paper", "black"), "3": ("eternit", "grey"), "4": ("concrete", "grey"), "5": ("roof_tiles", "red"), "6": ("metal", "grey"), "7": ("thatch", None), "10": ("eternit", "grey"), "11": ("plastic", None), "12": ("glass", None), "20": ("grass", "green"), "80": (None, None), "90": (None, None)}


def load_geodk(zp: str):
    z = zipfile.ZipFile(zp)
    return json.loads(z.read(z.infolist()[0].filename))


def load_bbr(zp: str) -> dict:
    z = zipfile.ZipFile(zp)
    rows = json.loads(z.read(z.infolist()[0].filename))
    return {r["id_lokalId"].lower(): r for r in rows if str(r.get("status")) == "6" and r.get("id_lokalId")}


class Dhm:
    """Bilinear ground height from the local DHM Terræn 1 km tiles (nodata -> NaN)."""
    def __init__(self, d: str):
        self.d = d
        self.t = {}

    def tile(self, n: int, e: int):
        k = (n, e)
        if k not in self.t:
            p = os.path.join(self.d, f"DHM_TERRAEN_1km_{n}_{e}.tif")
            if not os.path.exists(p):
                self.t[k] = None
            else:
                with rasterio.open(p) as ds:
                    a = ds.read(1).astype(np.float64)
                    a[a == ds.nodata] = np.nan
                    self.t[k] = (a, ds.transform)
        return self.t[k]

    def at(self, x: float, y: float) -> float:
        t = self.tile(int(y // 1000), int(x // 1000))
        if t is None:
            return float("nan")
        a, T = t
        c, r = ~T * (x, y)
        c -= 0.5
        r -= 0.5
        c0, r0 = int(np.floor(c)), int(np.floor(r))
        fc, fr = c - c0, r - r0

        def g(i, j):
            return a[min(max(j, 0), a.shape[0] - 1), min(max(i, 0), a.shape[1] - 1)]
        return g(c0, r0) * (1 - fc) * (1 - fr) + g(c0 + 1, r0) * fc * (1 - fr) + g(c0, r0 + 1) * (1 - fc) * fr + g(c0 + 1, r0 + 1) * fc * fr


def z11(lon: float, lat: float):
    n = 2048
    x = int((lon + 180) / 360 * n)
    y = int((1 - math.log(math.tan(math.radians(lat)) + 1 / math.cos(math.radians(lat))) / math.pi) / 2 * n)
    return x, y


def tiles_for(minlon, minlat, maxlon, maxlat):
    x0, y0 = z11(minlon, maxlat)
    x1, y1 = z11(maxlon, minlat)
    return {(x, y) for x in range(x0, x1 + 1) for y in range(y0, y1 + 1)}


def load_pois(cache: str, E0, N0, E1, N1):
    """Named OSM points of interest inside the coverage box, from the original tiles (before any
    emitter run): (E, N, name, kind). Also the OSM building names keyed by centroid for name reuse."""
    pois, bnames = [], []
    src = os.path.join(cache, "osm-original") if os.path.isdir(os.path.join(cache, "osm-original")) else os.path.join(cache, "osm")
    for fn in sorted(glob.glob(os.path.join(src, "osm_g1_z11_*.json"))):
        j = json.load(open(fn, encoding="utf-8")); els = j["elements"]
        nd = {e["id"]: (e.get("lon"), e.get("lat")) for e in els if e["type"] == "node"}
        for e in els:
            tags = e.get("tags") or {}
            name = tags.get("name") or tags.get("brand")
            if not name:
                continue
            kind = next((k for k in ("shop", "amenity", "office", "craft", "tourism", "leisure", "healthcare") if k in tags), None)
            if e["type"] == "node" and kind and e.get("lon") is not None:
                x, y = T_UTM.transform(e["lon"], e["lat"])
                if E0 <= x <= E1 and N0 <= y <= N1:
                    pois.append((x, y, name, kind))
            elif e["type"] == "way" and ("building" in tags or kind):
                pts = [nd[n] for n in e.get("nodes", []) if n in nd and nd[n][0] is not None]
                if not pts:
                    continue
                lon = sum(q[0] for q in pts) / len(pts); lat = sum(q[1] for q in pts) / len(pts)
                x, y = T_UTM.transform(lon, lat)
                if E0 <= x <= E1 and N0 <= y <= N1:
                    (bnames if "building" in tags else pois).append((x, y, name, kind or "building"))
    return pois, bnames


def load_entrances(path: str) -> dict:
    """data/derived/dar_0751.csv (tools/dar_chain.py) -> {geodanmark building id: [rows]}"""
    out = collections.defaultdict(list)
    if not path or not os.path.exists(path):
        return out
    with open(path, encoding="utf-8", newline="") as fh:
        for r in csv.DictReader(fh):
            if r.get("building_id"):
                out[int(r["building_id"])].append(r)
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--bbox", nargs=4, type=float, required=True, metavar=("E0", "N0", "E1", "N1"))
    ap.add_argument("--geodk", default=(glob.glob(os.path.join(ROOT, "data/vector/GEODKV_V4_Bygning_0751_*.zip")) or [""])[0])
    ap.add_argument("--bbr", default=(glob.glob(os.path.join(ROOT, "data/vector/BBR_V*_Bygning_0751_*.zip")) or [""])[0])
    ap.add_argument("--manholes-file", default=(glob.glob(os.path.join(ROOT, "data/vector/GEODKV_V4_Broenddaeksel_0751_*.zip")) or [""])[0])
    ap.add_argument("--dhm", default=os.path.join(ROOT, "data/raster"))
    ap.add_argument("--height", choices=["eave", "none"], default="eave")
    ap.add_argument("--simplify", type=float, default=0.15)
    ap.add_argument("--entrances", default=os.path.join(ROOT, "data/derived/dar_0751.csv"))
    ap.add_argument("--manholes", action="store_true")
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args()
    E0, N0, E1, N1 = a.bbox
    dhm = Dhm(a.dhm)
    bbr = load_bbr(a.bbr)
    feats = load_geodk(a.geodk)
    ents = load_entrances(a.entrances)
    pois, bnames = load_pois(CACHE, E0, N0, E1, N1)
    grid = collections.defaultdict(list)
    for i, (x, y, name, kind) in enumerate(pois):
        grid[(int(x // 50), int(y // 50))].append(i)
    bgrid = collections.defaultdict(list)
    for i, (x, y, name, kind) in enumerate(bnames):
        bgrid[(int(x // 50), int(y // 50))].append(i)
    def near(g, items, x, y, r):
        cx, cy = int(x // 50), int(y // 50); out = []
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for i in g.get((cx + dx, cy + dy), []):
                    px, py = items[i][0], items[i][1]
                    d = math.hypot(px - x, py - y)
                    if d <= r: out.append((d, i))
        return sorted(out)
    st = collections.Counter()
    unmapped = collections.Counter()
    nodes, ways, rels = [], [], []
    per_tile = collections.defaultdict(set)
    eaves = []
    extra_nodes = []          # entrance + manhole nodes, assigned to tiles by their own position

    for f in feats:
        if f.get("status") != "Anlagt":
            st["skip:status"] += 1
            continue
        geom = shp_wkt.loads(f["geometri"])
        if geom.geom_type != "Polygon":
            st["skip:geom"] += 1
            continue
        cx, cy = geom.centroid.x, geom.centroid.y
        if not (E0 <= cx <= E1 and N0 <= cy <= N1):
            continue
        lid = int(f["id_lokalId"])
        r = bbr.get((f.get("BBRUUID") or "").lower())
        tags = {}
        residential = False
        if f["bygningstype"] == "Tank/Silo":
            tags["building"] = "silo"
            tags["man_made"] = "silo"
        elif f["bygningstype"] == "Drivhus":
            tags["building"] = "greenhouse"
        elif r is None:
            tags["building"] = "shed" if str(f.get("underMinimumBygning")) == "True" else "yes"
            st["unkeyed:" + tags["building"]] += 1
        else:
            code = str(r.get("byg021BygningensAnvendelse"))
            if code not in USE:
                unmapped[code] += 1
                continue
            tags["building"] = USE[code]
            st["keyed"] += 1
            lv = str(r.get("byg054AntalEtager"))
            if lv.isdigit() and int(lv) > 0:
                tags["building:levels"] = lv
            elif code[0] == "9":
                tags["building:levels"] = "1"
            w = WALL.get(str(r.get("byg032YdervæggensMateriale")))
            if w:
                tags["building:material"] = w
            rm, rc = ROOF.get(str(r.get("byg033Tagdækningsmateriale")), (None, None))
            if rm:
                tags["roof:material"] = rm
            if rc:
                tags["roof:colour"] = rc
            residential = code in RESIDENTIAL
        tags["nordgrund:id"] = str(lid)
        tags["nordgrund:residential"] = "yes" if residential else "no"
        # eave height: roof-edge ring Z minus the DHM ground at the same vertices (median)
        if a.height == "eave":
            zs = []
            for x, y, *zz in geom.exterior.coords:
                if zz and zz[0] != -999.0:
                    g = dhm.at(x, y)
                    if not np.isnan(g):
                        zs.append(zz[0] - g)
            if zs:
                eave = float(np.median(zs))
                if 2.0 <= eave <= 200.0:      # Aarhus Ø Lighthouse is 142 m; the 320 m telemast is no building
                    tags["height"] = f"{eave:.1f}"
                    eaves.append(eave)
                    st["height:eave"] += 1
                else:
                    st["height:out_of_range"] += 1
        poly2d = Polygon([(x, y) for x, y, *_ in geom.exterior.coords], [[(x, y) for x, y, *_ in h.coords] for h in geom.interiors])
        for d, i in near(bgrid, bnames, cx, cy, 60):
            if poly2d.contains(Point(bnames[i][0], bnames[i][1])):
                tags["name"] = bnames[i][2]; st["name:osm_building"] += 1; break
        inside_pois = [i for d, i in near(grid, pois, cx, cy, 120) if poly2d.contains(Point(pois[i][0], pois[i][1]))]
        g2 = poly2d
        if a.simplify:
            g2 = g2.simplify(a.simplify, preserve_topology=True)
        if g2.is_empty or g2.geom_type != "Polygon":
            st["skip:simplified"] += 1
            continue
        rings = [list(g2.exterior.coords)] + [list(h.coords) for h in g2.interiors]
        # entrances: DAR access points snapped onto the outer ring, inserted as outline nodes
        ent_pts = []
        for e in ents.get(lid, []):
            try:
                ex, ey = float(e["E"]), float(e["N"])
            except (TypeError, ValueError):
                continue
            ring = LineString(rings[0])
            d = ring.project(Point(ex, ey))
            snapped = ring.interpolate(d)
            if Point(ex, ey).distance(snapped) > 25.0:
                st["entrance:too_far"] += 1
                continue
            sign = None
            if not residential:
                cands = [(math.hypot(pois[i][0] - snapped.x, pois[i][1] - snapped.y), i) for i in inside_pois]
                cands += [(d2, i) for d2, i in near(grid, pois, snapped.x, snapped.y, 12.0)]
                if cands:
                    sign = pois[min(cands)[1]][2]; st["entrance:sign"] += 1
            ent_pts.append((d, snapped.x, snapped.y, dict(e, sign=sign)))
        ent_pts.sort(key=lambda t: t[0])
        way_ids = []
        vi = 0
        lons, lats = [], []
        for ri, ring in enumerate(rings):
            nid_list = []
            pts = ring[:-1]
            # merge snapped entrance points into the outer ring in order
            if ri == 0 and ent_pts:
                line = LineString(ring)
                merged = [(line.project(Point(p)), p, None) for p in pts] + [(d, (sx, sy), e) for d, sx, sy, e in ent_pts]
                merged.sort(key=lambda t: t[0])
                pts = [(p, e) for _, p, e in merged]
            else:
                pts = [(p, None) for p in pts]
            for (x, y), e in pts:
                lon, lat = T_LL.transform(x, y)
                if e is None:
                    nid = NODE_BASE + lid * NODE_STRIDE + vi
                    vi += 1
                    assert vi < NODE_STRIDE, f"{lid}: too many vertices"
                    nodes.append({"type": "node", "id": nid, "lat": round(lat, 7), "lon": round(lon, 7)})
                else:
                    nid = ENT_BASE + int(e["husnummer_seq"])
                    etags = {"entrance": "main", "addr:street": e["vejnavn"], "addr:housenumber": e["husnummertekst"],
                             "nordgrund:street": e["vejnavn"], "nordgrund:housenumber": e["husnummertekst"]}
                    if e.get("postnr"):
                        etags["addr:postcode"] = e["postnr"]
                    if e.get("sign"):
                        etags["nordgrund:sign"] = e["sign"]
                    nodes.append({"type": "node", "id": nid, "lat": round(lat, 7), "lon": round(lon, 7), "tags": etags})
                    st["entrance"] += 1
                nid_list.append(nid)
                lons.append(lon)
                lats.append(lat)
            nid_list.append(nid_list[0])
            wid = WAY_BASE + lid * 4 + ri
            way_ids.append(wid)
            ways.append({"type": "way", "id": wid, "nodes": nid_list, "tags": dict(tags) if (ri == 0 and len(rings) == 1) else {}})
        if len(rings) > 1:
            rels.append({"type": "relation", "id": REL_BASE + lid,
                         "members": [{"type": "way", "ref": w, "role": "outer" if i == 0 else "inner"} for i, w in enumerate(way_ids)],
                         "tags": {**tags, "type": "multipolygon"}})
            st["multipolygon"] += 1
        for t in tiles_for(min(lons), min(lats), max(lons), max(lats)):
            per_tile[t].add(lid)
        st["emitted"] += 1
    if unmapped:
        sys.exit(f"UNMAPPED BBR byg021 codes (add to USE): {dict(unmapped)}")

    # manhole covers (GeoDanmark Broenddaeksel points, Z on the cover) -> nodes man_made=manhole
    if a.manholes and a.manholes_file:
        for m in load_geodk(a.manholes_file):
            if m.get("status") != "Anlagt":
                continue
            p = shp_wkt.loads(m["geometri"])
            if not (E0 <= p.x <= E1 and N0 <= p.y <= N1):
                continue
            lon, lat = T_LL.transform(p.x, p.y)
            extra_nodes.append({"type": "node", "id": MH_BASE + int(m["id_lokalId"]), "lat": round(lat, 7), "lon": round(lon, 7),
                                "tags": {"man_made": "manhole", "nordgrund:id": m["id_lokalId"]}})
            st["manhole"] += 1

    print("stats:", dict(st))
    print("eave height m: n=%d median %.1f p10 %.1f p90 %.1f" % (len(eaves), np.median(eaves), np.percentile(eaves, 10), np.percentile(eaves, 90)) if eaves else "no eaves")
    print("tiles:", {f"z11_{x}_{y}": len(v) for (x, y), v in per_tile.items()}, "| nodes", len(nodes), "ways", len(ways), "relations", len(rels), "extra nodes", len(extra_nodes))

    def in_cov(lon, lat):
        x, y = T_UTM.transform(lon, lat)
        return E0 <= x <= E1 and N0 <= y <= N1

    by_lid = collections.defaultdict(list)
    for n in nodes:
        if n["id"] >= ENT_BASE:
            continue
        by_lid[(n["id"] - NODE_BASE) // NODE_STRIDE].append(n)
    ent_by_way = collections.defaultdict(list)
    for w in ways:
        for nid in w["nodes"]:
            if ENT_BASE <= nid < MH_BASE:
                ent_by_way[(w["id"] - WAY_BASE) // 4].append(nid)
    ent_nodes = {n["id"]: n for n in nodes if ENT_BASE <= n["id"] < MH_BASE}
    extra_by_tile = collections.defaultdict(list)
    for n in extra_nodes:
        extra_by_tile[z11(n["lon"], n["lat"])].append(n)
    all_tiles = set(per_tile) | set(extra_by_tile)
    for (tx, ty) in sorted(all_tiles):
        lids = per_tile.get((tx, ty), set())
        p = os.path.join(CACHE, "osm", f"osm_g1_z11_{tx}_{ty}.json")
        if not os.path.exists(p):
            print("  tile not in cache (skipped):", p)
            continue
        j = json.load(open(p, encoding="utf-8"))
        els = j["elements"]
        nd = {e["id"]: (e.get("lon"), e.get("lat")) for e in els if e["type"] == "node"}
        drop_w = set()
        kept = []
        for e in els:
            if e["id"] >= WAY_BASE and e["type"] in ("node", "way", "relation"):
                continue                       # a previous emitter run: replaced wholesale
            if e["type"] == "way" and ("building" in e.get("tags", {}) or "building:part" in e.get("tags", {})):
                pts = [nd[n] for n in e["nodes"] if n in nd and nd[n][0] is not None]
                if pts and in_cov(sum(q[0] for q in pts) / len(pts), sum(q[1] for q in pts) / len(pts)):
                    drop_w.add(e["id"])
                    continue
            kept.append(e)
        kept2 = []
        for e in kept:
            if e["type"] == "relation" and ("building" in e.get("tags", {}) or "building:part" in e.get("tags", {})):
                refs = [m["ref"] for m in e.get("members", []) if m["type"] == "way"]
                if refs and any(x in drop_w for x in refs):
                    continue
            kept2.append(e)
        ours = [n for l in lids for n in by_lid.get(l, [])]
        ours += [ent_nodes[nid] for l in lids for nid in ent_by_way.get(l, [])]
        ours += [w for w in ways if (w["id"] - WAY_BASE) // 4 in lids] + [r for r in rels if r["id"] - REL_BASE in lids] + extra_by_tile.get((tx, ty), [])
        print(f"  {os.path.basename(p)}: {len(els)} elements -> drop {len(els) - len(kept2)} OSM building ways/relations (and prior emitter output), add {len(ours)} ours")
        if a.write:
            keep_dir = os.path.join(CACHE, "osm-original")
            os.makedirs(keep_dir, exist_ok=True)
            orig = os.path.join(keep_dir, os.path.basename(p))
            if not os.path.exists(orig):
                shutil.copy2(p, orig)
            j["elements"] = kept2 + ours
            j["generator"] = (j.get("generator") or "").split(" + NordGrund")[0] + " + NordGrund emit_geodk v1"
            tmp = p + ".tmp"
            with open(tmp, "w", encoding="utf-8") as fh:
                json.dump(j, fh, ensure_ascii=False, separators=(",", ":"))
            os.replace(tmp, p)
            sb = p[:-5] + ".osmbin"
            if os.path.exists(sb):
                os.remove(sb)
            print("    written; sidecar removed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
