import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path('/Users/topi/Coding/agentic-dev-kit')
OUT = Path(__file__).resolve().parent
assert Path.cwd().resolve() == ROOT
metadata = {'argv': ['make', 'test'], 'cwd': str(ROOT),
            'revision': subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip(),
            'started_at': datetime.now(timezone.utc).isoformat(), 'timeout_seconds': 1800,
            'status_before': subprocess.check_output(['git', 'status', '--short'], text=True)}
with (OUT / 'kit-test.log').open('x') as log:
    result = subprocess.run(['make', 'test'], cwd=ROOT,
                            env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1',
                                 'UV_CACHE_DIR': str(OUT / 'uv-cache')},
                            stdout=log, stderr=subprocess.STDOUT, timeout=1800)
metadata['exit_code'] = result.returncode
metadata['finished_at'] = datetime.now(timezone.utc).isoformat()
(OUT / 'kit-test.json').write_text(json.dumps(metadata, indent=2)+'\n')
print(json.dumps(metadata, indent=2))
print('\n'.join((OUT / 'kit-test.log').read_text().splitlines()[-80:]))
raise SystemExit(result.returncode)
