# SheafSignal 当前最短行动包

- Timestamp: `2026-05-04 00:49:12`
- Decision: `USER_ACTION_PACKET_READY_P0_BLOCKERS_REMAIN`
- P0 items: `1`
- P1 items: `1`

## 你现在只需要处理什么

推荐先填写统一入口：`release/EXTERNAL_INPUT_INTAKE_TEMPLATE.tsv`。

1. 重新生成 GitHub token：必须包含 `repo` 和 `workflow` scopes，保存到 `D:/secrets/github_token.txt`。
2. 提供 Han Yan email，并确认额外 16 个联系人是否不是作者；如果是作者，需要给出最终 author order、affiliation 和 CRediT。
3. 确认 author declarations：equal contribution、CRediT、funding、COI、ethics/data-use、GitHub/Zenodo public release approval。
4. Zenodo：手动上传 `release/archives/sheafsignal_zenodo_upload.zip` 后给 DOI，或把 Zenodo API token 保存到 `D:/secrets/zenodo_token.txt`。
5. 把 external review bundle 发给外部 AI/同行评审，拿回意见。

## Action Table

| Priority | Item | Current status | What you do | What Codex does after | Validation |
|---|---|---|---|---|---|
| `DONE` | GitHub token / gh login | `github_token_api=valid; gh=env_token_available_persistent_login_missing` | No user action needed. | Validate token scopes, authenticate GitHub tooling if possible, push the branch, then create the public release/tag after final gates pass. | `python scripts/check_external_release_authorization.py` |
| `DONE` | Han Yan email and author contact consistency | `missing_current_author_email=0; extra_supplied_contacts=0` | No user action needed. | Update author metadata templates, rerun contact reconciliation and author preflight, then regenerate submission metadata. | `python scripts/reconcile_author_contacts.py && python scripts/check_author_confirmation_preflight.py` |
| `P0` | Author-owned declarations | `blocking=0; pending=6` | Confirm CRediT, funding, competing interests, ethics/data-use wording, and GitHub/Zenodo public-release approval. | Apply AUTHOR_CONFIRMATION_RESPONSE_TEMPLATE.tsv, update manuscript-facing statements, and rerun final blocker checks. | `python scripts/apply_author_confirmation_response.py --apply && python scripts/check_author_confirmation_preflight.py` |
| `CODEX_READY` | Zenodo DOI | `token=present; doi_placeholder=pending` | No user action needed; Codex can mint DOI after author release approval. | Insert the real DOI into release metadata, Data Availability, and dataset manifest, then rebuild release archives and audits. | `python scripts/check_release_metadata_placeholders.py` |
| `P1` | External beta review return | `EXTERNAL_BETA_REVIEW_NO_RETURNED_REVIEWS` | Send the prepared external review bundle to 2-3 independent AI/human reviewers and return their comments. | Triage returned reviews into fixed, downgraded_by_design, or out_of_scope actions before final journal targeting. | `reviewer response matrix update` |

## 我拿到这些信息后会直接做什么

首先运行一键 readiness 检查：

```bash
python scripts/build_external_input_intake.py
python scripts/apply_external_input_intake.py
python scripts/run_unblock_readiness_check.py
```

1. 验证 token scope 和 Zenodo/API 状态，不打印任何 token。
2. 更新 author metadata、Data Availability、DOI 和 GitHub release 信息。
3. push 当前分支，创建 frozen release/tag。
4. public clean-clone 复现，并重跑 `pytest`、`ruff`、release audit、final blocker report。
5. 刷新 live Gantt、IF20-50 distance report 和 final GO/NO-GO。

## 边界

这个行动包解决投稿基础设施和作者事实卡点。它会提高 20-50 IF 投稿可防御性，但不保证任何期刊接收。
