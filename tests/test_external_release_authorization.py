from pathlib import Path
import importlib.util
import sys


def _load_script(name: str):
    root = Path(__file__).resolve().parents[1]
    path = root / "scripts" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def test_classify_missing_github_token_file_is_blocking(tmp_path):
    script = _load_script("check_external_release_authorization")

    row = script.classify_token_file(tmp_path / "missing_token.txt", "github")

    assert row.check_id == "github_token_file"
    assert row.status == "missing"
    assert row.severity == "blocking"


def test_classify_present_token_file_does_not_expose_content(tmp_path):
    script = _load_script("check_external_release_authorization")
    token_path = tmp_path / "github_token.txt"
    token_path.write_text("ghp_secret_token_value\n", encoding="utf-8")

    row = script.classify_token_file(token_path, "github")

    assert row.status == "present"
    assert "ghp_secret_token_value" not in row.evidence
    assert "Token content was not printed" in row.evidence


def test_authorization_report_keeps_acceptance_boundary():
    script = _load_script("check_external_release_authorization")
    rows = [
        script.AuthCheckRow(
            check_id="github_token_api",
            severity="blocking",
            status="invalid_or_unauthorized",
            evidence="GitHub API returned HTTP 401.",
            required_action="Regenerate token.",
            validation_command="python scripts/check_external_release_authorization.py",
        )
    ]

    report = script.build_report(rows)

    assert "EXTERNAL_RELEASE_AUTHORIZATION_BLOCKED" in report
    assert "guarantee journal acceptance" in report


def test_write_authorization_outputs(tmp_path):
    script = _load_script("check_external_release_authorization")
    rows = [
        script.AuthCheckRow(
            check_id="github_cli_binary",
            severity="pass",
            status="present",
            evidence="gh version test",
            required_action="None.",
            validation_command="gh --version",
        )
    ]

    outputs = script.write_authorization_outputs(tmp_path, rows)

    assert outputs["status"].exists()
    assert outputs["report"].exists()
    assert "github_cli_binary" in outputs["status"].read_text(encoding="utf-8")


def test_harmonize_github_token_downgrades_persistent_login_blocker():
    script = _load_script("check_external_release_authorization")
    rows = [
        script.AuthCheckRow(
            check_id="github_cli_auth",
            severity="blocking",
            status="not_logged_in",
            evidence="not logged in",
            required_action="login",
            validation_command="gh auth status",
        ),
        script.AuthCheckRow(
            check_id="github_token_api",
            severity="pass",
            status="valid",
            evidence="accepted",
            required_action="none",
            validation_command="python scripts/check_external_release_authorization.py",
        ),
    ]

    updated = script.harmonize_github_env_token(rows)
    by_id = {row.check_id: row for row in updated}

    assert by_id["github_cli_auth"].severity == "pending"
    assert by_id["github_cli_auth"].status == "env_token_available_persistent_login_missing"


def test_valid_token_missing_workflow_scope_remains_blocking():
    script = _load_script("check_external_release_authorization")
    rows = [
        script.AuthCheckRow(
            check_id="github_token_api",
            severity="blocking",
            status="valid_missing_workflow_scope",
            evidence="scopes=repo",
            required_action="add workflow",
            validation_command="python scripts/check_external_release_authorization.py",
        )
    ]

    assert script.classify_decision(rows) == "EXTERNAL_RELEASE_AUTHORIZATION_BLOCKED"
