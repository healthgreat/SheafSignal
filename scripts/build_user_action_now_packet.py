#!/usr/bin/env python
"""Build the shortest current user-action packet for submission blockers.

Author: SheafSignal contributors
Date: 2026-05-03
Purpose: convert live release, author, contact, and review gates into a concise
human action sheet so that external blockers can be cleared without guessing.
"""

from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


RELEASE_STATUS = Path("release/EXTERNAL_RELEASE_AUTHORIZATION_STATUS.tsv")
AUTHOR_PREFLIGHT = Path("manuscript/submission_metadata/AUTHOR_CONFIRMATION_PREFLIGHT_STATUS.tsv")
CONTACT_RECONCILIATION = Path("manuscript/submission_metadata/AUTHOR_CONTACT_RECONCILIATION.tsv")
EXTERNAL_REVIEW_TRIAGE = Path("external_ai_review_packet/EXTERNAL_BETA_REVIEW_TRIAGE_REPORT.md")
OUTPUT_TSV = Path("release/USER_ACTION_NOW_PACKET.tsv")
OUTPUT_MD = Path("release/USER_ACTION_NOW_PACKET_ZH.md")


@dataclass(frozen=True)
class ActionRow:
    priority: str
    item: str
    current_status: str
    what_user_should_do: str
    what_codex_will_do_after: str
    validation: str


def _read_tsv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def _read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def _write_tsv_atomic(path: Path, rows: list[ActionRow]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    fieldnames = list(ActionRow.__dataclass_fields__.keys())
    with tmp_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, delimiter="\t")
        writer.writeheader()
        for row in rows:
            writer.writerow(row.__dict__)
    tmp_path.replace(path)


def _write_text_atomic(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    tmp_path.write_text(text, encoding="utf-8")
    tmp_path.replace(path)


def _row_by_id(rows: list[dict[str, str]], check_id: str) -> dict[str, str]:
    for row in rows:
        if row.get("check_id") == check_id:
            return row
    return {}


def _count_author(rows: list[dict[str, str]], severity: str) -> int:
    return sum(row.get("severity") == severity for row in rows)


def _count_contact(rows: list[dict[str, str]], action_needed: str) -> int:
    return sum(row.get("action_needed") == action_needed for row in rows)


def _review_decision(text: str) -> str:
    marker = "- Decision: `"
    if marker not in text:
        return "not_run"
    return text.split(marker, 1)[1].split("`", 1)[0]


def build_action_rows(root: Path) -> list[ActionRow]:
    release_rows = _read_tsv(root / RELEASE_STATUS)
    author_rows = _read_tsv(root / AUTHOR_PREFLIGHT)
    contact_rows = _read_tsv(root / CONTACT_RECONCILIATION)
    review_text = _read_text(root / EXTERNAL_REVIEW_TRIAGE)

    github_token = _row_by_id(release_rows, "github_token_api")
    github_cli = _row_by_id(release_rows, "github_cli_auth")
    zenodo_token = _row_by_id(release_rows, "zenodo_token_file")
    zenodo_doi = _row_by_id(release_rows, "zenodo_doi_placeholders")

    blocking_author = _count_author(author_rows, "blocking")
    pending_author = _count_author(author_rows, "pending")
    missing_contact = _count_contact(contact_rows, "blocking_missing_email")
    extra_contacts = _count_contact(contact_rows, "confirm_not_author_or_update_author_line")
    review_decision = _review_decision(review_text)

    rows = [
        ActionRow(
            "P0",
            "GitHub token / gh login",
            f"github_token_api={github_token.get('status', 'missing')}; gh={github_cli.get('status', 'missing')}",
            "Create or update a GitHub classic token with repo and workflow scopes, save it to D:/secrets/github_token.txt, and do not paste it into chat.",
            "Validate token scopes, authenticate GitHub tooling if possible, push the branch, then create the public release/tag after final gates pass.",
            "python scripts/check_external_release_authorization.py",
        ),
        ActionRow(
            "P0",
            "Han Yan email and author contact consistency",
            f"missing_current_author_email={missing_contact}; extra_supplied_contacts={extra_contacts}",
            "Provide Han Yan email. Confirm whether the 16 supplied contacts not in the current author line are non-authors or should be added with author order/affiliations/CRediT.",
            "Update author metadata templates, rerun contact reconciliation and author preflight, then regenerate submission metadata.",
            "python scripts/reconcile_author_contacts.py && python scripts/check_author_confirmation_preflight.py",
        ),
        ActionRow(
            "P0",
            "Author-owned declarations",
            f"blocking={blocking_author}; pending={pending_author}",
            "Confirm final author order, equal-contribution wording, CRediT, funding, competing interests, ethics/data-use wording, and GitHub/Zenodo public-release approval.",
            "Apply AUTHOR_CONFIRMATION_RESPONSE_TEMPLATE.tsv, update manuscript-facing statements, and rerun final blocker checks.",
            "python scripts/apply_author_confirmation_response.py --apply && python scripts/check_author_confirmation_preflight.py",
        ),
        ActionRow(
            "P0",
            "Zenodo DOI",
            f"token={zenodo_token.get('status', 'missing')}; doi_placeholder={zenodo_doi.get('status', 'missing')}",
            "Either manually upload release/archives/sheafsignal_zenodo_upload.zip to Zenodo and give Codex the DOI, or save a Zenodo API token to D:/secrets/zenodo_token.txt.",
            "Insert the real DOI into release metadata, Data Availability, and dataset manifest, then rebuild release archives and audits.",
            "python scripts/check_release_metadata_placeholders.py",
        ),
        ActionRow(
            "P1",
            "External beta review return",
            review_decision,
            "Send the prepared external review bundle to 2-3 independent AI/human reviewers and return their comments.",
            "Triage returned reviews into fixed, downgraded_by_design, or out_of_scope actions before final journal targeting.",
            "reviewer response matrix update",
        ),
    ]
    return rows


def classify_decision(rows: list[ActionRow]) -> str:
    if any(row.priority == "P0" for row in rows):
        return "USER_ACTION_PACKET_READY_P0_BLOCKERS_REMAIN"
    return "USER_ACTION_PACKET_READY_NO_P0_BLOCKERS"


def build_report(rows: list[ActionRow]) -> str:
    decision = classify_decision(rows)
    p0_rows = [row for row in rows if row.priority == "P0"]
    p1_rows = [row for row in rows if row.priority == "P1"]
    table = [
        "| Priority | Item | Current status | What you do | What Codex does after | Validation |",
        "|---|---|---|---|---|---|",
    ]
    for row in rows:
        table.append(
            f"| `{row.priority}` | {row.item} | `{row.current_status}` | {row.what_user_should_do} | {row.what_codex_will_do_after} | `{row.validation}` |"
        )
    return "\n".join(
        [
            "# SheafSignal 当前最短行动包",
            "",
            f"- Timestamp: `{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}`",
            f"- Decision: `{decision}`",
            f"- P0 items: `{len(p0_rows)}`",
            f"- P1 items: `{len(p1_rows)}`",
            "",
            "## 你现在只需要处理什么",
            "",
            "推荐先填写统一入口：`release/EXTERNAL_INPUT_INTAKE_TEMPLATE.tsv`。",
            "",
            "1. 重新生成 GitHub token：必须包含 `repo` 和 `workflow` scopes，保存到 `D:/secrets/github_token.txt`。",
            "2. 提供 Han Yan email，并确认额外 16 个联系人是否不是作者；如果是作者，需要给出最终 author order、affiliation 和 CRediT。",
            "3. 确认 author declarations：equal contribution、CRediT、funding、COI、ethics/data-use、GitHub/Zenodo public release approval。",
            "4. Zenodo：手动上传 `release/archives/sheafsignal_zenodo_upload.zip` 后给 DOI，或把 Zenodo API token 保存到 `D:/secrets/zenodo_token.txt`。",
            "5. 把 external review bundle 发给外部 AI/同行评审，拿回意见。",
            "",
            "## Action Table",
            "",
            *table,
            "",
            "## 我拿到这些信息后会直接做什么",
            "",
            "首先运行一键 readiness 检查：",
            "",
            "```bash",
            "python scripts/build_external_input_intake.py",
            "python scripts/apply_external_input_intake.py",
            "python scripts/run_unblock_readiness_check.py",
            "```",
            "",
            "1. 验证 token scope 和 Zenodo/API 状态，不打印任何 token。",
            "2. 更新 author metadata、Data Availability、DOI 和 GitHub release 信息。",
            "3. push 当前分支，创建 frozen release/tag。",
            "4. public clean-clone 复现，并重跑 `pytest`、`ruff`、release audit、final blocker report。",
            "5. 刷新 live Gantt、IF20-50 distance report 和 final GO/NO-GO。",
            "",
            "## 边界",
            "",
            "这个行动包解决投稿基础设施和作者事实卡点。它会提高 20-50 IF 投稿可防御性，但不保证任何期刊接收。",
            "",
        ]
    )


def build_outputs(root: Path) -> dict[str, object]:
    root = root.resolve()
    rows = build_action_rows(root)
    _write_tsv_atomic(root / OUTPUT_TSV, rows)
    _write_text_atomic(root / OUTPUT_MD, build_report(rows))
    return {
        "decision": classify_decision(rows),
        "rows": len(rows),
        "p0_rows": sum(row.priority == "P0" for row in rows),
        "tsv": OUTPUT_TSV.as_posix(),
        "report": OUTPUT_MD.as_posix(),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    args = parser.parse_args(argv)
    summary = build_outputs(Path(args.root))
    print("USER_ACTION_NOW_PACKET_WRITTEN")
    for key, value in summary.items():
        print(f"{key}: {value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
