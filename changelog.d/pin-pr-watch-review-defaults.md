## PR watcher fallback review markers

BREAKING (gate semantics) — If you inherit the built-in noise markers, a
comment quoting `review skipped` or `bugbot needs on-demand usage enabled`
can now appear in `new_comments` and hold convergence. Inspect and acknowledge
it through the usual watch loop. Use `review.noise_markers` for custom filtering (#40).

If you match the reported outage reason, allow `review rate limited` to take
precedence over `couldn't start this review`, `review skipped` and
`no review credits` when the same message contains both markers and the watcher
uses its built-in outage list (#40).
