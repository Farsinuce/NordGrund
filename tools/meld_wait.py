#!/usr/bin/env python3
"""Poll a running Meld until the generation run is over, printing progress; exit 0 when every
planned cell is merged, 1 otherwise.   python tools/meld_wait.py [--interval 30] [--max-minutes 180]"""
from __future__ import annotations
import argparse, sys, time, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from meld_api import Meld

def main() -> int:
    ap = argparse.ArgumentParser(); ap.add_argument("--interval", type=float, default=30); ap.add_argument("--max-minutes", type=float, default=180)
    a = ap.parse_args(); m = Meld(); t0 = time.time(); seen = 0; idle_polls = 0
    while True:
        st = m.get("/api/status"); run = st.get("run", {}); pf = st.get("prefetch", {}); grid = st.get("grid", {})
        logs = st.get("log", [])
        new = logs[seen:] if len(logs) >= seen else logs
        seen = len(logs)
        for ln in new[-12:]: print("  |", ln if isinstance(ln, str) else ln.get("msg", ln))
        busy = [w for w in st.get("workers", []) if w.get("running")]
        counts = {}
        for v in grid.values(): counts[v] = counts.get(v, 0) + 1
        print(f"[{(time.time()-t0)/60:5.1f} min] phase={run.get('phase')} active={run.get('active')} done={run.get('done')}/{run.get('total')} failed={run.get('failed')} "
              f"prefetch={pf.get('phase')}:{pf.get('note','')[:60]} terrain={pf.get('terrain')} busy={[(w['cell_key'], w.get('progress'), w.get('message','')[:40]) for w in busy]} grid={counts}", flush=True)
        finished = (not run.get("active")) and (not pf.get("active")) and not busy
        if finished: idle_polls += 1
        else: idle_polls = 0
        if idle_polls >= 2 and grid:
            print("cell_health:", st.get("cell_health")); print("cell_fail:", st.get("cell_fail"))
            return 0 if all(v == "merged" for v in grid.values()) else 1
        if (time.time() - t0) / 60 > a.max_minutes:
            print("TIMEOUT waiting for the run"); return 2
        time.sleep(a.interval)

if __name__ == "__main__":
    sys.exit(main())
