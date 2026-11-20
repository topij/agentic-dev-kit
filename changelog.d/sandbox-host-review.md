## Trusted Claude reviews on the host

On macOS, configure `review.fallback_panel.host_sandbox.claude_version` and its system-tool `read_paths` and `command_dirs`, and a short `control_root` also declared in `scratch.roots`, then repeat the documented live acceptance probes. Use `panel_prompt.py --launch --trusted-source` from an independent trusted installation for trusted Claude source. Supply `ANTHROPIC_API_KEY` for the model client. Stage each lens and verifier as a self-contained clone in the allocated round using the documented independent-clone recipe, and stage test dependencies there. Verify the staged HEAD and base-to-head diff through the sandbox before review. Use explicit temporary paths within that round.

Keep an absolute `worker_launcher` for external contributions and Codex reviews. A configured worker takes precedence. The host launcher refuses an unprobed Claude version.

Record the reported runtime control directory and retire it through the session cleanup procedure after its processes finish.
