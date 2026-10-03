# Friction Log — agentic-dev-kit

> **Lean inbox (Principle #2 — the friction flywheel).** Friction surfaced during real use,
> recorded at session end. Single incidents route **down** to the tracker; a genuine
> multi-occurrence **pattern** graduates **up** into a rule or skill change.
>
> **What lands here is what is not yet issue-shaped.** A finding that already carries a
> reproduction, a named mechanism and a proposed fix is filed straight to the tracker by
> `wrap-up`'s friction-routing step, on the operator's go-ahead, rather than parked here
> — and parks here anyway when that route is unavailable — which is the routing Principle #2 prescribes,
> not a neglected inbox. What stays is the remainder: findings still missing one of those
> three, and single instances of a shape that only matters if it recurs.
>
> **Position alone does not tell you what is un-graduated, and this file does not
> pretend otherwise** ([`#224`](https://github.com/topij/agentic-dev-kit/issues/224)).
> New entries are appended at the *top*, so the dated sections above the most recent
> `## … — Backlog migrated` marker are un-graduated. But a sweep does not archive
> everything it passes over: an entry added *between* a triage run's draft and its
> finalize is recognised as new and deliberately **kept in this file, below the new
> marker**, ready for the next pass rather than archived unfiled. So the un-graduated
> set is everything above the newest marker **plus anything kept below it**, and a
> dated section below a marker is that safety mechanism working — not a straggler.
> Each marker's own block records what it swept.
>
> Tracker board: https://github.com/topij/agentic-dev-kit/issues

## 2026-10-04

- **The cockpit changed verification state while claiming an isolated run.** Severity L,
  kept for accumulation. `env -u FORCE_COLOR make test` at
  `8385211ea8ac0051df40d919ff0bd8515f43f8df` on 2026-10-03, in
  `/private/tmp/devkit-validation-integrity`, failed the suite state guard after the
  author polled `pr-watch` concurrently in that checkout. The quiet detached rerun
  supplied the verification evidence instead. The existing state-isolation requirement
  already governs the mistake; this entry proposes no new rule.
- **A public fallback disposition initially contained its local filename.** Severity L,
  kept for accumulation. The author supplied `/private/tmp/devkit-pr937-disposition.md`
  and `/private/tmp/devkit-pr938-parent-disposition.md` as `--disposition` values. That
  argument is literal text; stdin requires `--disposition -`. The author read back the
  public comments, replaced their bodies with the completed reports and verified exact
  read-back. The later composed receipt used stdin. The existing CLI contract already
  supplies the correct route; this entry records the misuse for recurrence.

## 2026-10-03

Parked rather than filed: this wrap-up ran with no operator present, so no tracker
payload could be approved. The first two carried a drafted payload, and were filed afterwards on
the operator's approval, as each one's annotation says.

- **The matrix guard's LOW residue from #923's last delta pass.** Severity L.
  - **Observed** in #923's last delta pass at `f60b530`; its disposition there names the
    lens behind each item.
    `scripts/tests/test_runtime_parity_matrix.py` misses the following:
    - It recognises only backtick fences, so a `~~~` fence holding a `#` line still ends
      a section early, and a rogue row after it goes unchecked. `_slugs` has the same
      gap.
    - It skips these link forms: unquoted or spaced `href`, `img src`, an angle-bracketed
      target containing a space, and reference definitions inside lists or quotes.
    - The `<?` in `LINK` and `REFERENCE`, `HREF`'s IGNORECASE, and the single-quoted
      `href` have no test that fails when they are removed.
  - **Mechanism:** the fence toggles test `startswith("```")` only; the link patterns
    and their controls were written per form.
  - **Proposed fix:** toggle on `~~~` too, in both functions, with a control; add one
    control per pattern branch named; leave the unparsed forms out of the claim, which
    already names the parsed forms only.
  - **Drafted title:** "Matrix guard: tilde fences, unpinned link-pattern branches, and
    the link forms it does not parse". **Filed as #925** on the operator's approval, with an added "Related: #216" line.
- **#919's tracker body does not scope the row audit the records now assign to it.**
  Severity M. The handoff, the exit record and the plan pointer all name #919 as the
  owner of "which matrix rows' claims are true". Read on 2026-10-03, #919's body
  described only item 10, whose acceptance #923 met, so a reader of the issue alone could
  close it.
  **Drafted comment for #919:** "#923 shipped item 10's check and the exit re-run; the
  operator declared the Phase 6 exit under the amendment in
  `saved_plans/phase6-exit-check_2026-10-02.md`. This issue stays open for what that
  amendment leaves unaudited: for each capability-matrix row that cites no stamped live
  record, name the tests that pin its repository side, or record that none does."
  **Posted on #919** on the operator's approval.
- **`make lint` does not see an untracked file, so a lint failure surfaced only after a
  stamp run started.** Severity L. Lint passed on a new, still-untracked test file; after
  it was committed, the `make test` stamp at `7c26636` stopped at ruff B905, and
  the stamp and its mutation runs were restarted. **Mechanism:** the `Makefile`'s lint line feeds
  ruff `git ls-files -z '*.py'`, which lists tracked files only. **Proposed fix:** add
  `--others --exclude-standard` to that listing, or say in `AGENTS.md` that lint covers
  tracked files only.
- **`pr_watch.py`'s verification-stamp parser and `wrap-up.md`'s stamp wording
  disagree.** Severity L. A PR body line reading "at `<sha>`, in `<dir>`, on `<date>`"
  — the directory that `wrap-up.md` asks a verification claim to name — was reported
  as no stamp at that head. **Mechanism:** `_VERIFICATION_STAMP_RE` requires
  `at <sha> on <date>` with nothing between them. **Proposed fix:** accept a clause
  between them in the parser, or have `wrap-up.md` prescribe the order "at `<sha>` on
  `<date>`, in `<dir>`".
- **A negative control anchored on a structural boundary stopped testing anything when
  an unrelated key moved that boundary.** Severity L, kept for accumulation.
  `test_runtime_parity_contract_rejects_a_gap_with_no_real_surface` inserted its entry
  just before the front matter's closing `---`. #923 added keys after
  `workflow_contract`, so the entry landed in another block and the test passed without
  raising, which only the full-suite stamp showed. Repaired in #923 by asserting that
  the insertion landed and matching the assertion's message.
- **The option offered for an operator decision overstated its own premise.** Severity
  M, kept for accumulation. The cockpit offered "the table's rows are confirmed by their
  own live records" as an option, the operator chose it, and #923's correctness lens
  then found rows that cite no stamped record, as #923's disposition at `9f23607`
  records. The operator re-decided on a narrowed
  wording. The shape: a decision option's factual premise was not checked against the
  record before it was offered.
- **#923 is a further occurrence of the shape #838 tracks.** Severity L. The full panel
  and each of the two delta passes found one more unpinned property of the new guard.
  Severity fell every round, and the LOW rule stopped the loop.

## 2026-09-28 — Backlog migrated by triage session 3058c6ec6d0e4c4a9298351d6f8b1aaf

Engine mode: `engine-backed`.

Filed [#844](https://github.com/topij/agentic-dev-kit/issues/844) from TRI-01, the `2026-09-27` entry `Record text written from expectation, not read back.`.

Filed [#845](https://github.com/topij/agentic-dev-kit/issues/845) from TRI-02, the `2026-09-11` entry `The review runtime stopped before delivering required adversarial coverage.`.

Filed [#846](https://github.com/topij/agentic-dev-kit/issues/846) from TRI-03, the `2026-09-09` entry `A review suite encountered undecodable process-list output.`.

Archived without filing: TRI-04, the `2026-08-27` entry `` `claude -p --output-format json` printed more than one JSON value on stdout in three of five cockpit probe invocations at 2.1.247, and one value on a repeat of the same invocation. ``.

Archived without filing: TRI-05, the `2026-08-27` entry `` `panel_prompt.py` produced an empty prompt file and hung until the tool timeout, then rendered in about a second on an identical re-run. ``.

Approval commands: `approve TRI-01 TRI-02 TRI-03`, `archive TRI-04 TRI-05`. Approver: `topij`.
