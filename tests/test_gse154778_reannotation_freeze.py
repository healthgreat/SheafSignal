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


def test_freeze_scanpy_reannotation_writes_prepared_inputs(tmp_path):
    script = _load_script("apply_gse154778_scanpy_reannotation")
    expression = tmp_path / "expression.csv"
    pd.DataFrame(
        {
            "cell_id": ["c1", "c2", "c3"],
            "LYZ": [4, 5, 0],
            "EPCAM": [0, 0, 3],
        }
    ).to_csv(expression, index=False)
    annotations = tmp_path / "scanpy_cell_annotations.csv"
    pd.DataFrame(
        {
            "cell_id": ["c1", "c2", "c3"],
            "scanpy_reannotated_cell_type": ["Myeloid", "Myeloid", "Tumor/Epithelial"],
            "sample_id": ["s1", "s2", "s2"],
            "lesion_type": ["Primary", "Metastatic", "Metastatic"],
            "annotation_version": ["scanpy_full_v1"] * 3,
        }
    ).to_csv(annotations, index=False)

    paths = script.freeze_scanpy_reannotation(
        expression_path=expression,
        scanpy_annotations_path=annotations,
        output_dir=tmp_path / "prepared",
    )

    metadata = pd.read_csv(paths["metadata"])
    profiles = pd.read_csv(paths["profiles"])
    summary = pd.read_csv(paths["annotation_summary"])
    assert set(metadata["cell_type"]) == {"Myeloid", "Tumor/Epithelial"}
    assert set(profiles["cell_type"]) == {"Myeloid", "Tumor/Epithelial"}
    assert "n_samples" in summary.columns

