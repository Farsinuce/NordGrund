# NordGrund fork features (REFERENCE §16 wish list), design as built, 3 Sep 2026

Fork branch `nordgrund` on `Farsinuce/arnis`, based on `78215bd`. Everything is behind one flag,
`--nordgrund <none|all|doors,torches,signs,lanterns,manholes>` (default `none`), appears in
`--help` for Meld's handshake, and is passed by Meld's new `nordgrund` project setting
(`src/arnis_cmd.py`, gated on `arnis_supports`). With the flag absent the golden gate is
byte-identical (5/5, same hashes as `78215bd`).

## Hooks in the fork (file:line at 78215bd, read 3 Sep 2026)

| what | where | fact |
|---|---|---|
| mapped entrance nodes | `buildings.rs:1136-1150` | an `entrance`/`door` node on the outline suppresses the preset doors; `doors.rs:5-24` places a dark-oak door at the node in element order, so a later wall can overwrite it (world #2 probe: 18 of 40 DAR entrances had a door) |
| our pass | `buildings.rs` after the interior, before the roof (`nordgrund::place_entrances`) | door, torch inside, sign outside, per entrance node; outward normal = the pass's own rule (`compute_outward_normal`, `:2991-3018`) |
| door height | `buildings.rs:2350` | `start_y_offset + abs_terrain_offset + 1` |
| ceiling lights | `buildings.rs:4705-4760` | glowstone at `x % 5 == 0 && z % 5 == 0` on every ceiling; ours: plain ceiling + `lantern[hanging=true]` one below on a 10-block world grid (`rem_euclid`) |
| node dispatch | `data_processing.rs:209` → `man_made.rs:525` | `man_made=manhole` now handled: grate at ground (`get_absolute_y(x,0,z)`), full water cauldron below; skipped when the cell above is not air |
| block entities | `world_editor/mod.rs:1018` (`insert_block_entity`, private) | new public `place_nordgrund_sign`: `front_text.messages` = four BARE strings, `back_text` empty, `is_waxed 1` (REFERENCE §11.2: the fork's dead `set_sign` and upstream JSON-quote the strings, which 26.2 rejects) |
| tag filter | `osm_parser.rs:46-63` | `addr:` was a discard prefix; `addr:street/housenumber/postcode` are now kept |
| blocks | `block_definitions.rs` ids 270-275 | pale_oak_wall_sign, pale_oak_wall_hanging_sign, wall_torch, waxed_weathered_copper_grate, lantern[hanging=true], water_cauldron[level=3] |

## Rules

- Door: `dark_oak_door` lower/upper with `facing` = outward normal, `hinge=left`.
- Torch: `wall_torch` in the cell inside the door at door_y + 2, facing into the room; only if
  that cell is air.
- Address sign: `pale_oak_wall_sign` outside at door_y + 2, facing out; lines = street (≤ 15
  chars, up to 2 lines) then the house number.
- Name board: a non-residential building (`nordgrund:residential=no` from the emitter, else the
  fork's residential type list) whose entrance carries `nordgrund:sign` (emitter: nearest named
  OSM shop/amenity/office/craft/tourism/leisure node inside the footprint or within 12 m), or
  whose way carries `nordgrund:sign`/`name`, gets a `pale_oak_wall_hanging_sign` with the name
  (≤ 10 chars × 4 lines) INSTEAD of the address sign (REFERENCE §16.4).
- Lanterns: 10-block grid keyed on world coordinates; the darkest floor cell (5 + 5 across,
  4 down) still reads light 1, which is what stops hostile spawns in 26.2. Applied to every
  ceiling, not only the ground floor: glowstone above ground is loot (PRIMER §1).
- Manholes: 14,227 GeoDanmark Broenddaeksel points in the pilot box.

## Measured on world #3 (project `aarhus-nordgrund`, 3 Sep 2026)

- Live 26.2 server (`tools/mcserver_check.py`, two chunks force-loaded): `data get block` returns
  `["Carl Blochs", "Gade", "42", ""]` for a wall sign and `["Godsbanens", "Åbne", "Værksteder", ""]`
  for a hanging sign: bare strings accepted, Danish letters intact, no serialization error.
- Every sign block has its block entity at the same position (10,078 blocks, 10,222 entities;
  the surplus are entities whose block a later pass replaced, harmless).
- At the emitted entrance nodes inside the cells: a door on 100 % (276 of 276), the address sign
  on 49–67 % (first build) because the facade pass had already put a lintel or accent block in
  the sign cell; fixed by letting the sign/torch replace the building's own relief (second build).
- 🟢 The fork writes a `minecraft:bed` block entity per bed; 26.2 has no such block-entity type
  and logs `Skipping block entity with invalid type` for each (30,149 per pilot world, also in
  world #1). Gated off for DataVersion ≥ 4903 on the branch.

## Open until walked

- Whether the ground pass (which runs last) preserves the grate at surface level.
- Sign readability in game (pale oak on brick), hanging-sign fit for long names.
- Doors on slopes: the door sits at the building's floor level, not the local terrain.
