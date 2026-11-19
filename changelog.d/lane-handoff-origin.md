## Headless lane settings and origin checks

Keep a single effective fetch URL and a single effective push URL for the lane's
`origin`. The launcher fails a receipt if either destination changes or becomes
unreadable after a runtime round. Inspect `terminal.error` for the affected direction.

For Claude, use `request.approval_policy.settings_profile_path` to identify the
configured source and `settings_profile_sha256` to verify its bytes. Wrappers
around Claude must preserve the inherited descriptor named by `--settings`
until the client reads it, including on resume.
