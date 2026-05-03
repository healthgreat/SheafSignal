# SheafSignal 当前最短行动包

- Timestamp: `2026-05-04 03:14:37`
- Decision: `USER_ACTION_PACKET_READY_NO_P0_BLOCKERS`
- P0 items: `0`
- P1 items: `1`

## 你现在只需要处理什么

当前没有 P0 用户动作。GitHub token rotation、作者声明、GitHub public release 和 Zenodo DOI 已有可审计记录。
P1 只剩外部 beta review return：这是 20-50 IF 稿件的加分项，不是本地 release 阻断项。

## Action Table

| Priority | Item | Current status | What you do | What Codex does after | Validation |
|---|---|---|---|---|---|
| `DONE` | GitHub token / gh login | `github_token_api=valid; gh=env_token_available_persistent_login_missing` | No user action needed. | Validate token scopes, authenticate GitHub tooling if possible, push the branch, then create the public release/tag after final gates pass. | `python scripts/check_external_release_authorization.py` |
| `DONE` | GitHub token rotation after chat exposure | `github_token_rotation_confirmed=pass` | No user action needed. | Use the token for GitHub push/release only after this safety gate passes. | `python scripts/build_external_input_intake.py` |
| `DONE` | Han Yan email and author contact consistency | `missing_current_author_email=0; extra_supplied_contacts=0` | No user action needed. | Update author metadata templates, rerun contact reconciliation and author preflight, then regenerate submission metadata. | `python scripts/reconcile_author_contacts.py && python scripts/check_author_confirmation_preflight.py` |
| `DONE` | Author-owned declarations | `blocking=0; pending=0` | No user action needed. | Apply AUTHOR_CONFIRMATION_RESPONSE_TEMPLATE.tsv, update manuscript-facing statements, and rerun final blocker checks. | `python scripts/apply_author_confirmation_response.py --apply && python scripts/check_author_confirmation_preflight.py` |
| `DONE` | Zenodo DOI | `token=present; doi_placeholder=cleared; published_doi=10.5281/zenodo.20012189` | No user action needed. | Keep the real DOI in release metadata, Data Availability, and dataset manifest; rebuild release archives and audits after any tracked release-file change. | `python scripts/check_release_metadata_placeholders.py` |
| `P1` | External beta review return | `EXTERNAL_BETA_REVIEW_NO_RETURNED_REVIEWS` | Send the prepared external review bundle to 2-3 independent AI/human reviewers and return their comments. | Triage returned reviews into fixed, downgraded_by_design, or out_of_scope actions before final journal targeting. | `reviewer response matrix update` |

## 我接下来直接做什么

我会继续运行一键 readiness 检查：

```bash
python scripts/build_external_input_intake.py
python scripts/apply_external_input_intake.py
python scripts/run_unblock_readiness_check.py
```

1. 验证 token scope 和 Zenodo/API 状态，不打印任何 token。
2. 更新 author metadata、Data Availability、DOI 和 GitHub release 信息。
3. push 当前分支，维护 frozen release/tag。
4. public clean-clone 复现，并重跑 `pytest`、`ruff`、release audit、final blocker report。
5. 刷新 live Gantt、IF20-50 distance report 和 final GO/NO-GO。

## 边界

这个行动包解决投稿基础设施和作者事实卡点。它会提高 20-50 IF 投稿可防御性，但不保证任何期刊接收。
