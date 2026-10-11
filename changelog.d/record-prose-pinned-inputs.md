## Record preflight object and date validation

Refresh `check_record_prose.py` and its tests. Preflight reads now ignore Git
replacement refs and graft files so local history rewrites cannot substitute
content or ancestry for the named commit objects.

Plain-text stamp dates are checked as complete whitespace-delimited tokens,
apart from trailing sentence punctuation and closing delimiters. Correct malformed
suffixes such as `2026-10-10/junk` instead of relying on a valid date prefix.
