## Triage sweep: one blank line before each heading and one newline at EOF

CHANGED — report shape: Refresh `lib/triage/inbox.py`, `lib/triage/finalize.py`,
`lib/triage/engine.py`, `scripts/tests/test_triage_inbox.py` and
`scripts/tests/test_finalize_triage.py`. The sweep's new inbox now has exactly one blank line
before each `## ` heading outside code, and ends in exactly one newline (#1396, #1474).
Before, a heading lost its blank line when the sweep removed the last entry of the
section above it and kept an earlier one. And when the sweep removed the file's last
entry, the blank line before it was left at EOF. `finalize.RENDERINGS` gains `pre-1474`,
the previous layout, and commit validation accepts it, so a sweep an older engine
committed still validates. `inbox.normalize_seams` is new. An inbox that already had
extra blank lines before a heading or at EOF loses them in its next sweep commit.
Update any test that expects the old spacing from `render_sweep`.
