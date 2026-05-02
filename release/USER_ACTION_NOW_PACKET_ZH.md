# SheafSignal 当前最短行动包

- Timestamp: `2026-05-03 07:56:50`
- Decision: `USER_ACTION_PACKET_READY_P0_BLOCKERS_REMAIN`
- P0 items: `4`
- P1 items: `1`

## 你现在只需要处理什么

1. 重新生成 GitHub token：必须包含 `repo` 和 `workflow` scopes，保存到 `D:/secrets/github_token.txt`。
2. 提供 Han Yan email，并确认额外 16 个联系人是否不是作者；如果是作者，需要给出最终 author order、affiliation 和 CRediT。
3. 确认 author declarations：equal contribution、CRediT、funding、COI、ethics/data-use、GitHub/Zenodo public release approval。
4. Zenodo：手动上传 `release/archives/sheafsignal_zenodo_upload.zip` 后给 DOI，或把 Zenodo API token 保存到 `D:/secrets/zenodo_token.txt`。
5. 把 external review bundle 发给外部 AI/同行评审，拿回意见。

## Action Table

| Priority | Item | Current status | What you do | What Codex does after | Validation |
|---|---|---|---|---|---|
| `P0` | GitHub token / gh login | `github_token_api=valid_missing_workflow_scope; gh=not_logged_in` | Create or update a GitHub classic token with repo and workflow scopes, save it to D:/secrets/github_token.txt, and do not paste it into chat. | Validate token scopes, authenticate GitHub tooling if possible, push the branch, then create the public release/tag after final gates pass. | `python scripts/check_external_release_authorization.py` |
| `P0` | Han Yan email and author contact consistency | `missing_current_author_email=1; extra_supplied_contacts=16` | Provide Han Yan email. Confirm whether the 16 supplied contacts not in the current author line are non-authors or should be added with author order/affiliations/CRediT. | Update author metadata templates, rerun contact reconciliation and author preflight, then regenerate submission metadata. | `python scripts/reconcile_author_contacts.py && python scripts/check_author_confirmation_preflight.py` |
| `P0` | Author-owned declarations | `blocking=2; pending=8` | Confirm final author order, equal-contribution wording, CRediT, funding, competing interests, ethics/data-use wording, and GitHub/Zenodo public-release approval. | Apply AUTHOR_CONFIRMATION_RESPONSE_TEMPLATE.tsv, update manuscript-facing statements, and rerun final blocker checks. | `python scripts/apply_author_confirmation_response.py --apply && python scripts/check_author_confirmation_preflight.py` |
| `P0` | Zenodo DOI | `token=missing; doi_placeholder=pending` | Either manually upload release/archives/sheafsignal_zenodo_upload.zip to Zenodo and give Codex the DOI, or save a Zenodo API token to D:/secrets/zenodo_token.txt. | Insert the real DOI into release metadata, Data Availability, and dataset manifest, then rebuild release archives and audits. | `python scripts/check_release_metadata_placeholders.py` |
| `P1` | External beta review return | `EXTERNAL_BETA_REVIEW_NO_RETURNED_REVIEWS` | Send the prepared external review bundle to 2-3 independent AI/human reviewers and return their comments. | Triage returned reviews into fixed, downgraded_by_design, or out_of_scope actions before final journal targeting. | `reviewer response matrix update` |

## 我拿到这些信息后会直接做什么

1. 验证 token scope 和 Zenodo/API 状态，不打印任何 token。
2. 更新 author metadata、Data Availability、DOI 和 GitHub release 信息。
3. push 当前分支，创建 frozen release/tag。
4. public clean-clone 复现，并重跑 `pytest`、`ruff`、release audit、final blocker report。
5. 刷新 live Gantt、IF20-50 distance report 和 final GO/NO-GO。

## 边界

这个行动包解决投稿基础设施和作者事实卡点。它会提高 20-50 IF 投稿可防御性，但不保证任何期刊接收。
