## Codex reviewer and verifier model defaults

Set `review.fallback_panel.lens_compute.codex.model` and
`review.fallback_panel.verifier_compute.codex.model` to `gpt-6.1-sol` to adopt
the upgraded defaults. Keep lens effort at `medium` and verifier effort at `low`,
or choose values supported by your account. Existing adopter configuration is
preserved by `init.sh`; newly seeded panels use these defaults.

Before selecting the new model, update the Codex client used to launch reviews
and confirm that your account can run `gpt-6.1-sol`. A client that rejects the
model cannot complete the fallback review; retain your existing model until that
prerequisite is met.
