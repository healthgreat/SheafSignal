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


def test_journal_target_table_keeps_nature_methods_primary():
    script = _load_script("build_journal_target_board")
    table = script.build_journal_table()
    primary = table.sort_values("priority").iloc[0]

    assert primary["journal"] == "Nature Methods"
    assert primary["target_role"] == "primary_methods_target"
    assert primary["fit_score_1_to_5"] == 5
    assert not bool(primary["can_guarantee_acceptance"])
    assert table["jif_2024"].between(20, 50).all()


def test_journal_action_board_contains_claim_boundaries():
    script = _load_script("build_journal_target_board")
    table = script.build_journal_table()
    board = script.build_action_board(table)

    assert "does not guarantee acceptance" in board
    assert "project-curated TME prior matrix" in board
    assert "sparse cell types remain supplement/QC only" in board
    assert "Nature Methods" in board


def test_journal_target_script_writes_table_and_board(tmp_path):
    script = _load_script("build_journal_target_board")
    table_out = tmp_path / "manuscript" / "JOURNAL_TARGETS_20_50.tsv"
    board_out = tmp_path / "manuscript" / "SCI20_50_ACTION_BOARD.md"

    assert script.main(["--table-out", str(table_out), "--board-out", str(board_out)]) == 0
    table = pd.read_csv(table_out, sep="\t")
    assert "metric_source_url" in table.columns
    assert table.loc[0, "journal"] == "Nature Methods"
    assert board_out.exists()
    assert not board_out.with_suffix(board_out.suffix + ".tmp").exists()
