## Run fallback review commands in a credential-free worker

Provision the reviewer worker described in `fallback-review-panel.md` and verify
its shell and tool access. Configure `review.fallback_panel.worker_launcher` in
the trusted deployment and use its `panel_prompt.py --launch --root <checkout>`
for lenses and verifiers. Regenerate
each installed Claude lens with `panel_prompt.py --lens <name> --agent-definition`
from the trusted installation and load the new definitions in a fresh session.
