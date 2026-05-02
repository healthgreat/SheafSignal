#!/usr/bin/env python
"""Insert the public GitHub repository URL into release metadata.

Author: SheafSignal maintainers
Date: 2026-05-03
Purpose: replace GitHub URL placeholders after the public repository exists,
while keeping branch push, tag creation, Zenodo DOI, and clean-clone checks as
separate gates.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


DEFAULT_REPO_URL = "https://github.com/healthgreat/SheafSignal"
SUMMARY_PATH = Path("release/GITHUB_URL_FINALIZATION_SUMMARY.md")


def _write_text_atomic(path: Path, text: str) -> None:
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    tmp_path.write_text(text, encoding="utf-8")
    tmp_path.replace(path)


def validate_github_url(url: str) -> str:
    url = url.strip().rstrip("/")
    if not re.fullmatch(r"https://github\.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", url):
        raise ValueError(f"Invalid GitHub repository URL: {url}")
    return url


def update_citation(path: Path, repo_url: str) -> bool:
    text = path.read_text(encoding="utf-8")
    new_text = re.sub(
        r'repository-code:\s*"https://github\.com/[^"]+"',
        f'repository-code: "{repo_url}"',
        text,
    )
    changed = new_text != text
    if changed:
        _write_text_atomic(path, new_text)
    return changed


def update_pyproject(path: Path, repo_url: str) -> bool:
    text = path.read_text(encoding="utf-8")
    replacements = {
        'Homepage = "https://github.com/TBD/SheafSignal"': f'Homepage = "{repo_url}"',
        'Repository = "https://github.com/TBD/SheafSignal"': f'Repository = "{repo_url}"',
        'Issues = "https://github.com/TBD/SheafSignal/issues"': f'Issues = "{repo_url}/issues"',
    }
    new_text = text
    for old, new in replacements.items():
        new_text = new_text.replace(old, new)
    changed = new_text != text
    if changed:
        _write_text_atomic(path, new_text)
    return changed


def update_zenodo_metadata(path: Path, repo_url: str) -> bool:
    data = json.loads(path.read_text(encoding="utf-8"))
    changed = False
    for item in data.get("related_identifiers", []):
        if item.get("relation") == "isSupplementTo" and "github.com" in str(
            item.get("identifier", "")
        ):
            if item.get("identifier") != repo_url:
                item["identifier"] = repo_url
                changed = True
    if changed:
        _write_text_atomic(path, json.dumps(data, indent=2, ensure_ascii=False) + "\n")
    return changed


def build_summary(repo_url: str, changed_files: list[str]) -> str:
    changed = "\n".join(f"- `{path}`" for path in changed_files) or "- none"
    return f"""# GitHub URL Finalization Summary

Repository URL: {repo_url}

Updated files:

{changed}

## Boundary

This step only replaces repository URL placeholders after the public repository
exists. It does not prove that the branch has been pushed, does not create a
release tag, does not mint a Zenodo DOI, and does not guarantee journal
acceptance.
"""


def finalize_github_url(root: Path, repo_url: str) -> list[str]:
    repo_url = validate_github_url(repo_url)
    changed_files: list[str] = []
    targets = [
        ("CITATION.cff", update_citation),
        ("pyproject.toml", update_pyproject),
        ("release/zenodo_deposition_metadata.json", update_zenodo_metadata),
    ]
    for rel_path, updater in targets:
        path = root / rel_path
        if path.exists() and updater(path, repo_url):
            changed_files.append(rel_path)
    summary = root / SUMMARY_PATH
    _write_text_atomic(summary, build_summary(repo_url, changed_files))
    changed_files.append(str(SUMMARY_PATH))
    return changed_files


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--repo-url", default=DEFAULT_REPO_URL)
    args = parser.parse_args(argv)

    changed = finalize_github_url(Path(args.root).resolve(), args.repo_url)
    print("updated: " + ";".join(changed))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
