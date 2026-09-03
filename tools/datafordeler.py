#!/usr/bin/env python3
"""Datafordeler FileDownloads client with provenance pinning (REFERENCE §17, CONSULT §9).

    python tools/datafordeler.py list   <Register> [--grep REGEX] [--max N]
    python tools/datafordeler.py get    <FileName> [--out DIR]            # vector zip, md5 from the listing
    python tools/datafordeler.py raster <FileName> [--out DIR]            # DHM tile, sha256 self-computed
    python tools/datafordeler.py latest <Register> <Entity> [--muni 0751] [--format json|csv] [--out DIR]

The key travels in the query string: never log a full URL. Every fetched file is recorded in
<repo>/manifest.json (tracked) with md5Hash/pointInTime from the listing, our sha256, bytes and time.
Only PageNumber paginates; raster listings cap pageSize at 100; HEAD 404s; a filename is never a
vintage pin. Reads DATAFORDELER_KEY from <repo>/.env (gitignored).
"""
from __future__ import annotations
import argparse, hashlib, json, os, re, sys, time
import requests

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = "https://api.datafordeler.dk/FileDownloads"
MANIFEST = os.path.join(ROOT, "manifest.json")

def key() -> str:
    for ln in open(os.path.join(ROOT, ".env"), encoding="utf-8"):
        if ln.startswith("DATAFORDELER_KEY="): return ln.strip().split("=", 1)[1].strip().strip('"')
    sys.exit("DATAFORDELER_KEY missing from .env")

def redact(url: str) -> str:
    return re.sub(r"apiKey=[^&]+", "apiKey=***", url)

def listing(register: str) -> list[dict]:
    out, page = [], 1
    while True:
        for attempt in range(4):          # spurious 401s hit LISTING calls, not GetFile: retry
            r = requests.get(f"{BASE}/v2.0/GetAvailableFileDownloads", params={"Register": register, "PageSize": 10000, "PageNumber": page, "apiKey": key()}, timeout=120)
            if r.status_code == 200: break
            time.sleep(2 * (attempt + 1))
        r.raise_for_status(); j = r.json()
        items = j.get("availableFileDownloads", []) if isinstance(j, dict) else j
        out.extend(items)
        if len(items) < 10000: break
        page += 1
    return out

def pick_latest(register: str, entity: str, muni: str | None, fmt: str) -> dict | None:
    """Newest generation of a TotalDownload/Current file for entity (+ kommune) in the given format."""
    c = [it for it in listing(register) if it.get("entityName") == entity and it.get("typeOfDownload") == "TotalDownload"
         and it.get("typeOfData") == "Current" and (it.get("containedFileFormat") or "").lower() == fmt.lower()
         and ((it.get("municipalityCode") or None) == muni)]
    return max(c, key=lambda it: int(it.get("generationNumber") or 0)) if c else None

def _download(url: str, params: dict, dest: str) -> tuple[int, str, str]:
    md5 = hashlib.md5(); sha = hashlib.sha256(); n = 0
    with requests.get(url, params=params, stream=True, timeout=600) as r:
        if r.status_code != 200: raise SystemExit(f"{redact(r.url)} -> {r.status_code}: {r.text[:300]}")
        with open(dest + ".part", "wb") as fh:
            for chunk in r.iter_content(1 << 20):
                fh.write(chunk); md5.update(chunk); sha.update(chunk); n += len(chunk)
    os.replace(dest + ".part", dest)
    return n, md5.hexdigest(), sha.hexdigest()

def pin(entry: dict) -> None:
    m = json.load(open(MANIFEST, encoding="utf-8")) if os.path.exists(MANIFEST) else {"_readme": "Provenance pins for downloaded source data: a filename is never a vintage pin; md5Hash + pointInTime (from the listing) and our sha256 are. Written by tools/datafordeler.py.", "files": []}
    m["files"] = [f for f in m["files"] if f.get("path") != entry["path"]] + [entry]
    json.dump(m, open(MANIFEST, "w", encoding="utf-8", newline="\n"), indent=1, ensure_ascii=False)

def cmd_list(a):
    items = listing(a.register); rx = re.compile(a.grep, re.I) if a.grep else None
    shown = 0
    for it in items:
        fn = it.get("fileName") or it.get("filename") or ""
        if rx and not rx.search(fn): continue
        print(f"{fn}  entity={it.get('entityName')} muni={it.get('municipalityCode')} gen={it.get('generationNumber')} pointInTime={it.get('pointInTime')} md5={it.get('md5Hash')}"); shown += 1
        if a.max and shown >= a.max: break
    print(f"({shown} shown of {len(items)} listed for {a.register})")

def cmd_get(a, raster=False):
    out = a.out or os.path.join(ROOT, "data", "raster" if raster else "vector"); os.makedirs(out, exist_ok=True)
    dest = os.path.join(out, a.filename)
    meta = {}
    if not raster:
        reg = a.filename.split("_")[0]
        for it in listing(reg):
            if (it.get("fileName") or "") == a.filename: meta = it; break
    t0 = time.time()
    n, md5, sha = _download(f"{BASE}/{'GetRasterFile' if raster else 'GetFile'}", {"FileName": a.filename, "apiKey": key()}, dest)
    ok = (meta.get("md5Hash") is None) or (meta["md5Hash"].lower() == md5)
    print(f"{a.filename}: {n:,} bytes in {time.time()-t0:.0f}s  md5={md5} listing_md5={meta.get('md5Hash')} match={ok}  sha256={sha[:16]}…")
    if not ok: os.remove(dest); sys.exit("md5 mismatch: file removed")
    pin({"fileName": a.filename, "path": os.path.relpath(dest, ROOT), "register": a.filename.split("_")[0], "bytes": n, "md5Hash": md5, "sha256": sha,
         "pointInTime": meta.get("pointInTime"), "listing_md5": meta.get("md5Hash"), "fetched": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())})

def cmd_latest(a):
    it = pick_latest(a.register, a.entity, a.muni, a.format)
    if not it: sys.exit(f"no TotalDownload/Current {a.format} file for {a.register}/{a.entity} muni={a.muni}")
    print("picked:", it["fileName"], "gen", it.get("generationNumber"), "pointInTime", it.get("pointInTime"))
    a.filename = it["fileName"]; cmd_get(a)

def main():
    ap = argparse.ArgumentParser(); sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("list"); p.add_argument("register"); p.add_argument("--grep"); p.add_argument("--max", type=int, default=0)
    p = sub.add_parser("get"); p.add_argument("filename"); p.add_argument("--out")
    p = sub.add_parser("raster"); p.add_argument("filename"); p.add_argument("--out")
    p = sub.add_parser("latest"); p.add_argument("register"); p.add_argument("entity"); p.add_argument("--muni"); p.add_argument("--format", default="json"); p.add_argument("--out")
    a = ap.parse_args()
    if a.cmd == "list": cmd_list(a)
    elif a.cmd == "get": cmd_get(a)
    elif a.cmd == "raster": cmd_get(a, raster=True)
    elif a.cmd == "latest": cmd_latest(a)

if __name__ == "__main__":
    main()
