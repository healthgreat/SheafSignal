# Environment Lock Report

Decision: `ENVIRONMENT_LOCK_PASS`

- Python version: 3.11.5
- Python executable: `D:\BioSoft\python\Python311\python.exe`
- Locked requirements: 216
- Core locked requirements: 12
- Lock warnings: 0

## Artifacts

- `envs/requirements-py311-lock.txt`
- `envs/requirements-core-lock.txt`
- `envs/environment_lock_audit.tsv`
- `envs/environment_lock_summary.tsv`

## Boundary

This lock records the local Python environment used for the hardening run.
It complements the broader conda YAML files, which remain convenience
environment definitions. Final public release should use this lock or a
container built from it for clean-clone reproduction.
