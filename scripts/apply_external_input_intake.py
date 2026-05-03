#!/usr/bin/env python
"""Convert filled external-input intake rows into author response rows.

Author: SheafSignal contributors
Date: 2026-05-03
Purpose: avoid duplicate manual entry by translating validated user-owned
intake fields into the author confirmation response TSV. By default this writes
a derived review file and does not overwrite the canonical author response.
"""

from __future__ import annotations

import argparse
import csv
import re
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


DEFAULT_INTAKE = Path("release/EXTERNAL_INPUT_INTAKE_TEMPLATE.tsv")
DEFAULT_AUTHOR_RESPONSE = Path(
    "manuscript/submission_metadata/AUTHOR_CONFIRMATION_RESPONSE_TEMPLATE.tsv"
)
DEFAULT_DERIVED_RESPONSE = Path(
    "manuscript/submission_metadata/AUTHOR_CONFIRMATION_RESPONSE_FROM_INTAKE.tsv"
)
DEFAULT_REPORT = Path(
    "manuscript/submission_metadata/AUTHOR_CONFIRMATION_FROM_INTAKE_REPORT.md"
)

YES_VALUES = {"yes", "approved", "confirmed", "true"}


@dataclass(frozen=True)
class DerivedRow:
    item: str
    current_value: str
    required_confirmation: str
    owner: str
    confirmed: str
    final_value: str
    notes: str


@dataclass(frozen=True)
class DerivationAuditRow:
    source_field: str
    target_item: str
    status: str
    evidence: str


def _read_tsv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def _replace_with_retry(tmp_path: Path, final_path: Path, retries: int = 5) -> None:
    for attempt in range(retries):
        try:
            tmp_path.replace(final_path)
            return
        except PermissionError:
            if attempt == retries - 1:
                raise
            time.sleep(0.2 * (attempt + 1))


def _write_tsv_atomic(path: Path, rows: list[object], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    with tmp_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, delimiter="\t")
        writer.writeheader()
        for row in rows:
            writer.writerow(row.__dict__)
    _replace_with_retry(tmp_path, path)


def _write_text_atomic(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    tmp_path.write_text(text, encoding="utf-8")
    _replace_with_retry(tmp_path, path)


def _intake_map(rows: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    return {str(row.get("field_id", "")).strip(): row for row in rows}


def _is_email(value: str) -> bool:
    return bool(re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", value.strip()))


def _is_yes(value: str) -> bool:
    return value.strip().lower() in YES_VALUES


def _value(rows: dict[str, dict[str, str]], field_id: str) -> str:
    return str(rows.get(field_id, {}).get("user_value", "")).strip()


def _notes(rows: dict[str, dict[str, str]], field_id: str) -> str:
    return str(rows.get(field_id, {}).get("notes", "")).strip()


def _response_index(rows: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    return {str(row.get("item", "")).strip(): row for row in rows}


def _base_row(response_index: dict[str, dict[str, str]], item: str) -> dict[str, str]:
    return dict(response_index.get(item, {"item": item, "current_value": "", "required_confirmation": "", "owner": ""}))


def _confirmed_row(
    response_index: dict[str, dict[str, str]],
    item: str,
    final_value: str,
    notes: str,
) -> DerivedRow:
    base = _base_row(response_index, item)
    return DerivedRow(
        item=item,
        current_value=str(base.get("current_value", "")),
        required_confirmation=str(base.get("required_confirmation", "")),
        owner=str(base.get("owner", "")),
        confirmed="yes",
        final_value=final_value,
        notes=notes,
    )


def _pending_row(response_index: dict[str, dict[str, str]], item: str, reason: str) -> DerivedRow:
    base = _base_row(response_index, item)
    return DerivedRow(
        item=item,
        current_value=str(base.get("current_value", "")),
        required_confirmation=str(base.get("required_confirmation", "")),
        owner=str(base.get("owner", "")),
        confirmed="fill_yes_no_or_skip",
        final_value="",
        notes=reason,
    )


def derive_author_response(
    intake_rows: list[dict[str, str]],
    existing_response_rows: list[dict[str, str]],
) -> tuple[list[DerivedRow], list[DerivationAuditRow]]:
    intake = _intake_map(intake_rows)
    response_index = _response_index(existing_response_rows)
    rows: list[DerivedRow] = []
    audit: list[DerivationAuditRow] = []

    def add(item: str, source: str, valid: bool, final_value: str, note: str) -> None:
        if valid:
            rows.append(_confirmed_row(response_index, item, final_value, note))
            status = "derived"
            evidence = final_value
        else:
            rows.append(_pending_row(response_index, item, note))
            status = "pending"
            evidence = note
        audit.append(DerivationAuditRow(source, item, status, evidence))

    han_email = _value(intake, "han_yan_email")
    add(
        "Han Yan email",
        "han_yan_email",
        _is_email(han_email),
        han_email,
        "Need a valid Han Yan email in intake user_value.",
    )

    equal_wording = _value(intake, "equal_contribution_wording")
    add(
        "equal contribution note",
        "equal_contribution_wording",
        bool(equal_wording),
        equal_wording,
        "Need exact equal-contribution wording in intake user_value.",
    )

    extra_decision = _value(intake, "extra_contacts_decision")
    author_order_ok = _is_yes(_value(intake, "author_order_approved"))
    author_note = "Extra supplied contacts decision: " + (extra_decision or "missing")
    if extra_decision == "expand_author_line":
        author_note += "; author line must be updated before approval."
        author_order_ok = False
    if _notes(intake, "author_order_approved"):
        author_note += "; " + _notes(intake, "author_order_approved")
    add(
        "author order",
        "author_order_approved",
        author_order_ok and extra_decision == "not_authors",
        _base_row(response_index, "author order").get("current_value", ""),
        author_note,
    )

    add(
        "affiliations",
        "author_order_approved",
        author_order_ok,
        _base_row(response_index, "affiliations").get("current_value", ""),
        _notes(intake, "author_order_approved") or "Affiliations approved through intake.",
    )

    add(
        "CRediT roles",
        "credit_roles_approved",
        _is_yes(_value(intake, "credit_roles_approved")),
        _base_row(response_index, "CRediT roles").get("current_value", ""),
        _notes(intake, "credit_roles_approved") or "CRediT roles approved through intake.",
    )

    funding = _value(intake, "funding_statement_approved")
    add(
        "funding acquisition",
        "funding_statement_approved",
        bool(funding),
        "Not reported" if _is_yes(funding) else funding,
        "Funding statement derived from intake.",
    )

    coi = _value(intake, "competing_interests_approved")
    add(
        "competing interests",
        "competing_interests_approved",
        bool(coi),
        _base_row(response_index, "competing interests").get("current_value", "")
        if _is_yes(coi)
        else coi,
        "Competing interests statement derived from intake.",
    )

    ethics = _value(intake, "ethics_data_use_approved")
    add(
        "ethics data-use",
        "ethics_data_use_approved",
        bool(ethics),
        _base_row(response_index, "ethics data-use").get("current_value", "")
        if _is_yes(ethics)
        else ethics,
        "Ethics/data-use statement derived from intake.",
    )

    add(
        "public GitHub release",
        "github_public_release_approved",
        _is_yes(_value(intake, "github_public_release_approved")),
        "Public GitHub release approved.",
        _notes(intake, "github_public_release_approved") or "Release approval derived from intake.",
    )

    add(
        "Zenodo deposition",
        "zenodo_deposition_approved",
        _is_yes(_value(intake, "zenodo_deposition_approved")),
        "Zenodo deposition approved.",
        _notes(intake, "zenodo_deposition_approved") or "Zenodo approval derived from intake.",
    )

    rows.append(_pending_row(response_index, "ORCID IDs", "Optional ORCID IDs not handled by intake."))
    audit.append(
        DerivationAuditRow(
            "orcid_ids",
            "ORCID IDs",
            "optional_pending",
            "Optional ORCID IDs not handled by intake.",
        )
    )
    return rows, audit


def classify_decision(audit_rows: list[DerivationAuditRow]) -> str:
    if not audit_rows:
        return "AUTHOR_RESPONSE_FROM_INTAKE_INPUT_MISSING"
    if any(row.status == "pending" for row in audit_rows):
        return "AUTHOR_RESPONSE_FROM_INTAKE_PARTIAL"
    return "AUTHOR_RESPONSE_FROM_INTAKE_READY"


def build_report(
    audit_rows: list[DerivationAuditRow],
    *,
    overwrite_response_template: bool,
) -> str:
    decision = classify_decision(audit_rows)
    derived = sum(row.status == "derived" for row in audit_rows)
    pending = sum(row.status == "pending" for row in audit_rows)
    optional = sum(row.status == "optional_pending" for row in audit_rows)
    audit_lines = [
        f"- `{row.source_field}` -> `{row.target_item}`: `{row.status}` ({row.evidence})"
        for row in audit_rows
    ] or ["- none"]
    return "\n".join(
        [
            "# Author Response From External Intake Report",
            "",
            f"- Timestamp: `{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}`",
            f"- Decision: `{decision}`",
            f"- Overwrote canonical response template: `{overwrite_response_template}`",
            f"- Derived rows: `{derived}`",
            f"- Pending rows: `{pending}`",
            f"- Optional pending rows: `{optional}`",
            "",
            "## Derivation Audit",
            "",
            *audit_lines,
            "",
            "## Next Command When Ready",
            "",
            "```bash",
            "python scripts/apply_author_confirmation_response.py --apply",
            "python scripts/check_author_confirmation_preflight.py",
            "```",
            "",
            "## Boundary",
            "",
            "This script only translates user-provided intake values into an author",
            "response TSV. It does not decide authorship, does not validate email",
            "ownership, does not infer missing declarations, and does not guarantee",
            "journal acceptance.",
            "",
        ]
    )


def build_outputs(
    root: Path,
    *,
    overwrite_response_template: bool = False,
) -> dict[str, object]:
    root = root.resolve()
    rows, audit = derive_author_response(
        _read_tsv(root / DEFAULT_INTAKE),
        _read_tsv(root / DEFAULT_AUTHOR_RESPONSE),
    )
    output_path = root / (
        DEFAULT_AUTHOR_RESPONSE if overwrite_response_template else DEFAULT_DERIVED_RESPONSE
    )
    _write_tsv_atomic(output_path, rows, list(DerivedRow.__dataclass_fields__.keys()))
    _write_text_atomic(
        root / DEFAULT_REPORT,
        build_report(audit, overwrite_response_template=overwrite_response_template),
    )
    return {
        "decision": classify_decision(audit),
        "rows": len(rows),
        "pending_rows": sum(row.status == "pending" for row in audit),
        "response": output_path.relative_to(root).as_posix(),
        "report": DEFAULT_REPORT.as_posix(),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--overwrite-response-template", action="store_true")
    args = parser.parse_args(argv)
    summary = build_outputs(
        Path(args.root),
        overwrite_response_template=args.overwrite_response_template,
    )
    print("AUTHOR_RESPONSE_FROM_INTAKE_WRITTEN")
    for key, value in summary.items():
        print(f"{key}: {value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
