# Public Clean-Clone Reproduction Report

- Decision: `PUBLIC_CLEAN_CLONE_PASS`
- Source: `https://github.com/healthgreat/SheafSignal`
- Ref: `v0.1.0`
- Commit: `766ec1e6215ebfc92e18f81e6e82a4da73422a56`
- Clone path: `D:\BioSoft\tmp\sheafsignal_public_clean_clone_final`
- Generated: `2026-05-04 03:14:11 +08:00`

## Command Summary

- `git clone --branch v0.1.0 --depth 1`: returncode `0`.
- `python -m pytest -q`: returncode `0`; `305 passed, 1 warning`.
- `ruff check scripts tests`: returncode `0`; `All checks passed!`.
- `python scripts/release_audit.py`: returncode `0`; release audit passed.
- `python scripts/check_release_metadata_placeholders.py`: returncode `0`; `RELEASE_METADATA_PLACEHOLDERS_CLEAR`.
- `python scripts/check_final_submission_blockers.py --report-only`: returncode `0`; GO/NO-GO report regenerated.

## Boundary

This report verifies that the public GitHub tag can be cloned and the local test/audit suite can run from that clone. It does not guarantee journal acceptance or validate biological causality.

