#!/usr/bin/env python3
"""DAR address chain for one kommune (CONSULT §9): Husnummer (national, status 3) whose adgangspunkt
is one of the kommune's Adressepunkt rows -> street name (NavngivenVej) + house number + the access
point's EPSG:25832 position + the GeoDanmark building id it belongs to.

    python tools/dar_chain.py --muni 0751 --out data/derived/dar_0751.csv

Output columns: husnummer_seq (stable small int from the sorted Husnummer id), husnummer_id, status,
adgangspunkt_id, E, N, noejagtighed, vejnavn, husnummertekst, postnr, building_id (GeoDanmark
id_lokalId, may be empty), bbr_building (BBR uuid, may be empty). Streams the 1.7 GB CSV once.
"""
from __future__ import annotations
import argparse, csv, glob, io, os, sys, zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
csv.field_size_limit(1 << 30)


def open_csv(pattern: str):
    zp = sorted(glob.glob(os.path.join(ROOT, "data/vector", pattern)))[-1]
    z = zipfile.ZipFile(zp)
    name = z.infolist()[0].filename
    fh = z.open(name)
    return csv.DictReader(io.TextIOWrapper(fh, encoding="utf-8", newline="")), zp


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--muni", default="0751")
    ap.add_argument("--out", default=os.path.join(ROOT, "data/derived/dar_0751.csv"))
    a = ap.parse_args()
    rd, zp = open_csv(f"DAR_V*_Adressepunkt_{a.muni}_*.zip")
    points = {}
    for r in rd:
        if r.get("status") != "8":          # Adressepunkt: 8 = gældende (Husnummer/NavngivenVej use 3)
            continue
        pos = r.get("position") or ""
        if not pos.startswith("POINT"):
            continue
        xy = pos[pos.find("(") + 1:pos.find(")")].split()
        points[r["id_lokalId"]] = (float(xy[0]), float(xy[1]), r.get("oprindelse_nøjagtighedsklasse") or "")
    print(f"{os.path.basename(zp)}: {len(points)} status-8 access points")
    rd, zp = open_csv("DAR_V*_NavngivenVej_TotalDownload_csv_*.zip")
    streets = {}
    for r in rd:
        if r.get("status") == "3":
            streets[r["id_lokalId"]] = r.get("vejnavn") or ""
    print(f"{os.path.basename(zp)}: {len(streets)} status-3 named roads")
    rd, zp = open_csv("DAR_V*_Husnummer_TotalDownload_csv_*.zip")
    rows = []
    n = 0
    for r in rd:
        n += 1
        ap_ = r.get("adgangspunkt") or ""
        if ap_ not in points or r.get("status") != "3":
            continue
        E, N, acc = points[ap_]
        rows.append({"husnummer_id": r["id_lokalId"], "status": r["status"], "adgangspunkt_id": ap_, "E": f"{E:.2f}", "N": f"{N:.2f}",
                     "noejagtighed": acc, "vejnavn": streets.get(r.get("navngivenVej") or "", ""), "husnummertekst": r.get("husnummertekst") or "",
                     "postnr": (r.get("adgangsadressebetegnelse") or "").rsplit(",", 1)[-1].strip().split(" ")[0] if r.get("adgangsadressebetegnelse") else "",
                     "building_id": r.get("geoDanmarkBygning") or "", "bbr_building": r.get("adgangTilBygning") or ""})
    print(f"{os.path.basename(zp)}: {n} rows streamed, {len(rows)} status-3 house numbers in kommune {a.muni}")
    rows.sort(key=lambda x: x["husnummer_id"])
    for i, x in enumerate(rows):
        x["husnummer_seq"] = i + 1
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    with open(a.out, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["husnummer_seq"] + [k for k in rows[0] if k != "husnummer_seq"])
        w.writeheader()
        w.writerows(rows)
    with_b = sum(1 for x in rows if x["building_id"])
    noname = sum(1 for x in rows if not x["vejnavn"])
    print(f"written {a.out}: with GeoDanmark building id {with_b} ({100 * with_b / len(rows):.1f}%), missing street name {noname}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
