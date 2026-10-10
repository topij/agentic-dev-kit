# Ticket execution environment

Every new tracker ticket records where its complete acceptance criteria can be
implemented and verified. Apply this contract to ad hoc tickets as well as the
`wrap-up`, `triage-friction-log`, and `post-merge-systemize` tracker routes.
It is shared by runtimes; it grants no tracker-write or merge authority.

## Classify before presenting the payload

| Value | Meaning |
|---|---|
| `cloud` | A fresh checkout can implement and verify the complete ticket using tracked files, reproducible fixtures, and explicitly named services or setup available to the cloud session. |
| `local` | Completion requires an existing machine's files, ignored or untracked artifacts, retained state, another local checkout, a desktop app, hardware, or machine-bound access that the cloud session cannot reproduce. |
| `unknown` | The required inputs or verification environment have not been established. Missing metadata means unknown, never cloud. |

Classify the acceptance criteria, not the title or the files being edited. A code
change requiring validation against an adopter's retained ignored state is `local`.
A test that generates its own ignored fixtures can be `cloud`. File ignore status
alone does not decide portability. Name tools, network access and authentication
needed for `cloud`; the classification does not promise those capabilities are
available in every session. If credentials or service access have not been
established for the intended cloud setup, record `unknown`.

For mixed work, classify the whole ticket as `local` when its required local
verification remains. A cloud authoring portion can be described explicitly, or
proposed as a separate ticket with its own acceptance criteria. Do not quietly
drop local verification to call the original ticket cloud-capable.

Include this section in the proposed body, replacing the placeholders:

```markdown
## Execution environment

- Target: `cloud` / `local` / `unknown` (choose one)
- Required inputs: <tracked paths, reproducible setup, services, or local resources>
- Verification: <how the acceptance criteria are checked, including environment prerequisites>
- Reason: <why this target is supported, or what needs checking>
```

Use repository-relative paths where possible. Describe sensitive files by their
purpose or safe path pattern; never paste secrets or private file contents into a
ticket. For `unknown`, name the missing evidence and how to establish it.

`tracker.execution_environment.labels` optionally maps the target values to
tracker label names. The mapped label names must be non-empty and distinct; a malformed mapping
reports a label-discovery gap and uses body-only classification. When the mapping
exists, include the matching label in the
exact proposed payload along with other applicable labels. Resolve labels against
the destination before approval; if a label is unavailable, present a body-only
payload and report that label discovery is degraded. Creating labels requires
separate authorization; a ticket-writing workflow does not create them implicitly.
An absent mapping uses the body section alone. Do not invent label defaults for
an existing adopter, and never add metadata to an already approved payload.

The body explains the classification; labels are an index for backlog discovery.
An absent label can use a valid body section. Conflicting environment labels,
conflicting body/label values, malformed sections, or a known requirement that
contradicts the target render `unknown` with the reason. A label alone is a
provisional hint until the ticket body and prerequisites are checked before
recommendation. A metadata correction is an ordinary tracker update under the
same approval policy as other updates. Existing tickets are not bulk edited by
`session-start`.

## Read in session-start and parallel planning

Establish the current execution environment from explicit invocation context or
runtime-provided evidence. An invocation such as `session-start cloud` supplies
that context. If neither establishes it, report `environment unknown`; never infer
cloud or local from an OS name or a pathname. This classification is separate
from the runtime (Codex or Claude) and execution mode (`inline` or `delegate`).

Gather the complete field-limited backlog with labels or equivalent environment
metadata. Keep full bodies out of that list's rendered output. For a candidate
whose label is absent, fetch its body separately and retain the execution section
for classification; use bounded batches when the backend supports them. Keep an
unread or legacy ticket visible as `unknown`, rather than guessing. Before
recommending a labelled candidate, read its body, reconcile its environment
section and acceptance criteria, and check the named prerequisites read-only.
Missing inputs or access mean blocked in this session, even for a `cloud` ticket.
A failed detail read leaves that candidate unknown and reports the source gap.

Apply the same check to handoff, inbox, PR and CI candidates. Follow pointers to
local plans or retained artifacts; do not assume that a tracked handoff makes its
untracked references available. No ticket metadata is needed when the required
inputs can be established directly from those sources.

In a cloud session, recommend only `cloud` candidates whose prerequisites are
available. Keep `local`, `unknown`, and otherwise blocked candidates visible in
an environment-blocked list with their source pointer and the needed resource or
check. Urgency stays visible there; an urgent local task does not become eligible
by being urgent. In a local session, a `local` candidate is eligible only after its
required local inputs are observed. If the session environment itself is unknown,
render conditional choices and request that context in an interactive invocation;
a non-interactive invocation reports the gap and exits without choosing executable
work. If there is no eligible candidate, say so and name the prerequisite that
would enable a candidate, without recommending blocked work as executable.

An operator-named task remains the pick, but when incompatible, report it as
blocked and give its enabling condition. Do not substitute another task or start
an unapproved authoring subset. These reads never upload files, copy private local
state into the cloud, edit tickets, or launch work.
