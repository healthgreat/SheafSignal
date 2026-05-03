# External Input Intake Report

- Timestamp: `2026-05-03 08:08:43`
- Decision: `EXTERNAL_INPUT_INTAKE_P0_MISSING`
- P0 missing/blocking fields: `11`

## Intake Status

| Field | Priority | Status | Blocking | Evidence | Next action |
|---|---|---|---|---|---|
| `github_token_file` | `P0` | `pass` | `no` | D:\secrets\github_token.txt exists_nonempty | Save the required secret file to D:\secrets\github_token.txt. |
| `zenodo_doi` | `P0` | `missing` | `yes` | doi_valid=False; zenodo_token_file_present=False | Fill a real DOI or save a Zenodo token outside the repository. |
| `han_yan_email` | `P0` | `missing` | `yes` | email_missing_or_invalid | Provide a valid email address. |
| `extra_contacts_decision` | `P0` | `missing` | `yes` | value=blank; allowed=expand_author_line,not_authors | Choose one of the allowed values and put details in notes if needed. |
| `equal_contribution_wording` | `P0` | `missing` | `yes` | blank | Provide an approval value or replacement wording in user_value. |
| `author_order_approved` | `P0` | `missing` | `yes` | value=blank | Enter yes/approved/confirmed, or document corrections before approval. |
| `credit_roles_approved` | `P0` | `missing` | `yes` | value=blank | Enter yes/approved/confirmed, or document corrections before approval. |
| `funding_statement_approved` | `P0` | `missing` | `yes` | blank | Provide an approval value or replacement wording in user_value. |
| `competing_interests_approved` | `P0` | `missing` | `yes` | blank | Provide an approval value or replacement wording in user_value. |
| `ethics_data_use_approved` | `P0` | `missing` | `yes` | blank | Provide an approval value or replacement wording in user_value. |
| `github_public_release_approved` | `P0` | `missing` | `yes` | value=blank | Enter yes/approved/confirmed, or document corrections before approval. |
| `zenodo_deposition_approved` | `P0` | `missing` | `yes` | value=blank | Enter yes/approved/confirmed, or document corrections before approval. |
| `external_beta_review_return_path` | `P1` | `pass` | `no` | optional_blank | Optionally provide a real path to returned reviews. |

## How To Use

Fill `release/EXTERNAL_INPUT_INTAKE_TEMPLATE.tsv`. Do not paste GitHub
or Zenodo token values into the TSV. Save secret tokens only to the
`secret_path` locations listed in the template.

After filling the TSV or secret files, run:

```bash
python scripts/build_external_input_intake.py
python scripts/run_unblock_readiness_check.py
```

## Boundary

This intake validates whether required external inputs are present. It
does not infer authorship, does not validate token scopes by itself,
does not mint a DOI, and does not guarantee journal acceptance.
