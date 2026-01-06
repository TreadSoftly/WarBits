# Visual Blueprint Sources (Free / Non-Paid)

This doc is NOT a requirement to run WarBits.
It exists to help you build a *large visual blueprint DB* without paying for assets.

## High-leverage sources to investigate

### 1) Wikimedia Commons aircraft 3-view drawings
- Many aircraft have vector-ish 3-view drawings.
- Licenses vary (public domain, CC-BY, CC-BY-SA).
- These are useful for:
  - generating 2D silhouettes
  - extracting outlines
  - validating proportions

### 2) Objaverse / Objaverse-XL
- Very large dataset of 3D objects with metadata.
- IMPORTANT: **individual objects have individual licenses**.
- Use the metadata to filter for:
  - CC0 / CC-BY (ship-safe)
  - avoid NC/ND if you plan to distribute commercially

### 3) Public-domain government docs
- Some technical drawings and manuals are public domain (varies by country and document).

## Policy suggestion

Even if you ingest models locally:
- store per-blueprint provenance + license fields
- add a filter step that can exclude “not safe to redistribute” assets

This avoids getting kneecapped later when you want to ship.

