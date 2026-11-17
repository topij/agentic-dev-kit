"""Run a Claude PR lane in a fresh, unmounted macOS arm64 Lima guest."""

import argparse
import base64
import contextlib
import http.client
import json
import os
import platform
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from urllib.parse import quote, urlsplit

ENGINE = Path(__file__).resolve().parent
sys.path.insert(0, str(ENGINE / "lib"))
from kitconfig import get, load_config, repo_root  # noqa: E402

PERMISSIONS = {"contents": "write", "pull_requests": "write", "metadata": "read"}


def gh(path):
    result = subprocess.check_output(["gh", "api", "--hostname", "github.com", path])
    return json.loads(result)


def protected_head(repo, base):
    """Require an effective repository update rule bypassable only by the operator via PR."""
    operator = gh("user")["id"]
    route = f"repos/{repo}"
    ref = quote(base, safe="")
    for rule in gh(f"{route}/rules/branches/{ref}"):
        if (rule["type"], rule.get("ruleset_source_type"), rule.get("ruleset_source")) != (
            "update",
            "Repository",
            repo,
        ):
            continue
        detail = gh(f"{route}/rulesets/{int(rule['ruleset_id'])}")
        actors = detail.get("bypass_actors")
        if (
            detail["enforcement"] == "active"
            and any(item["type"] == "update" for item in detail["rules"])
            and actors
            == [{"actor_type": "User", "actor_id": operator, "bypass_mode": "pull_request"}]
        ):
            return gh(f"{route}/branches/{ref}")["commit"]["sha"]
    raise ValueError("the configured base needs an active operator-only pull-request update rule")


def api(method, path, token, data=None):
    # A fixed HTTPS origin and no redirects keep both JWT and installation token on GitHub.
    with contextlib.closing(http.client.HTTPSConnection("api.github.com", timeout=30)) as conn:
        conn.request(
            method,
            "/" + path,
            None if data is None else json.dumps(data),
            {
                "Authorization": "Bearer " + token,
                "User-Agent": "devkit-isolated-lane",
                "Content-Type": "application/json",
                "Accept": "application/vnd.github+json",
            },
        )
        response = conn.getresponse()
        if response.status not in (200, 201, 204):
            raise ValueError(f"GitHub {method} {path} returned HTTP {response.status}")
        return json.loads(response.read()) if response.status != 204 else None


def b64(data):
    return base64.urlsafe_b64encode(data).rstrip(b"=")


@contextlib.contextmanager
def installation_token(repo, app_id, key):
    now = int(time.time())
    claims = {"iss": str(app_id), "iat": now - 60, "exp": now + 480}
    body = b64(b'{"alg":"RS256","typ":"JWT"}') + b"." + b64(json.dumps(claims).encode())
    signature = subprocess.check_output(
        ["openssl", "dgst", "-sha256", "-sign", str(key)], input=body
    )
    jwt = (body + b"." + b64(signature)).decode()
    installation = api("GET", f"repos/{repo}/installation", jwt)
    if installation["app_id"] != app_id or installation.get("suspended_at"):
        raise ValueError("expected an active installation of the specified App on the target")
    repo_id = gh(f"repos/{repo}")["id"]
    grant = api(
        "POST",
        f"app/installations/{installation['id']}/access_tokens",
        jwt,
        {"repository_ids": [repo_id], "permissions": PERMISSIONS},
    )
    token = grant["token"]
    try:
        scope = api("GET", "installation/repositories?per_page=2", token)
        if (
            grant["permissions"] != PERMISSIONS
            or scope["total_count"] != 1
            or [r["id"] for r in scope["repositories"]] != [repo_id]
        ):
            raise ValueError("installation token scope differs from the requested grant")
        yield token, installation["app_slug"] + "[bot]"
    finally:
        api("DELETE", "installation/token", token)


def run_isolated(args):
    root = repo_root(ENGINE)
    cfg = load_config(root / "config/dev-model.yaml")
    base = get(cfg, "vcs.protected_branch")
    prefix = get(cfg, "vcs.dev_branch_prefix")
    image = get(cfg, "parallel.isolated_image_url", "")
    digest = get(cfg, "parallel.isolated_image_sha512", "")
    if platform.system() != "Darwin" or platform.machine() != "arm64":
        raise ValueError("isolated requires a macOS arm64 host with Lima")
    if urlsplit(image).scheme != "https" or not re.fullmatch(r"[a-fA-F0-9]{128}", digest):
        raise ValueError("configure parallel.isolated_image_url and isolated_image_sha512")
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", args.scope):
        raise ValueError("scope must be a lowercase slug")
    origin = subprocess.check_output(
        ["git", "-C", root, "remote", "get-url", "origin"], text=True
    ).strip()
    match = re.fullmatch(
        r"(?:https://github\.com/|git@github\.com:)([\w.-]+/[\w.-]+?)(?:\.git)?", origin
    )
    if not match:
        raise ValueError("isolated requires a github.com origin")
    repo = match[1]
    head = protected_head(repo, base)
    branch = f"{prefix}/{args.scope}"
    refs = gh(f"repos/{repo}/git/matching-refs/heads/" + quote(branch, safe=""))
    if any(item["ref"] == "refs/heads/" + branch for item in refs):
        raise ValueError("lane branch already exists on the target")
    prompt = args.prompt_file.read_text()
    provision = args.provision.read_bytes() if args.provision else None
    vm = {
        "vmType": "vz",
        "arch": "aarch64",
        "plain": True,
        "mounts": [],
        "propagateProxyEnv": False,
        "ssh": {"loadDotSSHPubKeys": False, "forwardAgent": False, "overVsock": False},
        "images": [{"location": image, "arch": "aarch64", "digest": "sha512:" + digest.lower()}],
    }
    # A private LIMA_HOME also excludes the user's Lima overrides and prevents
    # reuse or deletion of a pre-existing instance. Keep failures for recovery.
    work = Path(tempfile.mkdtemp(prefix="devkit-vm-", dir="/tmp")).resolve()
    ctl_env = {
        "HOME": str(Path.home()),
        "PATH": "/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin",
        "LIMA_HOME": str(work / "l"),
    }

    def lima(*argv, **kw):
        return subprocess.run(
            ["limactl", "--tty=false", *argv], env=ctl_env, cwd=work, check=True, **kw
        )

    try:
        template = work / "lane.yaml"
        template.write_text(json.dumps(vm))
        lima("start", "--name=v", str(template))
        shell = ("shell", "--workdir=/tmp", "v")
        if provision is not None:
            lima(*shell, "/bin/bash", "-se", input=provision)
        if head != protected_head(repo, base):
            raise ValueError("protected base moved during guest preparation")
        with installation_token(repo, args.app_id, args.app_key) as (token, bot):
            payload = {
                "repo": repo,
                "base": base,
                "head": head,
                "scope": args.scope,
                "token": token,
                "engines": str(ENGINE.relative_to(root)),
                "prompt": prompt,
                "bot": bot,
                "model_key": os.environ.get("DEVKIT_LANE_ANTHROPIC_API_KEY"),
            }
            # Discard guest-controlled output; even diagnostics can echo a credential.
            guest = (ENGINE / "lib/isolated_guest.py").read_text()
            result = lima(
                *shell,
                "python3",
                "-I",
                "-c",
                guest,
                input=json.dumps(payload).encode(),
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
            )
            guest_head = result.stdout.strip()
            if not re.fullmatch(rb"[0-9a-f]{40}", guest_head):
                raise ValueError("guest did not return a Git commit ID")
        prs = gh(
            f"repos/{repo}/pulls?state=open&base={quote(base, safe='')}&head="
            + quote(repo.split("/")[0] + ":" + branch, safe="")
        )
        if (
            len(prs) != 1
            or prs[0]["user"]["login"] != bot
            or prs[0]["head"]["sha"] != guest_head.decode()
            or prs[0]["draft"]
            or prs[0]["head"]["repo"]["full_name"] != repo
            or prs[0]["head"]["ref"] != branch
            or prs[0]["base"]["repo"]["full_name"] != repo
            or prs[0]["base"]["ref"] != base
        ):
            raise ValueError("the expected open App-authored PR was not found")
        print(json.dumps({"url": prs[0]["html_url"], "head": prs[0]["head"]["sha"], "author": bot}))
    finally:
        # Print the location before stop/delete too, in case Lima cannot finish either.
        print(f"Pilot VM location: LIMA_HOME={work / 'l'}", file=sys.stderr)
        if (work / "l/v").is_dir():
            lima("stop", "v")
    lima("delete", "v")
    shutil.rmtree(work)


def main():
    def terminate(signum, frame):
        raise SystemExit(128 + signum)

    signal.signal(signal.SIGTERM, terminate)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("scope")
    parser.add_argument("--app-id", type=int, required=True)
    parser.add_argument("--app-key", type=Path, required=True)
    parser.add_argument("--prompt-file", type=Path, required=True)
    parser.add_argument(
        "--provision",
        type=Path,
        help="operator-owned guest setup script, run before token issuance",
    )
    try:
        run_isolated(parser.parse_args())
    except (
        KeyError,
        ValueError,
        OSError,
        subprocess.SubprocessError,
        http.client.HTTPException,
    ) as exc:
        print(f"isolated lane: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
