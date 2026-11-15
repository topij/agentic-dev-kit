## Record lane reviews from the cockpit

After upgrading the lane engines together, use `dev_session.sh pr-watch <scope>`
from the cockpit to poll, handle findings, and record independent review at the
reviewed head. The merge and reconciliation checks read that session's
`cockpit-state/pr-watch/`. Start a fresh watch and review for open lanes whose
acknowledgements, settle baseline and receipt were recorded in the lane sandbox.
