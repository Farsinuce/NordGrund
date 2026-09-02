"""Tiny client for a locally running Meld (5c1353e). Token comes from <MELD_DATA_DIR>/session.json."""
from __future__ import annotations
import json, os, sys, time
import requests

DATA_DIR = os.environ.get("MELD_DATA_DIR", r"D:\ai\NordGrund\data\meld-data")

def session() -> dict:
    return json.load(open(os.path.join(DATA_DIR, "session.json"), encoding="utf-8"))

class Meld:
    def __init__(self, url: str | None = None, token: str | None = None):
        s = session()
        self.url = (url or s["url"]).rstrip("/")
        self.h = {"X-Meld-Token": token or s.get("token", "")}
    def get(self, path: str, timeout: float = 60):
        r = requests.get(self.url + path, headers=self.h, timeout=timeout); r.raise_for_status(); return r.json()
    def post(self, path: str, body: dict | None = None, timeout: float = 600, ok_codes=(200,)):
        r = requests.post(self.url + path, headers=self.h, json=body or {}, timeout=timeout)
        try: j = r.json()
        except Exception: j = {"raw": r.text}
        if r.status_code not in ok_codes:
            raise RuntimeError(f"POST {path} -> {r.status_code}: {json.dumps(j)[:800]}")
        return j

def dump(o) -> str:
    return json.dumps(o, indent=1, ensure_ascii=False)

if __name__ == "__main__":
    m = Meld(); print(dump(m.get(sys.argv[1] if len(sys.argv) > 1 else "/api/state")))
