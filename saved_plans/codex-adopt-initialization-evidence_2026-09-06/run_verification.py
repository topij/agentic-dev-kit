import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

OUT = Path('/private/tmp/adk-adopt-continuation-20260906-AFeElK')
FIXTURE = Path('/private/tmp/adk-adopt-field-20260905-5mfj1st8/fixture')
KIT = Path('/Users/topi/Coding/agentic-dev-kit')
mode = sys.argv[1]
if mode == 'fixture':
    root = FIXTURE
    argv = ['uv', 'run', '--with', 'pytest', '--with', 'pyyaml', 'python', '-m',
            'pytest', 'scripts/devkit/lib/state_paths/tests/', 'scripts/devkit/tests/', '-q']
elif mode == 'kit':
    root = KIT
    argv = ['make', 'test']
else:
    raise SystemExit('unknown verification mode')
assert Path.cwd().resolve() == root
env = os.environ.copy()
env['PYTHONDONTWRITEBYTECODE'] = '1'
env['UV_CACHE_DIR'] = str(OUT / 'uv-cache')
if mode == 'fixture':
    state = OUT / 'fixture-test-state'
    state.mkdir(exist_ok=False)
    env['DEVKIT_STATE_ROOT'] = str(state)
stamp = {
    'mode': mode, 'cwd': str(root), 'argv': argv,
    'started_at': datetime.now(timezone.utc).isoformat(),
    'revision': subprocess.check_output(['git', '-C', str(root), 'rev-parse', 'HEAD'], text=True).strip(),
    'status_before': subprocess.check_output(['git', '-C', str(root), 'status', '--short'], text=True),
    'env': {k: env[k] for k in ('PYTHONDONTWRITEBYTECODE', 'UV_CACHE_DIR', 'DEVKIT_STATE_ROOT') if k in env},
    'timeout_seconds': 1800,
}
started = time.monotonic()
log = OUT / (mode + '-verification.log')
assert not log.exists()
with log.open('x') as stream:
    try:
        result = subprocess.run(argv, cwd=root, env=env, stdout=stream, stderr=subprocess.STDOUT, timeout=1800)
        stamp['exit_code'] = result.returncode
    except subprocess.TimeoutExpired:
        stamp['timed_out'] = True
stamp['elapsed_seconds'] = time.monotonic() - started
stamp['finished_at'] = datetime.now(timezone.utc).isoformat()
stamp['output_path'] = str(log)
assert Path.cwd().resolve() == root
(OUT / (mode + '-verification.json')).write_text(json.dumps(stamp, indent=2) + '\n')
print(json.dumps(stamp, indent=2), flush=True)
print('\n'.join(log.read_text().splitlines()[-100:]), flush=True)
raise SystemExit(stamp.get('exit_code', 124))
