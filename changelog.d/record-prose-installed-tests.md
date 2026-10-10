## Installed narrative-checker tests

Refresh `scripts/tests/test_record_prose.py` in your configured engine directory.
Its prerequisite checks now use the installed paths, so vendored checker tests run
instead of skipping an engine installed outside the kit's default `scripts/` layout.
