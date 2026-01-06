# WarBits normalized data (v1)

This folder contains **normalized, domain-specific tables** extracted from the four Excel workbooks you provided.

Nothing here is "game logic" yet — this is the cleaned data layer we can load quickly and deterministically at runtime.

## What’s inside (counts)

- Vehicles: 688 records (merged across sources)
- Weapons: 391 records
- Warheads: 374 records
- Sensor packages (optics/TGP/weapon sights): 196 records
- Custom loadout meta: 8 aircraft blocks
- Custom loadout options: 306 slot-options

## Files

### vehicles.jsonl
Unified vehicle registry (currently aircraft-focused).

Sources merged:
- WarThunder_FactChecker2.xlsx: aircraft climb/time/speed vs altitude curves (301 aircraft, 2107 points)
- WarThunder_FactChecker1.xlsx: sea level top-speed table (230 aircraft)
- WarThunder_FactChecker1.xlsx: TGP and sights platform list (196 platforms)
- specialialdata.xlsx: Custom Loadouts aircraft list (8 aircraft)

Notes:
- Some aircraft exist in one source but not another (e.g., A-10A early/late have custom loadouts and sea-level speed, but not the detailed climb table).
- vehicles.jsonl keeps *all* sources and doesn’t discard “partial” aircraft — missing performance just means we don’t yet have that performance.

### aircraft_performance_points_fc2.csv
Flattened points from FactChecker2 for easier plotting/debugging:
- altitude_m
- climb_time_*_s
- max_speed_wep_* values

### sea_level_speed_fc1.csv
Sea-level top speed table from FactChecker1 (aircraft list with BR + top speed).

### weapons.jsonl
Unified weapons registry built from:
- FactChecker1 “Missile Data” (row-based table)
- FactChecker1 transposed weapon sheets (AAM/AGM/GBU/SAM/ATGM/AShM)

Structure:
- `fields`: canonical numeric values we recognize (mass, thrust, burn time, ΔV, tnt eq, etc.)
- `raw_fields`: everything else kept verbatim-ish for later mapping
- `sources`: which sheet(s) contributed

### warheads.jsonl
Warhead entries extracted from weapon sheets when explosive TNT equivalent and/or warhead type is present.

### sensors_tgp_and_sights.jsonl
Per-aircraft optics/sensor packages:
- built-in sights
- targeting pod info
- weapon sight info

### custom_loadout_meta.jsonl
Per-aircraft custom-loadout constraints:
- max_load_kg
- max_left_load_kg
- exempt_from_imbalance_calcs

### custom_loadout_options.jsonl
Per-aircraft slot/category options, including:
- slot index
- option text
- parsed `quantity` + `weapon_name`
- `weapon_id_match` when we could match to weapons.jsonl

### vehicle_alias_candidates.jsonl
Small list of automatic alias suggestions (currently just A-10A early/late → A-10A).

## Known gaps (by design, for now)

- Hardpoint geometry and real “station limits” aren’t present in these sheets; we’re only capturing the *allowed* options.
- Dumb bombs/rockets/gunpods aren’t in FactChecker1 weapon sheets, so many loadout options won’t match a weapon_id yet.
  - Next step: create placeholder weapon records for those from loadouts, *or* locate them in another sheet/source.
- Terrain/biome tables aren’t present in these Excel files — those will be authored directly in our own data schema.

