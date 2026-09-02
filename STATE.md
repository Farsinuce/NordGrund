# STATE.md

Where the work is right now. Rewritten in place at the end of every session, never appended.
Kept short. File name and format are [PROPOSED].

## 1 Sep 2026

- **Workspace:** `CLAUDE.md`, `decisions.md`, this file, the three PIVOT files and
  `NordGrund.code-workspace`. Not a git repo. No forks, no code, no credentials in use.
- **Next:** PRIMER §5 work item 1, which waits on nobody. Creating our own repos waits on
  `decisions.md` A.
  1. Clone `Teddy563/meld` at `5c1353e`.
  2. Fetch the fork's v3.1.8 release binary (== `78215bd`) and place it beside `meld_launch.py`.
  3. Apply PRIMER §3 through `project.json` and the local API.
  4. Generate the pilot tile 6223_574 (central Aarhus) across at least one Meld cell border.
  5. Walk it against build 9 (PRIMER §4). Ask the user to re-review PRIMER §3 (`decisions.md` F).
- **PRIMER §3 was re-verified 1 Sep 2026** against Meld `5c1353e`: four defaults were wrong for us
  (scale, buildings, bake lighting, snow); the section is the runbook.
- **Machine** (verified 1 Sep 2026; re-run the version commands before relying on any of it):
  - Python 3.12.9 (Meld needs 3.10+).
  - Rust stable, installed 1 Sep; open a fresh shell for `cargo`.
  - Java: the 26.2 server needs Java 25. `java` on PATH is 25.0.4 today, but a JDK 21 is also
    installed, so launch with `C:\Program Files\Java\jdk-25.0.4\bin\java.exe` by absolute path.
  - A 26.2 server runtime is at `d:\ai\KlodsDanmark\testserver` (`server.jar`, `libraries/`);
    boot flags in the old repo's `tools/mcserver.py` (`-Xmx2G -Xms1G`, four `-D*.encoding=UTF-8`
    flags, `nogui`).
- **Walk logistics:** point a copied server runtime at a COPY of build 9, never at
  `testserver\denmark-test` (loading dirties chunks, REFERENCE §12).
- **Time-critical:** DAWA closes 1 Oct 2026 (`decisions.md` G).
- **Pins** (🟡 from the message of old-repo commit 09cbf36): PRIMER and REFERENCE were verified at
  Teddy563/arnis `78215bd` and Teddy563/meld `5c1353e` (both still HEAD, last pushed 27 Aug 2026)
  and louis-e/arnis `c7b5f19` (upstream moved past it on 31 Aug 2026 and again on 1 Sep).
