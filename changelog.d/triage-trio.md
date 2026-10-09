## Triage engine: comma id refusal names the separator; finalize `resume_action` names the flag; an emptied section's intro is archived

CHANGED (report / return shape): an approval command whose ids contain a comma, such
as `approve TRI-01,TRI-02`, is still refused, now with the detail `malformed approval
command: ids are space-separated; a comma is not a separator` rather than `mixed or
malformed approval command` (#1016). The triage report's command help gains a line
saying ids are space-separated. A pinned test that matches the old detail for a comma
needs updating; send ids separated by spaces.

CHANGED (report / return shape): a triage resume, or a refused `new`, against a session
in `forge-finalize` or `archive-sweep` now returns `resume_action` `resume with
{"finalize": true}` instead of `resume` (#1017). Every finalize continuation must carry
`finalize: true`, not only the first. A caller that compares `resume_action` to
`resume` for those phases needs updating.

CHANGED (report / return shape): when a triage sweep removes every entry of a dated
section, the prose between that section's heading and its first entry now moves to the
archive with the entries, directly under the same date heading, and the section leaves
the inbox (#1018). Before, the heading and its prose stayed in the inbox. A section that
keeps an entry keeps its prose. Commit validation still accepts a sweep an earlier
engine committed. Nothing to do unless you pin the swept inbox or archive bytes.
