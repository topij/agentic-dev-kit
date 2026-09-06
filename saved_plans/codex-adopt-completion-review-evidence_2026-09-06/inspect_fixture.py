import difflib
import hashlib
import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path('/Users/topi/Coding/agentic-dev-kit')
FIXTURE = Path('/private/tmp/adk-adopt-field-20260905-5mfj1st8/fixture')
SOURCE = Path('/private/tmp/adk-adopt-continuation-20260906-AFeElK/kit-source')
OUT = Path(__file__).resolve().parent
SOURCE_SHA = 'ab0a6d62308b298478b2f85fc961f14348f35365'
BASE = '08ac687f4ae14218a3861c6b8b143d8b86c4e3c2'
EVIDENCE = ROOT / 'saved_plans/codex-adopt-initialization-evidence_2026-09-06'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def run(argv, cwd=FIXTURE):
    p = subprocess.run(argv, cwd=cwd, env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1',
                       'GIT_OPTIONAL_LOCKS': '0'}, capture_output=True, text=True, timeout=60)
    return {'argv': argv, 'cwd': str(cwd), 'exit_code': p.returncode,
            'stdout': p.stdout, 'stderr': p.stderr}


def git(root, *args):
    result = run(['git', '-C', str(root), *args], ROOT)
    assert result['exit_code'] == 0, result
    return result['stdout'].strip()


def snapshot():
    paths = [p for p in FIXTURE.rglob('*') if '.git' not in p.relative_to(FIXTURE).parts]
    paths += [FIXTURE / '.git/config', FIXTURE / '.git/hooks/pre-push']
    return {str(p.relative_to(FIXTURE)): sha(p.read_bytes()) for p in sorted(paths) if p.is_file()}


assert Path.cwd().resolve() == ROOT
assert git(FIXTURE, 'rev-parse', 'HEAD') == BASE
assert git(FIXTURE, 'symbolic-ref', '--short', 'HEAD') == 'chore/adopt-agentic-dev-kit'
assert git(FIXTURE, 'remote', '-v') == ''
assert git(SOURCE, 'rev-parse', 'HEAD') == SOURCE_SHA
before = snapshot()
for rel, digest in json.loads((EVIDENCE / 'sha256.json').read_text()).items():
    assert sha((EVIDENCE / rel).read_bytes()) == digest, rel
assert (FIXTURE / 'config/dev-model.yaml').read_bytes() == (EVIDENCE / 'config-after-init.yaml').read_bytes()
old = ROOT / 'saved_plans/codex-adopt-field-evidence_2026-09-05'
assert (FIXTURE / 'kit-manifest.json').read_bytes() == (old / 'install-baseline.json').read_bytes()
for row in json.loads((old / 'copy-ledger.json').read_text()):
    if row['action'] == 'copied':
        assert sha((FIXTURE / row['destination']).read_bytes()) == row['sha256'], row
for rel, original in json.loads((old / 'fixture-inputs.json').read_text()).items():
    if rel not in ('config/dev-model.yaml', '.gitignore'):
        assert (FIXTURE / rel).read_text() == original, rel

doctor = run(['python3', str(FIXTURE / 'scripts/devkit/kit_doctor.py'), '--root', str(FIXTURE),
              '--manifest', str(SOURCE / 'kit-manifest.json')])
assert doctor['exit_code'] == 0, doctor
renders = {}
patches = []
agents = (FIXTURE / 'AGENTS.md').read_text()
assert agents == '<!-- devkit-source: kit-own -->\n# Fixture policy\nPreserve this fixture-specific policy.\n'
patches.extend(difflib.unified_diff(agents.splitlines(True), agents.splitlines(True)[1:],
                                  fromfile='a/AGENTS.md', tofile='b/AGENTS.md'))
for lens in ('adversarial', 'correctness'):
    rel = f'.claude/agents/{lens}.md'
    renders[lens] = run(['python3', str(FIXTURE / 'scripts/devkit/panel_prompt.py'),
                         '--root', str(FIXTURE), '--lens', lens, '--agent-definition'])
    assert renders[lens]['exit_code'] == 0, renders[lens]
    patches.extend(difflib.unified_diff((FIXTURE / rel).read_text().splitlines(True),
                   renders[lens]['stdout'].splitlines(True), fromfile='a/'+rel, tofile='b/'+rel))

raw = json.loads((EVIDENCE / 'fixture-verification-output.json').read_text())
assert sha(raw['output'].encode()) == raw['output_sha256']
failed = [line[7:].split(' - ', 1)[0] for line in raw['output'].splitlines() if line.startswith('FAILED ')]
assert failed and len(failed) == len(set(failed))
after = snapshot()
assert before == after, [p for p in before.keys() | after.keys() if before.get(p) != after.get(p)]
report = {'argv': ['python3', str(Path(__file__).resolve())], 'cwd': str(ROOT),
          'observed_at': datetime.now(timezone.utc).isoformat(), 'kit_revision': git(ROOT, 'rev-parse', 'HEAD'),
          'fixture': str(FIXTURE), 'fixture_revision': BASE, 'installed_source': SOURCE_SHA,
          'continuity': 'retained copy ledger, inputs, post-init config and install baseline matched',
          'fixture_files_before_after_equal': before == after,
          'fixture_snapshot_sha256': sha(json.dumps(before, sort_keys=True).encode()),
          'absent_registration_paths': [p for p in ('.codex/config.toml', '.codex/hooks.json', '.claude/settings.json')
                                        if not (FIXTURE / p).exists()],
          'doctor': doctor, 'lens_renders': renders,
          'failed_node_inventory_source_sha256': sha((EVIDENCE / 'fixture-verification-output.json').read_bytes()),
          'failed_nodes': failed}
assert Path.cwd().resolve() == ROOT
(OUT / 'inspection.json').write_text(json.dumps(report, indent=2) + '\n')
(OUT / 'ownership-and-lenses.patch').write_text(''.join(patches))
print(doctor['stdout'])
print(''.join(patches))
print('Read-only inspection retained at ' + str(OUT / 'inspection.json'))
