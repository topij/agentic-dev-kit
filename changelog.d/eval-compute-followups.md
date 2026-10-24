## Compute maps of another shape are refused; `kit_doctor` reports them

CHANGED (engine CLI surface): `panel_prompt.py` now exits 2 on a
`review.fallback_panel.lens_compute` or `verifier_compute` value it used to read as
unset or ignore:

- a `lens_compute` section or runtime value that is an empty string, an empty list or
  `false` (it read as "inherit the cockpit's");
- a `review` or `review.fallback_panel` that is not a map;
- a runtime other than `claude` or `codex` under either section;
- a key other than `model` or `effort`, matched case-sensitively, so `modle` or
  `Effort` is refused.

A null `verifier_compute.claude.effort` now reads as unset instead of being refused.
If `panel_prompt.py` now refuses your config, fix the key it names, or drop it to inherit.

ADDED (report shape): `kit_doctor.py --json` gains `compute_problems`, a list holding the
refusal `panel_prompt.py` would print for each malformed compute map, and the text report
prints each one as a `⚠ compute config:` line. It is advisory and does not change the exit
status.
