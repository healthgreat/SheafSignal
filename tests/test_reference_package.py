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


def test_reference_table_contains_core_verified_methods():
    script = _load_script("build_reference_package")
    table = script.build_reference_table()

    keys = set(table["citation_key"])
    assert "cellchat_jin_2021" in keys
    assert "cellphonedb_efremova_2020" in keys
    assert "nichenet_browaeys_2020" in keys
    assert "liana_plus_dimitrov_2024" in keys
    assert "hodge_rank_jiang_2011" in keys
    assert table["doi"].str.startswith("10.").all()


def test_placeholder_replacement_resolves_manuscript_refs():
    script = _load_script("build_reference_package")
    text = "Tools include [REF: CellChat], [REF: NicheNet] and [REF: cellular sheaves]."
    replaced = script.replace_placeholders(text, script.build_placeholder_map())

    assert "[REF:" not in replaced
    assert "@cellchat_jin_2021" in replaced
    assert "@nichenet_browaeys_2020" in replaced
    assert "@cellular_sheaves_hansen_2019" in replaced


def test_reference_package_writes_expected_files(tmp_path):
    script = _load_script("build_reference_package")
    manuscript = tmp_path / "SCI_MANUSCRIPT_V1.md"
    manuscript.write_text(
        "Cell-cell communication [REF: CellChat], [REF: CellPhoneDB], [REF: LIANA].\n",
        encoding="utf-8",
    )
    out_dir = tmp_path / "references"

    exit_code = script.main(
        [
            "--output-dir",
            str(out_dir),
            "--manuscript",
            str(manuscript),
        ]
    )

    assert exit_code == 0
    expected = set(script.OUTPUT_FILES.values())
    observed = {path.name for path in out_dir.iterdir()}
    assert expected.issubset(observed)
    referenced = (out_dir / "SCI_MANUSCRIPT_V1_referenced.md").read_text(encoding="utf-8")
    assert "[REF:" not in referenced
    gaps = (out_dir / "SCI_REFERENCE_GAP_REPORT.md").read_text(encoding="utf-8")
    assert "REFERENCE_PLACEHOLDERS_RESOLVED" in gaps
    refs = pd.read_csv(out_dir / "SCI_REFERENCES_VERIFIED.tsv", sep="\t")
    assert "source_url" in refs.columns
