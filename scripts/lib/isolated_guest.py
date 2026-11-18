"""Guest half of dev_session.sh isolated. Its output is the local PR head."""

import json
import pathlib
import subprocess
import sys
import tempfile


def main():
    p = json.load(sys.stdin)
    home = pathlib.Path(tempfile.mkdtemp(dir=pathlib.Path.home()))
    env = dict(
        HOME=str(home),
        PATH="/usr/local/bin:/usr/bin:/bin",
        LANG="C.UTF-8",
        GH_TOKEN=p["token"],
        GH_PROMPT_DISABLED="1",
        GIT_TERMINAL_PROMPT="0",
    )
    if p["model_key"]:
        env["ANTHROPIC_API_KEY"] = p["model_key"]

    def run(args, **kw):
        if "capture_output" not in kw:
            kw.setdefault("stdout", subprocess.DEVNULL)
        return subprocess.run(args, env=env, check=True, **kw)

    run(["gh", "auth", "setup-git", "--hostname", "github.com"])
    run(["git", "config", "--global", "user.name", p["bot"]])
    run(["git", "config", "--global", "user.email", p["bot"] + "@users.noreply.github.com"])
    issuer = home / "issuer"
    run(
        [
            "git",
            "clone",
            "--single-branch",
            "--branch",
            p["base"],
            "--",
            "https://github.com/" + p["repo"] + ".git",
            str(issuer),
        ]
    )
    if (
        run(["git", "-C", issuer, "rev-parse", "HEAD"], capture_output=True).stdout.decode().strip()
        != p["head"]
    ):
        sys.exit("protected base moved before clone")
    engines = issuer / p["engines"]
    descriptor = json.loads(
        run(
            [
                engines / "dev_session.sh",
                "new",
                p["scope"],
                "--headless",
                "--base",
                p["base"],
                "--branch",
                p["branch"],
                "--runtime",
                "claude",
                "--merge-class",
                "operator",
            ],
            cwd=issuer,
            stdout=subprocess.PIPE,
        ).stdout
    )
    if descriptor["base_oid"] != p["head"] or descriptor["merge_class"] != "operator":
        sys.exit("issued descriptor differs from protected base or merge class")
    prompt = home / "task.txt"
    prompt.write_text(p["prompt"])
    run(
        [
            "python3",
            "-I",
            engines / "launch_lane.py",
            "--descriptor",
            descriptor["descriptor_path"],
            "--prompt-file",
            prompt,
        ],
        cwd=issuer,
    )
    lane = pathlib.Path(descriptor["worktree"])
    state = pathlib.Path(descriptor["session_dir"])
    receipt = json.loads(
        (state / ("launch-receipt-" + descriptor["descriptor_id"] + ".json")).read_bytes()
    )
    if receipt["terminal"]["lane_state"]["state"] != "pr-ready":
        sys.exit("lane did not report a ready PR")
    status = run(
        ["git", "-C", lane, "status", "--porcelain", "--untracked-files=all"], capture_output=True
    )
    if status.stdout:
        sys.exit("lane still has local changes")
    head = (
        run(["git", "-C", lane, "rev-parse", "HEAD"], capture_output=True).stdout.decode().strip()
    )
    print(head)


if __name__ == "__main__":
    main()
