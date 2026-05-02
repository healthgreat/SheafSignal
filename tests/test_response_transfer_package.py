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


def _journal_targets() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "priority": 1,
                "journal": "Nature Methods",
                "target_role": "primary_methods_target",
                "current_position": "best_aligned_high_risk_first_submission",
                "do_not_claim": "Do not claim clinical utility or broad superiority.",
            },
            {
                "priority": 3,
                "journal": "Molecular Cancer",
                "target_role": "cancer_application_route",
                "current_position": "possible_after_stronger_cancer_story",
                "do_not_claim": "Do not turn sparse cell types into mechanisms.",
            },
        ]
    )


def _final_blockers() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "blocker_id": "zenodo_doi::dataset_manifest",
                "severity": "blocking",
                "status": "pending",
                "evidence": "gse154778",
                "required_action": "Mint DOI.",
            },
            {
                "blocker_id": "author_metadata::authors",
                "severity": "pending",
                "status": "tbd_by_authors",
                "evidence": "template",
                "required_action": "Fill authors.",
            },
        ]
    )


def test_decision_tree_preserves_no_guarantee_and_blocker_boundaries():
    script = _load_script("build_response_transfer_package")

    text = script.build_decision_tree(_journal_targets(), _final_blockers())

    assert "not a guarantee of journal acceptance" in text
    assert "1 blocking item(s), 1 pending non-blocking item(s)" in text
    assert "Never claim clinical utility" in text
    assert "Never claim broad superiority" in text


def test_transfer_package_contains_conditional_molecular_cancer_route():
    script = _load_script("build_response_transfer_package")

    table = script.build_transfer_package_by_journal(_journal_targets())
    mc = table.loc[table["journal"] == "Molecular Cancer"].iloc[0]

    assert mc["transfer_status"] == "conditional_transfer"
    assert "Myeloid" in mc["evidence_to_emphasize"]
    assert "sparse cell types" in mc["do_not_claim"]


def test_do_not_claim_checklist_blocks_overclaiming():
    script = _load_script("build_response_transfer_package")

    text = script.build_do_not_claim_checklist()

    assert "Guaranteed acceptance" in text
    assert "Clinical utility" in text
    assert "Full pretrained NicheNet" in text
    assert "Comparator analyses show alignment and complementarity" in text


def test_response_transfer_package_writes_expected_files(tmp_path):
    script = _load_script("build_response_transfer_package")
    targets = tmp_path / "targets.tsv"
    blockers = tmp_path / "blockers.tsv"
    _journal_targets().to_csv(targets, sep="\t", index=False)
    _final_blockers().to_csv(blockers, sep="\t", index=False)

    out_dir = tmp_path / "manuscript" / "response_transfer"
    exit_code = script.main(
        [
            "--output-dir",
            str(out_dir),
            "--journal-targets",
            str(targets),
            "--final-blockers",
            str(blockers),
        ]
    )

    assert exit_code == 0
    expected = set(script.OUTPUT_FILES.values())
    observed = {path.name for path in out_dir.iterdir()}
    assert expected.issubset(observed)
    assert not any(path.name.endswith(".tmp") for path in out_dir.iterdir())
    transfer = pd.read_csv(out_dir / "03_transfer_package_by_journal.tsv", sep="\t")
    assert "Nature Methods" in set(transfer["journal"])
