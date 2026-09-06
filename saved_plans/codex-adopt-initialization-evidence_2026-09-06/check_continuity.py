import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

KIT = Path('/Users/topi/Coding/agentic-dev-kit')
REPO = Path('/private/tmp/adk-adopt-field-20260905-5mfj1st8/fixture')
EVIDENCE = KIT / 'saved_plans/codex-adopt-field-evidence_2026-09-05'
SOURCE = 'ab0a6d62308b298478b2f85fc961f14348f35365'


def git(*args):
    return subprocess.check_output(['git', '-C', str(REPO), *args], text=True).strip()


def digest(path):
    assert path.is_file() and not path.is_symlink(), path
    return hashlib.sha256(path.read_bytes()).hexdigest()


assert Path.cwd().resolve() == KIT
assert REPO.resolve() == REPO
assert git('rev-parse', 'HEAD') == '08ac687f4ae14218a3861c6b8b143d8b86c4e3c2'
assert git('symbolic-ref', '--short', 'HEAD') == 'chore/adopt-agentic-dev-kit'
assert not git('remote', '-v')
checks = {}
for row in json.loads((EVIDENCE / 'copy-ledger.json').read_text()):
    if row['action'] == 'copied':
        checks[row['destination']] = digest(REPO / row['destination']) == row['sha256']
for target, retained in [('config/dev-model.yaml', 'staged-config.yaml'),
                         ('kit-manifest.json', 'install-baseline.json')]:
    checks[target] = (REPO / target).read_bytes() == (EVIDENCE / retained).read_bytes()
for rel, original in json.loads((EVIDENCE / 'fixture-inputs.json').read_text()).items():
    if rel != 'config/dev-model.yaml':
        checks[rel] = (REPO / rel).read_text() == original
assert all(checks.values()), [path for path, ok in checks.items() if not ok]
assert json.loads((REPO / 'kit-manifest.json').read_text())['kit_commit'] == SOURCE
assert (REPO / 'init.sh').read_bytes() == subprocess.check_output(
    ['git', '-C', str(KIT), 'show', SOURCE + ':init.sh'])
absent = ['notes/friction.md', 'notes/friction-archive.md',
          '.git/hooks/pre-push', '.claude/settings.json', '.codex/hooks.json']
for rel in absent:
    assert not (REPO / rel).exists() and not (REPO / rel).is_symlink(), rel
print(json.dumps({
    'command': 'PYTHONDONTWRITEBYTECODE=1 python3 /private/tmp/adk-adopt-continuation-20260906-AFeElK/check_continuity.py',
    'cwd': str(KIT),
    'date': datetime.now(timezone.utc).isoformat(),
    'kit_revision': subprocess.check_output(['git', '-C', str(KIT), 'rev-parse', 'HEAD'], text=True).strip(),
    'fixture': str(REPO), 'fixture_revision': git('rev-parse', 'HEAD'),
    'installed_source': SOURCE, 'checks': checks, 'absent': absent,
    'result': 'retained staging matches; initialization remains pending',
}, indent=2))
