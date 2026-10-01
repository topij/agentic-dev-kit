Treat the user's request as the optional PR number or additional watch context. Resolve
the configured engine path from the repository root.

When the fallback panel runs, use one isolated fresh-context reviewer per configured
lens. Carry `review.fallback_panel.lens_compute.codex` on the `codex exec` argv as
`-c model_reasoning_effort=<effort>` and, when configured, `-m <model>`; read the
applied values back from the rollout. Translate only runtime-native reviewer isolation
and available mechanisms, and never treat an unavailable reviewer as a waiver.
