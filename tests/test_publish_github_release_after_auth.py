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


def test_scope_parser_requires_workflow():
    script = _load_script("publish_github_release_after_auth")

    assert script.missing_required_scopes("repo, gist") == {"workflow"}
    assert script.missing_required_scopes("repo, workflow") == set()


def test_release_steps_include_push_and_tag():
    script = _load_script("publish_github_release_after_auth")

    steps = script.build_release_steps(
        repo="healthgreat/SheafSignal",
        branch="codex/sheafsignal-hardening-release",
        tag="v0.1.0",
        archive=Path("release/archives/sheafsignal_github_release.zip"),
        create_release=True,
        draft=True,
    )
    ids = [step.step_id for step in steps]

    assert "push_branch" in ids
    assert "push_tag" in ids
    assert "create_github_release" in ids
    assert "--draft" in steps[-1].command


def test_publication_report_keeps_acceptance_boundary():
    script = _load_script("publish_github_release_after_auth")

    report = script.build_report(
        decision="GITHUB_RELEASE_DRY_RUN_READY",
        login="healthgreat",
        scopes="repo, workflow",
        branch="codex/sheafsignal-hardening-release",
        tag="v0.1.0",
        repo="healthgreat/SheafSignal",
        logs=["DRY_RUN push_branch"],
        dry_run=True,
    )

    assert "GITHUB_RELEASE_DRY_RUN_READY" in report
    assert "does not guarantee" in report


def test_blocked_report_mentions_missing_scope_without_token_content():
    script = _load_script("publish_github_release_after_auth")

    report = script.build_blocked_report(
        "GitHub token is valid but missing required scope(s): workflow"
    )

    assert "GITHUB_RELEASE_BLOCKED" in report
    assert "workflow" in report
    assert "token contents" in report
