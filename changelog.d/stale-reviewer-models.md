## Codex model-cache advisory

ADDED (report / return shape): `kit_doctor.py --json` includes `codex_models`
with cache path, observation state/detail and explicit model-pin observations.
Update consumers that pin the report shape. Read missing-pin and newer-family
advisories before upgrading; they do not change exit status. Follow the model
upgrade procedure in `fallback-review-panel.md` and retain comparison evidence.
