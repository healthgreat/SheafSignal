#!/usr/bin/env python
"""Build a user-facing handoff for remaining submission blockers.

Author: SheafSignal contributors
Date: 2026-05-03
Purpose: turn live GitHub, Zenodo, and author-owned submission gates into a
clear Chinese handoff checklist without exposing token contents.
"""

from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from pathlib import Path


RELEASE_UNBLOCKER_PATH = Path("release/RELEASE_UNBLOCKER_MATRIX.tsv")
EXTERNAL_AUTH_PATH = Path("release/EXTERNAL_RELEASE_AUTHORIZATION_STATUS.tsv")
ZENODO_PREFLIGHT_PATH = Path("release/ZENODO_UPLOAD_PREFLIGHT_STATUS.tsv")
AUTHOR_PREFLIGHT_PATH = Path("manuscript/submission_metadata/AUTHOR_CONFIRMATION_PREFLIGHT_STATUS.tsv")
OUTPUT_TSV = Path("release/SUBMISSION_UNBLOCKER_HANDOFF_ZH.tsv")
OUTPUT_REPORT = Path("release/SUBMISSION_UNBLOCKER_HANDOFF_ZH.md")


@dataclass(frozen=True)
class HandoffAction:
    priority: str
    owner: str
    action_item: str
    current_status: str
    user_action: str
    codex_after_unblocked: str
    validation_command: str
    submission_impact: str


def _read_tsv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def _first_status(rows: list[dict[str, str]], key: str, value: str, status_col: str = "status") -> str:
    for row in rows:
        if str(row.get(key, "")) == value:
            return str(row.get(status_col, "")).strip()
    return "not_found"


def _count(rows: list[dict[str, str]], key: str, value: str) -> int:
    return sum(1 for row in rows if str(row.get(key, "")) == value)


def build_handoff_actions(root: Path) -> list[HandoffAction]:
    auth_rows = _read_tsv(root / EXTERNAL_AUTH_PATH)
    zenodo_rows = _read_tsv(root / ZENODO_PREFLIGHT_PATH)
    author_rows = _read_tsv(root / AUTHOR_PREFLIGHT_PATH)
    release_rows = _read_tsv(root / RELEASE_UNBLOCKER_PATH)

    github_status = _first_status(auth_rows, "check_id", "github_token_api")
    github_cli_status = _first_status(auth_rows, "check_id", "github_cli_auth")
    zenodo_token_status = _first_status(zenodo_rows, "check_id", "zenodo_token_file")
    zenodo_archive_status = _first_status(zenodo_rows, "check_id", "zenodo_archive_sha256")
    author_blocking = _count(author_rows, "severity", "blocking")
    author_pending = _count(author_rows, "severity", "pending")
    live_blockers = _count(release_rows, "priority", "blocking")

    actions = [
        HandoffAction(
            priority="P0",
            owner="user",
            action_item="GitHub token needs workflow scope",
            current_status=f"github_token_api={github_status}; github_cli_auth={github_cli_status}",
            user_action=(
                "Regenerate a GitHub classic token with repo and workflow scopes, "
                "then overwrite D:\\secrets\\github_token.txt. Do not paste the token into chat."
            ),
            codex_after_unblocked=(
                "Validate scopes, push codex/sheafsignal-hardening-release to the public repo, "
                "create v0.1.0 tag/release, and record the release URL."
            ),
            validation_command="python scripts/check_external_release_authorization.py",
            submission_impact="Required for public, citable GitHub code release.",
        ),
        HandoffAction(
            priority="P0",
            owner="user_or_codex_after_token",
            action_item="Zenodo DOI minting",
            current_status=f"zenodo_archive_sha256={zenodo_archive_status}; zenodo_token_file={zenodo_token_status}",
            user_action=(
                "Either upload release/archives/sheafsignal_zenodo_upload.zip manually to Zenodo "
                "and provide the DOI, or save a Zenodo API token to D:\\secrets\\zenodo_token.txt."
            ),
            codex_after_unblocked=(
                "Insert the minted DOI into metadata/datasets.tsv, Data Availability, release metadata, "
                "and rerun placeholder/final blocker audits."
            ),
            validation_command="python scripts/check_zenodo_upload_preflight.py",
            submission_impact="Required for permanent processed-data/software archive citation.",
        ),
        HandoffAction(
            priority="P0",
            owner="authors",
            action_item="Author-owned submission facts",
            current_status=f"blocking={author_blocking}; pending={author_pending}",
            user_action=(
                "Provide Han Yan email, final equal-contribution wording, final author order, "
                "CRediT approval, funding statement, COI statement, ethics/data-use wording, "
                "and explicit GitHub/Zenodo public-release approval."
            ),
            codex_after_unblocked=(
                "Update submission metadata templates, rerun author preflight, and regenerate final "
                "submission blocker report."
            ),
            validation_command="python scripts/check_author_confirmation_preflight.py",
            submission_impact="Required before journal upload; these facts cannot be inferred by code.",
        ),
        HandoffAction(
            priority="P1",
            owner="codex_after_public_release",
            action_item="Public clean-clone reproduction",
            current_status=f"release_blocking_gates={live_blockers}",
            user_action="No manual analysis needed after GitHub and Zenodo identifiers are real.",
            codex_after_unblocked=(
                "Clone the public repository into a fresh directory, install locked dependencies, "
                "run demo/tests/audits, and write clean-clone evidence."
            ),
            validation_command="python -m pytest -q; python scripts/release_audit.py",
            submission_impact="Converts local reproducibility into reviewer-grade public reproducibility evidence.",
        ),
        HandoffAction(
            priority="P1",
            owner="codex",
            action_item="Submission-day journal metric and warning-list check",
            current_status="pending_submission_day",
            user_action="Pick the target journal route only after the final GO/NO-GO report is green.",
            codex_after_unblocked=(
                "Recheck latest JIF, CAS zone, and warning-list status for the chosen journal before submission."
            ),
            validation_command="rerun journal metric audit immediately before submission",
            submission_impact="Prevents stale IF/CAS/warning claims in the submission strategy.",
        ),
    ]
    return actions


def _write_tsv_atomic(path: Path, actions: list[HandoffAction]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    fieldnames = list(HandoffAction.__dataclass_fields__.keys())
    with tmp_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, delimiter="\t")
        writer.writeheader()
        for action in actions:
            writer.writerow(action.__dict__)
    tmp_path.replace(path)


def _write_text_atomic(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    tmp_path.write_text(text, encoding="utf-8")
    tmp_path.replace(path)


def build_report(actions: list[HandoffAction]) -> str:
    p0 = [action for action in actions if action.priority == "P0"]
    p1 = [action for action in actions if action.priority == "P1"]
    lines = [
        "# SheafSignal 投稿解锁交接单",
        "",
        "- Decision: `SUBMISSION_EXTERNAL_ACTIONS_REQUIRED`",
        f"- P0 blockers: `{len(p0)}`",
        f"- P1 follow-up actions: `{len(p1)}`",
        "- Boundary: 这是投稿基础设施和作者事实交接单，不是期刊接收保证。",
        "",
        "## 你现在只需要处理的事",
        "",
        "1. GitHub token 重新生成：勾选 `repo` 和 `workflow`，覆盖 `D:\\secrets\\github_token.txt`。",
        "2. Zenodo：手动上传 `release/archives/sheafsignal_zenodo_upload.zip` 并给 DOI，或保存 token 到 `D:\\secrets\\zenodo_token.txt`。",
        "3. 作者信息：补 Han Yan 邮箱、共同贡献准确写法、CRediT、funding、COI、ethics/data-use、GitHub/Zenodo 公开授权。",
        "   推荐直接填写 `manuscript/submission_metadata/AUTHOR_CONFIRMATION_RESPONSE_TEMPLATE.tsv`。",
        "",
        "## 我在你完成后会直接做的事",
        "",
        "1. 验证 GitHub token scope，不打印 token 内容。",
        "2. push 当前分支到公开 GitHub，创建 release tag。",
        "3. 写回真实 Zenodo DOI 和 GitHub release metadata。",
        "4. 从公开 GitHub clean clone，重跑 tests/audits。",
        "5. 重新生成 final GO/NO-GO、IF20-50 distance report 和投稿包。",
        "6. 运行 guarded post-unblock release pipeline："
        "`python scripts/build_post_unblock_release_pipeline.py --doi <REAL_ZENODO_DOI> --execute`。",
        "",
        "## Action Table",
        "",
        "| Priority | Owner | Action item | Current status | User action | Codex after unblocked | Validation |",
        "|---|---|---|---|---|---|---|",
    ]
    for action in actions:
        lines.append(
            f"| `{action.priority}` | `{action.owner}` | {action.action_item} | "
            f"`{action.current_status}` | {action.user_action} | "
            f"{action.codex_after_unblocked} | `{action.validation_command}` |"
        )
    lines.extend(
        [
            "",
            "## 20-50 IF 解释边界",
            "",
        "这些 P0 blocker 清除后，项目才进入正式 20-50 IF submission package 阶段。"
        "清除它们会提高可复现性和投稿合规性，但不能保证任何期刊接收。",
        "",
        "## 已准备好的自动化链条",
        "",
        "- `manuscript/submission_metadata/AUTHOR_CONFIRMATION_RESPONSE_TEMPLATE.tsv`",
        "- `scripts/apply_author_confirmation_response.py`",
        "- `release/POST_UNBLOCK_RELEASE_PIPELINE_PLAN.tsv`",
        "- `release/POST_UNBLOCK_RELEASE_PIPELINE_REPORT.md`",
        "",
        "默认命令只生成计划，不执行外部发布：",
        "",
        "```bash",
        "python scripts/build_post_unblock_release_pipeline.py",
        "```",
        "",
        "只有 GitHub、Zenodo、作者确认都解除后，才允许显式执行：",
        "",
        "```bash",
        "python scripts/build_post_unblock_release_pipeline.py --doi <REAL_ZENODO_DOI> --execute",
        "```",
        "",
    ]
    )
    return "\n".join(lines)


def write_outputs(root: Path, actions: list[HandoffAction]) -> dict[str, Path]:
    tsv_path = root / OUTPUT_TSV
    report_path = root / OUTPUT_REPORT
    _write_tsv_atomic(tsv_path, actions)
    _write_text_atomic(report_path, build_report(actions))
    return {"tsv": tsv_path, "report": report_path}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    args = parser.parse_args(argv)

    root = Path(args.root).resolve()
    actions = build_handoff_actions(root)
    outputs = write_outputs(root, actions)
    print("SUBMISSION_UNBLOCKER_HANDOFF_WRITTEN")
    print(f"P0 blockers: {sum(action.priority == 'P0' for action in actions)}")
    for label, path in outputs.items():
        print(f"{label}: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
