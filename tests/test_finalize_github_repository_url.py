from pathlib import Path
import importlib.util
import json
import sys


def _load_script(name: str):
    root = Path(__file__).resolve().parents[1]
    path = root / "scripts" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def test_validate_github_url_rejects_non_github():
    script = _load_script("finalize_github_repository_url")

    assert script.validate_github_url("https://github.com/healthgreat/SheafSignal/") == (
        "https://github.com/healthgreat/SheafSignal"
    )
    try:
        script.validate_github_url("https://example.com/SheafSignal")
    except ValueError:
        pass
    else:
        raise AssertionError("invalid URL should raise ValueError")


def test_finalize_github_url_updates_metadata(tmp_path):
    script = _load_script("finalize_github_repository_url")
    (tmp_path / "release").mkdir()
    (tmp_path / "CITATION.cff").write_text(
        'repository-code: "https://github.com/TBD/SheafSignal"\n',
        encoding="utf-8",
    )
    (tmp_path / "pyproject.toml").write_text(
        '[project.urls]\n'
        'Homepage = "https://github.com/TBD/SheafSignal"\n'
        'Repository = "https://github.com/TBD/SheafSignal"\n'
        'Issues = "https://github.com/TBD/SheafSignal/issues"\n',
        encoding="utf-8",
    )
    (tmp_path / "release" / "zenodo_deposition_metadata.json").write_text(
        json.dumps(
            {
                "related_identifiers": [
                    {
                        "identifier": "https://github.com/TBD/SheafSignal",
                        "relation": "isSupplementTo",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    changed = script.finalize_github_url(
        tmp_path, "https://github.com/healthgreat/SheafSignal"
    )

    assert "CITATION.cff" in changed
    assert "pyproject.toml" in changed
    assert "release/zenodo_deposition_metadata.json" in changed
    assert "github.com/TBD" not in (tmp_path / "CITATION.cff").read_text(
        encoding="utf-8"
    )
    assert "healthgreat/SheafSignal/issues" in (tmp_path / "pyproject.toml").read_text(
        encoding="utf-8"
    )
