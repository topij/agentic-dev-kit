import datetime
import json
import os
import subprocess
from pathlib import Path

root=Path(__file__).parent
nodes=["test_panel_prompt.py::test_the_committed_lens_definitions_are_what_the_generator_renders","test_kit_doctor.py::test_shipped_runtime_adapters_equal_the_renderer_for_both_runtimes","test_kitconfig.py::test_shipped_skeletons_carry_the_unrendered_marker[handoff.md]"]
env={**os.environ,"PYTHONDONTWRITEBYTECODE":"1","UV_OFFLINE":"1","UV_CACHE_DIR":str(root/"uv-cache-seeded"),"UV_PYTHON":"/Users/topi/.local/share/uv/python/cpython-3.14.7-macos-aarch64-none/bin/python3.14"}
for directory,prefix in (("source-copy","scripts/tests/"),("fixture-copy","scripts/devkit/tests/")):
 argv=["uv","run","--with","pytest","--with","pyyaml","python","-m","pytest","--basetemp",str(root/(directory+"-basetemp")),"-q"]+[prefix+n for n in nodes]
 p=subprocess.run(argv,cwd=root/directory,env={**env,"DEVKIT_STATE_ROOT":str(root/(directory+"-state"))},text=True,capture_output=True,timeout=120)
 result={"argv":argv,"cwd":str(root/directory),"source":"ab0a6d62308b298478b2f85fc961f14348f35365","fixture_baseline":"08ac687f4ae14218a3861c6b8b143d8b86c4e3c2","date":datetime.datetime.now(datetime.timezone.utc).isoformat(),"exit_code":p.returncode,"stdout":p.stdout,"stderr":p.stderr}
 (root/(directory+"-diagnoses.json")).write_text(json.dumps(result,indent=2))
 print(directory+": "+str(p.returncode))
 print("\n".join(p.stdout.splitlines()[-10:]))
