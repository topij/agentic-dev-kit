# Phase 5 D — PHASE5-D-SYSTEMIZE-BOUNDARIES-01 approval packet

**Prepared for approval. Nothing below has been approved or executed.** This packet
turns the D-SYSTEMIZE-BOUNDARIES row of the [D proposal](phase5-d-proposal_2026-09-21.md)
into an executable scope, in the form of
[PHASE5-D-SYSTEMIZE-LIVE-01](phase5-d-systemize-live_2026-09-23.md). It covers the Stage A
rows for cap-triggered omission, batched analysis, competing cache mtimes and hostile
artifact targets ([route ledger](phase5-stage-a-routes_2026-09-18.md)). Everything it
produces is **synthetic evidence, labelled as synthetic**. None of it is a live-window
route. Topi owns scope changes and the acceptance decision on what the evidence covers.

## Grounding reads

All reads below were taken from `/Users/topi/Coding/agentic-dev-kit` on 2026-09-23.

- `gh api repos/topij/agentic-dev-kit/branches/main --jq .commit.sha` printed
  `a6b281a5f6f0a4eafeb789f36bb405d5c62d5aca`. `gh run view 35900905170` (the push run
  for that sha) printed `completed success`.
- The merged config comes from `kitconfig.load_config()`, including the gitignored
  overlay. It declares `systemize.batch_size: 25`, `single_pass_max_prs: 60`,
  `max_findings_prs_per_run: 75`, `pattern_threshold: 2`, `tracker_severity: high`,
  `lookback_days: 7`, and `review.bots: [coderabbit]` with aliases `coderabbitai` and
  `coderabbitai[bot]`. These are the thresholds the corpora cross. None is lowered.
- The artifact rules exercised here live in `scripts/lib/systemize/artifacts.py`
  (`check_targets`, `read_regular`, `locked`, `publish`) and the shared resolver's
  `resolve_read_path` (newer-of-two by mtime; the sandbox wins a tie). The cap, ranking
  and derived batching fields live in `scripts/lib/systemize/normalize.py` (`build`,
  `verify`).
- **What the unit suite already covers, and what it does not.** The
  `scripts/tests/test_systemize_*.py` modules check the cap, the read cascade in both
  directions, and each hostile-target refusal in process against small fixtures. They do
  not run the entry points as subprocesses over a population that crosses the shipped
  thresholds, slice a batched digest, reduce clusters across slices, break the
  equal-mtime tie, or retarget a parent while an engine is running. Those gaps are this
  package's scope.
- The kit ships a fake forge for its own tests: `FAKE_GH` in
  `scripts/tests/test_systemize_support.py`, a stand-in `gh` that serves paged GraphQL
  from a JSON fixture. This package reuses it byte for byte, so it adds no new forge
  double for review.

## Proposed approval: PHASE5-D-SYSTEMIZE-BOUNDARIES-01

**Purpose:** run the real engine entry points as subprocesses, in a new isolated clone at
the shipped configuration, against synthetic corpora and a hostile filesystem fixture.
Retain the evidence the D row names, then stop and present the results. No kit, config,
tracker, friction, notification or forge write is included.

### Decisions bound by this approval

1. **Workspace.** Bind these roots:
   - `D=/private/tmp/adk-phase5-d-systemize-boundaries-20260923`
   - `K="$D/kit"`, a fresh `git clone https://github.com/topij/agentic-dev-kit`,
     detached at `a6b281a5f6f0a4eafeb789f36bb405d5c62d5aca`
   - `S="$D/sandbox"`, the `DEVKIT_STATE_ROOT` for the sandbox cases
   - `O="$D/outside"`, the escape destination and victim files
   - `F="$D/forge"`: the fake `gh`, its fixtures and call logs
   - `E=/Users/topi/Coding/agentic-dev-kit/state/review-evidence/phase5-d-systemize-boundaries-01`

   Refuse if `$D` or `$E` already exists, and never reset or remove either. Copy
   `config/dev-model.local.yaml` into the clone byte for byte and verify it by SHA-256.
   Require the clone's and the control checkout's `config_fingerprint` to be equal.
   Every write uses an absolute path, and `pwd` is asserted before each write sequence.
2. **No real forge is reachable.** Every engine run sets `PATH="$F/bin:$PATH"` and
   `GH_CONFIG_DIR="$D/gh-empty"`, an empty directory, so a real `gh` has no credentials.
   `command -v gh` must print `$F/bin/gh` before each run. `FAKE_GH_LOG` records every
   argv the fake receives. The fake's repository is `synthetic/adk-d-boundaries` and its
   head is a fixed synthetic sha, so each run identity says it is synthetic.
3. **Fake forge provenance.** Import `FAKE_GH` from `$K/scripts/tests/test_systemize_support.py`
   at the bound sha. Write it to `$F/bin/gh` with the same shebang substitution that
   `fake_env` makes, and record its SHA-256. Fixture `page_size` is `50`, so the merged-PR
   read pages as it does against GitHub. The one addition is H11's wrapper (decision 7),
   which calls the unmodified fake.
4. **Mode and window.** Every run uses `--mode test --window-days 7`. Each case has its own
   `--date`, so no two cases share an artifact path. Test mode forbids branch, commit,
   pull-request, friction-log and tracker writes. The optional `[TEST]` notification is
   excluded too.
5. **Corpora.** `$E/gen_corpus.py` is written for this package and generates them
   deterministically. For each corpus it also writes an **independent expectation**:
   - the expected ranked and capped identities;
   - the omitted identities;
   - `findings_pr_count`, `single_pass_recommended`, `n_batches`;
   - the exact slices.

   These values are computed from the corpus specification with the workflow's
   declared ordering (maximum severity, then unaddressed count, then total, then number).
   The generator does not import kit code. Findings come from `coderabbitai`.
   - Their severity labels mix the reviewer forms the table maps (`🔴 Critical`,
     `_🟠 Major_`, `_🟡 Minor_`, `**High Severity**`, `Severity: medium`). One PR carries
     an unmapped `![P2 Badge]`, which must appear in `severity_limitations`.
   - Their addressed states mix resolved, outdated and unresolved threads.
   - Some findings are review-object bodies, which the digest records as `unevidenced`.

   | Corpus | Date | Finding-bearing PRs | Expected |
   |---|---|---|---|
   | B60 | 2026-06-01 | 60 | no cap; single pass; `n_batches` 3 |
   | B61 | 2026-06-02 | 61 | no cap; batched, slices 25/25/11 |
   | B75 | 2026-06-03 | 75 | no cap; batched 25/25/25 |
   | B76 | 2026-06-04 | 76 | cap; one omitted, and ranks 75 and 76 tie on every key but number |
   | M90 | 2026-06-05 | 90, plus noise | cap; 15 omitted; batched 25/25/25 |

   M90's noise PRs are trusted-author findings on PRs outside the window, findings from
   an untrusted login, a trusted discussion comment (context, not a finding), an empty
   review body, and PRs with no reviews. Two PRs are merged before the window but
   updated inside it, so both the `mergedAt` filter and the `updatedAt` early stop are
   exercised. The merged-PR read spans more than one page.
6. **Planted shapes (M90 only)**, for the clustering step:
   - **X:** one mechanism on two PRs in different slices. Reduction must union them into
     one `pattern` cluster.
   - **W:** one mechanism on three PRs inside one slice, also a `pattern`.
   - **Y:** one mechanism on two threads of a single PR. It has one distinct PR, so it is
     not a `pattern`.
   - **Z:** one mechanism on one kept PR and one omitted PR. Only the kept PR is visible,
     so Z must not be reported as a two-PR pattern.
   - **Singles:** a high single (`tracker-approval`), a low single (`friction-log`), and a
     finding citing `AGENTS.md` (`covered`).

   The answer key is written to `$E/answer-key.json`, and its SHA-256 is recorded in
   `$E/SHA256SUMS` before any clustering agent starts. The key never enters an agent's
   prompt.
7. **Hostile targets.** Each case runs on its own date from 2026-07-01, with its planted
   object in place before the engine starts. Each must exit `1` with one stderr line
   naming the check. The planted object, any victim file and `$O` must be byte- and
   inode-identical afterwards, and no artifact may appear anywhere else. Cases checked
   before the forge read must also show zero fake-forge calls.

   | Case | Engine | Planted object | Expected refusal |
   |---|---|---|---|
   | H1 | fetch | cache target is a symlink to a file inside the state root | not a regular file |
   | H2 | fetch | report target is a symlink to `$K/AGENTS.md` | repository control input |
   | H3 | fetch | cache target is a symlink to a file in `$O` | rejected by the resolver (`safe_join` resolves outside its base) |
   | H4 | fetch | the cache directory is a symlink to `$O` | rejected by the resolver, before `check_targets` |
   | H5 | fetch | cache target is hardlinked to a file in `$O` | has 2 links |
   | H6 | fetch | report target is hardlinked to `$K/AGENTS.md` | has 2 links (alias) |
   | H7a | digest | digest target is a FIFO (after a clean fetch for that date) | not a regular file |
   | H7b | fetch | report target is a directory | not a regular file |
   | H8 | fetch | report target committed locally in the clone (`git add -f`), never pushed | tracked by Git |
   | H9 | fetch | digest target is a symlink to the cache target's path | collide through a link |
   | H10 | digest | a valid digest from another run identity sits at the target | different run; preserved |
   | H11 | fetch | the wrapper renames `$S/cache` aside and symlinks it to `$O` while serving the first `PR_reviews` page | parent symlink escaping, at the pre-publish re-check |
   | H12 | fetch | **interposed:** a one-shot wrapper around `os.fsync` performs H11's swap inside `publish`, after the temp write | parent retargeted outside |

   H11 and H12 also record where the lock and temp files end up. Reading the code
   predicts that both are left in the directory that was moved aside. H12 patches the
   engine in process, so it is labelled as interposed evidence rather than an
   unmodified-entry-point run.
8. **Competing caches** (date 2026-06-10). Two raw bundles are created with the same run
   identity but different populations:
   - `P`, with three finding-bearing PRs, from a fetch without a sandbox, which writes
     to `$K/state`;
   - `Q`, with five finding-bearing PRs, from a fetch with `DEVKIT_STATE_ROOT="$S"`.

   Fixed mtimes are then set with `os.utime`, and the sandboxed digest is run three
   times:

   | Case | mtimes | Expected source (`cache_path` in the envelope) | Expected count |
   |---|---|---|---|
   | C1 | Q newer | `$S/cache/…` | 5 |
   | C2 | P newer | `$K/state/cache/…` | 3 |
   | C3 | equal | `$S/cache/…` (sandbox wins a tie) | 5 |

   Each digest must land in `$S`, and `--verify` must agree each time. The `$K/state`
   tree must hash the same before and after all three cases. Each case's digest bytes
   are retained before the next run replaces them, a same-run replacement the engine
   permits.
9. **Clustering (M90 only), blind to the key.**
   - **Slices:** three fresh subagents, one per slice of the validated digest
     (`prs[0:25]`, `prs[25:50]`, `prs[50:75]`). Each gets only its slice inline plus the
     workflow's Step 2 text, and is told to read no files.
   - **Reduction:** a fourth fresh subagent gets only the three slice outputs, Step 2,
     the routing declaration and `pattern_threshold`, and produces the single cluster
     set.
   - **Heartbeat:** `tick --step cluster --slice i/3` runs after each slice agent.
   - **Model:** `systemize.analysis_tier` is `expensive`, which maps to `fable` on
     Claude. The Agent tool exposes a model choice, so the four subagents are requested
     as `fable`. This session's own model is not switched.
   - The reduced set is then compared with the sealed key.
   - **Limit:** this session wrote the corpus and the key, so the clustering is blind
     but not independent of the corpus author. D-FRESH-CONTEXT remains separate.

### Stage 1 — executed on this approval

1. Set up the workspace (decisions 1–3). Record the clone head, the overlay hash, both
   fingerprints, the fake's hash and `command -v gh`.
2. **Baseline:** in `$K`, run
   `uv run --with pytest --with pyyaml pytest -q scripts/tests/test_systemize_*.py`
   with a raised timeout. This is a focused baseline at the bound sha, not `make test`:
   this package changes no kit file.
3. Generate the corpora, the expectations and the answer key, then seal their hashes.
4. For each corpus in decision 5, run:
   - `heartbeat_cli.py start`, then `fetch_merged_prs.py`, then `digest_merged_prs.py`;
   - `digest_merged_prs.py --verify <digest>`, then `heartbeat_cli.py tick --step digest`.

   Compare every digest with its independent expectation field by field. For B60–B76,
   complete the heartbeat after the digest tick.
5. For M90, run the clustering in decision 9. Then write the test-mode report at
   `$K/reports/post-merge-systemize_7d_test_2026-06-05.md`. Its body opens with
   `SYNTHETIC — PHASE5-D-SYSTEMIZE-BOUNDARIES-01` and carries the full cap disclosure
   (all omitted identities), the exact slices, clusters and proposed routes. Nothing is
   written to any route. Then run `heartbeat_cli.py complete --reason complete`.
6. Run the competing-cache cases (decision 8), then the hostile cases (decision 7).
7. For every call, retain in `$E`:
   - argv, exit status, stdout, stderr, timing and the fake-forge call log;
   - before/after `lstat` snapshots and hashes;
   - digests, heartbeat state and the report;
   - `SHA256SUMS`.

   Write `$E/RESULTS.md` with one row per case: expected, observed, and whether they
   match.
8. **Stop and present.** A divergence from an expectation is a **finding**. It is
   recorded but not repaired, and the independent cases continue. Any repair is a
   separate kit-PR decision, and so is filing any finding.

### Excluded

- Any kit code, test, doc or config change, and any PR.
- Any read of the real forge. Every forge read goes to the fake.
- Live mode, notification (including `[TEST]`), tracker and friction writes.
- Lowering a configured threshold.
- D-SYSTEMIZE-RECOVERY's process-kill cutpoints, D-FRESH-CONTEXT and all triage work.
- Any claim that synthetic results establish live-window behaviour.
- Writes to the control checkout outside `$E`.

### Stops

Keep the checkpoint and propose a bounded amendment on any of these:

- `$D` or `$E` already exists;
- the clone head, overlay hash or fingerprint check fails;
- `command -v gh` does not print the fake;
- the fake-forge log shows a call that reached anything but the fake;
- the baseline suite fails;
- **any write outside `$D` and `$E`**, which stops the whole package;
- a needed action outside this scope.

**Approval wording:** "I approve PHASE5-D-SYSTEMIZE-BOUNDARIES-01 Stage 1 as scoped:
synthetic corpora and hostile fixtures run through the real engine entry points in a new
isolated clone at a6b281a with the shipped thresholds and a fake forge, blind subagent
clustering for M90, stopping with results presented; no kit, config, forge, tracker,
friction or notification write."
