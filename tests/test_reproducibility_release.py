from pathlib import Path
import importlib.util

import pandas as pd


def _load_script(name: str):
    root = Path(__file__).resolve().parents[1]
    path = root / "scripts" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_release_inventory_classifies_processed_data_as_zenodo(tmp_path):
    script = _load_script("build_reproducibility_release")
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "module.py").write_text("print('ok')\n", encoding="utf-8")
    processed = tmp_path / "data" / "processed" / "dataset"
    processed.mkdir(parents=True)
    (processed / "expression.csv").write_text("cell_id,G1\nc1,1\n", encoding="utf-8")

    inventory = script.build_release_inventory(tmp_path)

    by_path = inventory.set_index("relative_path")
    assert by_path.loc["src/module.py", "release_target"] == "github"
    assert by_path.loc[
        "data/processed/dataset/expression.csv",
        "release_target",
    ] == "zenodo"
    assert len(by_path.loc["data/processed/dataset/expression.csv", "sha256"]) == 64


def test_release_builder_writes_manifests(tmp_path):
    script = _load_script("build_reproducibility_release")
    (tmp_path / "metadata").mkdir()
    (tmp_path / "metadata" / "datasets.tsv").write_text(
        "dataset_id\taccession_or_doi\nx\tGSE1\n",
        encoding="utf-8",
    )
    processed = tmp_path / "data" / "processed" / "dataset"
    processed.mkdir(parents=True)
    (processed / "metadata.csv").write_text("cell_id\nc1\n", encoding="utf-8")

    assert script.main(["--root", str(tmp_path), "--output-dir", str(tmp_path / "release")]) == 0

    github = pd.read_csv(tmp_path / "release" / "github_release_manifest.tsv", sep="\t")
    zenodo = pd.read_csv(tmp_path / "release" / "zenodo_upload_manifest.tsv", sep="\t")
    assert "metadata/datasets.tsv" in set(github["relative_path"])
    assert "data/processed/dataset/metadata.csv" in set(zenodo["relative_path"])
    assert (tmp_path / "release" / "DATA_AVAILABILITY_STATEMENT_DRAFT.md").exists()
