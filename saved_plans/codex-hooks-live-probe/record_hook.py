#!/usr/bin/env python3
import json
import os
import sys
import time
from pathlib import Path

name = sys.argv[1]
payload = json.load(sys.stdin)
root = Path(os.environ["PROBE_ROOT"])
log = root / "probe.jsonl"


def record(phase: str) -> None:
    row = {
        "name": name,
        "phase": phase,
        "hook_event_name": payload.get("hook_event_name"),
        "source": payload.get("source"),
        "tool_name": payload.get("tool_name"),
        "input_cwd": payload.get("cwd"),
        "process_cwd": os.getcwd(),
    }
    with log.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, sort_keys=True) + "\n")
        handle.flush()


record("start")
if name.endswith("-timeout"):
    time.sleep(3)
    record("finish")
elif name == "ss-visible":
    print("SESSION_PLAIN_VISIBLE")
elif name == "pt-json":
    print(
        json.dumps(
            {
                "systemMessage": "POST_SYSTEM_VISIBLE",
                "hookSpecificOutput": {
                    "hookEventName": "PostToolUse",
                    "additionalContext": "POST_CONTEXT_VISIBLE",
                },
            }
        )
    )
elif name == "pt-plain":
    print("POST_PLAIN_SHOULD_BE_IGNORED")
