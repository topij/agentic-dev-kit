## Runtime adapters with historical descriptions

CHANGED: `kit_doctor.py --adapter-report` can report an unchanged earlier skill
as `kit-stale` using the install manifest's `kit_commit`, even after the kit changes
its description. Provide a source kit checkout containing that commit and its
ancestry. Read the per-path baseline-unavailable detail when history cannot establish
a known render; preserve those adapters for manual reconciliation. Authored changes
and unrecognized historical template bodies remain `adopter-owned`.
