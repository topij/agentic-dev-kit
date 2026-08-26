# Codex environment-capable launcher design — 2026-08-26

## Slice boundary

This design selects one supported unattended Codex launcher for the existing
`new --headless` lane descriptor. It does not calibrate models or reasoning effort,
reconcile downstream repositories, change lane merge policy, or define a general
launcher framework.

The product inventory is grounded in the installed client help and the official
OpenAI developer-command reference. The repository contract remains authoritative for
lane identity and safety. Documentation describes a product surface; only the live
isolation record for this slice can establish that the selected client actually ran
with the intended worktree and lane environment.

## Design matrix

| Launch surface | Worktree authority | Environment replacement | Inherited-variable removal | State-root isolation | Process identity | Durable evidence | Authoritative observer | Unavailable / failure outcome |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Native in-session agent dispatch | Prompted path only; the dispatch surface has no child `cwd` field | No child environment field | None | The marker can help only if no inherited explicit root wins | Runtime-owned agent id; no OS child binding | Agent final text only | Agent self-report | Unsupported for unattended state-writing lanes; remain attended or use the selected wrapper |
| Desktop/app task creation | Runtime-selected checkout or app worktree | No complete per-task process environment map on the task surface | None | App-owned worktree isolation, not the descriptor environment contract | App task id, not a descriptor-bound local process | App task transcript | App/runtime | Unsupported for this local descriptor contract |
| Interactive `codex -C <worktree>` | Stable CLI `-C`; operator shell remains the launch authority | Operator shell can assign values | Depends on the operator command | Valid for attended activation | Foreground CLI process | Interactive transcript; no one-shot launch receipt | Operator plus child session | Attended path only; a missing export is an operator-visible activation failure, not an unattended success |
| Stable `codex exec -C <worktree>` invoked directly | Stable CLI `-C` | Inherits the caller environment | None supplied by Codex itself | Unsafe when an inherited explicit lane root outranks the marker | Foreground CLI process, not descriptor-bound | Optional JSONL/final-message output | Codex process self-report | Unsupported directly; it becomes supported only behind the selected kit-owned wrapper |
| **Selected: kit-owned wrapper → stable `codex exec -C <worktree>`** | Wrapper sets the child `cwd`; child independently resolves `cwd` and Git top-level before `exec` | Start from permitted caller environment, remove lane/repository overrides, then assign every descriptor environment key unconditionally | Remove every inherited `DEVKIT_*`; remove `GH_REPO`, Git repository override variables including injected `GIT_CONFIG*`, `PWD`, and `OLDPWD`; set descriptor keys, seed `PWD` from the descriptor, then validate it against the resolved child cwd | Descriptor root must equal the independently read marker and the session state directory; `DEVKIT_STATE_ROOT`, `DEVKIT_ROOT`, and refusal mode must agree | One-shot descriptor id plus an exclusive pipe-bound capability, child PID/parent/session ids, and OS process-start fingerprint when available, observed before `exec`; the launched process group must be absent at terminalization | Canonical descriptor, exclusive attempt record, exclusively reserved empty final path, observed receipt, terminal receipt, and final-message digest | Child wrapper reads Git fetch/push origin identities, marker, persisted lane metadata, filesystem relationships, canonical prompt contract, and its own process identity; parent rechecks the durable receipt, child PID, launch capability, and available live process fingerprint before accepting launch | Any mismatch, stale descriptor, prior attempt, occupied evidence path, missing observation, surviving process group, interrupted child, missing final message, or nonzero child exit is non-success and leaves terminal or partial evidence that blocks reuse |
| Experimental app-server / protocol clients | Protocol can select a thread working directory | Host-process environment can be arranged outside the protocol | Requires a separate host wrapper | Possible but duplicates the selected wrapper and protocol lifecycle | Server plus thread/turn ids | Protocol event stream | Client and server | Not selected: experimental surface and a larger authority chain than this bounded slice needs |
| Codex cloud task | Cloud environment and service checkout | Cloud environment configuration, not the local descriptor map | Not observable from the local lane engine | Does not bind the local worktree marker and state sandbox | Remote task id | Cloud task record | Remote service | Unsupported for a local `new --headless` descriptor |

## Supported contract

The supported unattended Codex mechanism is a kit-owned Python engine that consumes an
on-disk descriptor issued by `dev_session.sh new --headless`, consumes the task prompt
as bytes, and starts the config-selected Codex headless command with `-C` pointing at
the descriptor worktree. The tracked configuration owns the Codex headless command and
descriptor lifetime. The runtime adapter only invokes the shared workflow and names the
runtime-native mechanism. Issue the descriptor with `new --headless --runtime codex`
or `DEVKIT_RUNTIME=codex`; the wrapper refuses a descriptor for another runtime.

The wrapper treats the environment in two classes:

- Every inherited `DEVKIT_*` key is removed. The descriptor then assigns
  `DEVKIT_STATE_ROOT`, `DEVKIT_ROOT`, and
  `DEVKIT_REFUSE_UNSANDBOXED_STATE` unconditionally.
- `GH_REPO`, `GIT_DIR`, `GIT_WORK_TREE`, `GIT_COMMON_DIR`, `GIT_INDEX_FILE`, every
  injected `GIT_CONFIG` / `GIT_CONFIG_*` key, `PWD`, and `OLDPWD` are removed because
  they can redirect repository or worktree observation. `PWD` is seeded from the
  descriptor and must equal the child's independently resolved physical cwd. Other
  permitted process variables remain available.

## Independent observation and evidence chain

`dev_session.sh` issues a canonical descriptor into the session directory and prints
the same bytes. It binds a unique descriptor id, issue/expiry times, canonical
worktree/session/state/repository roots, origin fetch and push identities, scope, branch, base,
merge class, base commit, lane commit, prompt preamble, runtime, and descriptor
environment.

Before `exec`, the child wrapper constructs observations without copying those fields
from the descriptor:

- worktree from resolved `cwd` and `git rev-parse --show-toplevel`;
- repository from Git's common directory and the observed origin fetch and push URLs;
- lane and state root from the worktree/session filesystem relationship and marker;
- branch from Git symbolic-ref and the separately persisted session branch;
- base and merge class from separately persisted session metadata, with base and lane
  commits resolved through Git;
- prompt contract from a fresh `dev_session.sh print-contract` call in the bound
  repository rather than trusting descriptor text;
- process from its PID, parent PID, session id, and OS process-start fingerprint.

The receipt contains separately constructed `request`, `expected`, and `observed`
objects. The request binds the exact descriptor bytes, task bytes, and combined prompt.
The parent accepts the launch only after the observed receipt is durably replaced on
disk and the live child process still has the recorded start fingerprint. A successful
terminal receipt additionally binds the child's exit and final-message bytes.

## Fail-closed outcomes

- Creating the attempt record and reserving an empty final-message path are exclusive.
  A prior, interrupted, or completed attempt or occupied evidence path blocks launch.
- Expiry, descriptor relocation, changed descriptor bytes, a moved base or lane commit,
  or a mismatched worktree/session/repository/branch/base/state relationship refuses
  before Codex starts.
- Caller-supplied identity is never enough: descriptor fields and environment values
  are compared with child-side Git, filesystem, marker, metadata, and process
  observations.
- The parent accepts only the child reached through the current exclusive handshake and
  matching launch capability; when the host exposes a process-start fingerprint it must
  also match. PID reuse cannot satisfy the one-shot capability or previous attempt.
- Signal interruption or a leader exit with live descendants terminates the complete
  child process group: configured grace follows `SIGTERM`, then `SIGKILL`, and the group
  must disappear before terminalization. A hard-killed parent leaves the exclusive
  partial attempt, which blocks silent retry.
- The parent cannot return success until the terminal receipt and final-message digest
  are durable.

## Ownership boundary

The descriptor issuer, Codex launcher, receipt validator, and behavioral tests are
kit-owned engines or test surfaces. The launch and failure policy belongs in
`parallel-headless.md` and the runtime-parity capability row. The Codex skill stays a
thin binding that selects no environment, identity, retry, or evidence policy.
