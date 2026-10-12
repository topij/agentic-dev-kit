## Record-prose preflight: a closing-keyword pairing moved unchanged between narrative paths is no longer reported

CHANGED (gate semantics): `scripts/check_record_prose.py` no longer reports a
keyword/reference pairing whose every line was moved unchanged, in order, from one
contiguous run of lines the same change deletes from a configured narrative path. An
archive sweep that moves inbox entries containing such a pairing now passes, where it
used to exit 1. A pairing copied while its source stays, one a move newly joins, and
every commit message are still reported. The JSON report's `limits` list gains one
entry describing this.

Take `scripts/check_record_prose.py` together with
`docs/agentic-dev-kit/fallback-review-panel.md`, which describes the check to the
review lens. If you vendor the kit's tests, take `scripts/tests/test_record_prose.py`
as well.
