# Clean-Clone Reproduction Preflight Report

- Decision: `CLEAN_CLONE_PREFLIGHT_PASS_LOCAL_EXPORT`
- Source root: `E:\4实验数据\10新算法\SheafSignal`
- Git branch: `codex/sheafsignal-hardening-release`
- Git commit: `73cc44d`
- Python executable: `D:\BioSoft\python\Python311\python.exe`
- Commands run: `4`

## Command Results

- `pytest_core_clean_export`: `pass`, returncode `0`, 1.271s
- `cli_demo_clean_export`: `pass`, returncode `0`, 0.757s
- `assert_demo_outputs`: `pass`, returncode `0`, 0.0s
- `release_audit_clean_export`: `pass`, returncode `0`, 21.105s

## Interpretation Boundary

This preflight exports the current Git `HEAD` into a clean temporary directory and runs a lightweight reproduction check from tracked files only. It is stronger than testing the dirty working tree, but it is not a substitute for a final public-GitHub clean clone after the release URL and Zenodo DOI are inserted.
