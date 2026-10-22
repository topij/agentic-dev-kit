## `review.fallback_panel.verifier_compute` declares the verifier's compute

ADDED (config key): `review.fallback_panel.verifier_compute.<runtime>`, with optional
`model` and `effort` like `lens_compute` (#1155). The kit ships `claude: {model: haiku}`
and `codex: {model: gpt-5.6-sol, effort: low}`, and `init.sh` writes it only into a
fresh `fallback_panel` block. To adopt it, add the block under your
`review.fallback_panel`, each runtime with its `# runtime-status:` line. Without it, the
verifier's `Run at:` line still names the cockpit's choice.

CHANGED (engine CLI surface): `panel_prompt.py --verifier` exits 2 when that key's
value for the runtime is not a map, or holds a `model` or `effort` that is not one word
of letters, digits, `.`, `_` or `-`.
