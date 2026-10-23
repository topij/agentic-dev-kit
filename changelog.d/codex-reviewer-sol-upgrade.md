## Codex reviewer and verifier model defaults

Set `review.fallback_panel.lens_compute.codex.model` and
`review.fallback_panel.verifier_compute.codex.model` to `gpt-6.1-sol` to adopt
the upgraded defaults. Keep lens effort at `medium` and verifier effort at `low`,
or choose values supported by your account. Existing adopter configuration is
preserved by `init.sh`; newly seeded panels use these defaults.
