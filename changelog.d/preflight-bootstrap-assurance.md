## Narrative preflight dependency bootstrap

Refresh the shared fallback-review doctrine. Allow for `uv run` dependency
bootstrap before the Python checker starts, including package-index access and
cache/environment writes. Retain stdout, stderr and process status when no JSON
report is produced; establish the unavailable check independently with retained
evidence, or hold the review receipt.
