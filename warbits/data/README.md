WarBits Data Tables
===================

This folder contains normalized data tables generated from the Excel
sources under `warbits/data/raw`.

How to regenerate
-----------------
- `pip install -e .[data]`
- `python tools/data_pipeline/build_tables.py`
- Requires `openpyxl` and `pandas` for Excel parsing.

Validation
----------
- `python -m warbits.tools.validate_data`

Tables
------
- `vehicles.json`: aircraft performance profiles with derived max speed and
  best climb rate.
- `weapons.json`: weapon records normalized from FactChecker1 sheets.
- `warheads.json`: warhead records derived from weapons (1:1 by default).
- `sensors.json`: built-in sights and targeting pods from the TGP sheet.
- `terrain.json`: seed biome/material records (placeholders for now).
- `loadouts.json`: empty placeholder (custom loadouts need a clearer schema).
- `data_summary.json`: counts and warnings from the build script.

Notes
-----
- Raw Excel sources live in `warbits/data/raw`.
- Normalized ingest outputs live in `warbits/data/normalized`.
- Climb times in FactChecker2 are stored as hh:mm in Excel but represent
  mm:ss; the pipeline converts them to seconds using that assumption.
- Most unmatched fields from the weapon sheets are preserved under
  `attributes` for later mapping.
