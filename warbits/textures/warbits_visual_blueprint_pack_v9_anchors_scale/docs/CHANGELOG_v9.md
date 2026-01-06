# Changelog — Visual Blueprint Pack v9 (Anchors + Attachments + Scale Fit)

## Added
- `warbits.visual.anchors`
  - `AnchorDB` (JSONL) + deterministic default anchor generation.
- `warbits.visual.scale_fit`
  - Uniform + non-uniform scale fitting helpers for real-world dimensions.
- `warbits.visual.attach`
  - Minimal pose + attachment helpers to mount child blueprints.
- `warbits.visual.tools.anchors_cli`
  - CLI to build, inspect, and edit anchors JSONL.

## Updated
- `warbits.visual.registry.VisualRegistry`
  - optional anchor DB merge + cached bounds/dims/center helpers.

## Tests
- Anchor generation and merge behavior
- Scale fit
- Attachment positioning
