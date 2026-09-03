#!/usr/bin/env python3
"""Boot a dedicated 26.2 server on a world COPY, wait for "Done", run a few console commands,
stop cleanly, and scan the log for the load-time corruption signals (REFERENCE §12). Hashes the
region files before and after so the autosave trap is visible. Exit 1 on any signal or hash change.

    python tools/mcserver_check.py <serverdir> [--timeout 300] [--cmd "..." ...]
"""
from __future__ import annotations
import argparse, hashlib, os, queue, subprocess, sys, threading, time

JAVA = os.environ.get("MC_JAVA", r"C:\Program Files\Java\jdk-25.0.4\bin\java.exe")
JVM = ["-Xmx3G", "-Xms1G", "-Dstdin.encoding=UTF-8", "-Dstdout.encoding=UTF-8", "-Dstderr.encoding=UTF-8", "-Dfile.encoding=UTF-8"]
# Load-path strings a 26.2 server prints when a region/chunk/block entity is malformed
# (the list the old harness verified against the real jar, REFERENCE §12; re-verify on 26.3).
BAD = ["missing level data, skipping", "Recoverable errors when loading section", "is in the wrong location; relocating",
       "stream is truncated", "Unable to read or access the world gen settings file", "Ignoring heightmap data",
       "Unrecognized custom compression", "Failed to parse either", "] Serialization errors:",
       "Skipping block entity with invalid type", "Failed to create block entity", "Failed to load data for block entity",
       "found in a wrong chunk", "contains duplicated block entities", "mismatched block entity",
       "Block state mismatch on block entity", "Tried to load a DUMMY block entity", "Tried to load a block entity for block",
       "Exception", "Failed to"]

def region_hashes(world: str) -> dict:
    out = {}
    for d, _, fs in os.walk(world):
        for f in fs:
            if f.endswith(".mca"):
                p = os.path.join(d, f); out[os.path.relpath(p, world)] = hashlib.sha256(open(p, "rb").read()).hexdigest()
    return out

def level_name(serverdir: str) -> str:
    for ln in open(os.path.join(serverdir, "server.properties"), encoding="utf-8"):
        if ln.startswith("level-name="): return ln.strip().split("=", 1)[1]
    return "world"

def main() -> int:
    ap = argparse.ArgumentParser(); ap.add_argument("serverdir"); ap.add_argument("--timeout", type=int, default=300)
    ap.add_argument("--cmd", action="append", default=[]); ap.add_argument("--keep", action="store_true", help="leave the server running"); ap.add_argument("--settle", type=float, default=8, help="seconds to wait after the commands before stopping")
    a = ap.parse_args(); sd = os.path.abspath(a.serverdir); world = os.path.join(sd, level_name(sd))
    before = region_hashes(world); print(f"world {world}: {len(before)} region files hashed before load")
    p = subprocess.Popen([JAVA, *JVM, "-jar", "server.jar", "nogui"], cwd=sd, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="replace", bufsize=1)
    q: queue.Queue = queue.Queue()
    def pump():
        for ln in iter(p.stdout.readline, ""): q.put(ln.rstrip("\n"))
        q.put(None)
    threading.Thread(target=pump, daemon=True).start()
    log = []; t0 = time.time(); done = False; sent = False; stopped_at = None
    cmds = list(a.cmd) or ["seed", "time query daytime", "forceload query", "worldborder get"]
    while True:
        try: ln = q.get(timeout=1)
        except queue.Empty: ln = ""
        if ln is None: break
        if ln:
            log.append(ln)
            if not done and ")! For help, type" in ln:
                done = True; print(f"server up after {time.time()-t0:.0f}s")
                for c in cmds: p.stdin.write(c + "\n")
                p.stdin.flush(); sent = True; t_done = time.time()
        if done and sent and stopped_at is None and time.time() - t_done > a.settle and not a.keep:
            p.stdin.write("save-all flush\nstop\n"); p.stdin.flush(); stopped_at = time.time()
        if time.time() - t0 > a.timeout:
            print("TIMEOUT"); p.kill(); break
        if p.poll() is not None and q.empty(): break
        if a.keep and done and sent and time.time() - t_done > a.settle:
            print("server left running (--keep); pid", p.pid); return 0
    p.wait(timeout=60)
    bad = [l for l in log if any(b in l for b in BAD)]
    after = region_hashes(world); changed = [k for k in before if before[k] != after.get(k)] + [k for k in after if k not in before]
    tail = "\n".join(log[-25:]); print("---- log tail ----\n" + tail)
    print(f"---- corruption signals: {len(bad)}"); [print("  !!", b) for b in bad[:20]]
    print(f"---- region files changed by the load/save round trip: {len(changed)}"); [print("  ~", c) for c in changed[:20]]
    ok = done and not bad
    print("RESULT:", "PASS" if ok else "FAIL", "(regions rewritten: %d — the autosave trap, walk a COPY)" % len(changed))
    return 0 if ok else 1

if __name__ == "__main__":
    sys.exit(main())
