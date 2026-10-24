# Parallel lanes: verification mutations

Reference for anyone changing `dev_session.sh`, the lane launcher, or the lane identity
chain that [`workflows/parallel.md`](workflows/parallel.md) declares in its *Lane
authority and resume matrix*. A session running the `parallel` workflow does not need
this file; it moved here from that workflow so the workflow carries only what running
a lane needs.

## Semantic mutation matrix

These are the hostile changes the kit verification surfaces must reject. Engine
branches need behavioral mutations; executed launcher instructions without a shipped
launcher need semantic assertions until an integration surface exists. Add that live
launcher mutation with the environment-capable launcher rather than simulating one here.

| Mutation | Required observable result |
| --- | --- |
| inherit cockpit lane/state variables instead of applying descriptor `env` | the supported wrapper removes inherited `DEVKIT_*`, assigns every descriptor key unconditionally, and the live child/receipt must observe only the descriptor environment |
| launch a correct descriptor in another worktree, or let a child echo descriptor identity without observing Git/filesystem/process state | the child-side observer refuses before `exec`; caller-supplied expected fields cannot substitute for Git, marker, persisted metadata, path relationships, and the launch capability |
| reuse an expired, foreign, interrupted, or completed descriptor/process, or return before observations/final text are durable | exclusive attempt creation, descriptor expiry, process-capability handshake, observed receipt, and terminal final-message digest refuse the launch or its success outcome |
| declare a transport the named runtime does not implement (Claude prompt as an argument, Codex final text on stdout, a worktree flag for Claude), or issue a descriptor for a runtime without a configured command | the wrapper refuses before any attempt record exists; the receipt's request binds the runtime and its transports so parent and child cannot resolve different templates |
| return Claude final text that is empty, malformed, partial, duplicated, an array, a non-`result` object, an error result, or an empty `result`; or accept it before the child observation is durably bound | the terminal receipt is `failed` with the reason named, `final_text_sha256` is absent, and the exclusive attempt remains; success requires the bound observation, a clean exit, and exactly one successful result object |
| change the Codex argv order, drop `--cd`, `--output-last-message`, or the `-` argument, or route Codex evidence through stdout while adding Claude | the pinned Codex argv and `last-message-file` route fail their behavioral test; Claude support cannot regress Codex silently |
| drop or alter persisted branch, base, or merge class | merge refuses; reconciliation cannot widen the lane to `held` |
| inherit ambient `GH_REPO`, fail a forge read, or return malformed JSON | the engine stops before rendering or authorizing an empty/clean result |
| return a fork, foreign owner, wrong base, or wrong head branch under the requested head name | row is not eligible to identify or terminalize the lane |
| move the PR head between identity read and act-time review | merge refuses before the forge write and asks for a retry |
| return a held probe for another PR, base, or head, or with blockers / non-convergence | lane remains `open` |
| keep a local, cached remote-tracking, or live origin branch tip newer than the selected merged PR, or move a ref in either direction during its snapshot reads | lane remains `open`; the older PR cannot claim the observed work shipped |
| tear down the session before an operator-held decision | the open PR remains `open`; absent class/state evidence is never reconstructed |
| create worktree content after `rm`'s status probe, or remove a dirty/unlanded lane | the non-force Git removal refuses at act time, the session survives, and unlanded branch work remains recoverable |
