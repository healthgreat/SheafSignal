# SheafSignal 投稿解锁交接单

- Decision: `SUBMISSION_EXTERNAL_ACTIONS_REQUIRED`
- P0 blockers: `3`
- P1 follow-up actions: `2`
- Boundary: 这是投稿基础设施和作者事实交接单，不是期刊接收保证。

## 你现在只需要处理的事

1. GitHub token 重新生成：勾选 `repo` 和 `workflow`，覆盖 `D:\secrets\github_token.txt`。
2. Zenodo：手动上传 `release/archives/sheafsignal_zenodo_upload.zip` 并给 DOI，或保存 token 到 `D:\secrets\zenodo_token.txt`。
3. 作者信息：补 Han Yan 邮箱、共同贡献准确写法、CRediT、funding、COI、ethics/data-use、GitHub/Zenodo 公开授权。
   推荐直接填写 `manuscript/submission_metadata/AUTHOR_CONFIRMATION_RESPONSE_TEMPLATE.tsv`。

## 我在你完成后会直接做的事

1. 验证 GitHub token scope，不打印 token 内容。
2. push 当前分支到公开 GitHub，创建 release tag。
3. 写回真实 Zenodo DOI 和 GitHub release metadata。
4. 从公开 GitHub clean clone，重跑 tests/audits。
5. 重新生成 final GO/NO-GO、IF20-50 distance report 和投稿包。
6. 运行 guarded post-unblock release pipeline：`python scripts/build_post_unblock_release_pipeline.py --doi <REAL_ZENODO_DOI> --execute`。

## Action Table

| Priority | Owner | Action item | Current status | User action | Codex after unblocked | Validation |
|---|---|---|---|---|---|---|
| `P0` | `user` | GitHub token needs workflow scope | `github_token_api=valid_missing_workflow_scope; github_cli_auth=not_logged_in` | Regenerate a GitHub classic token with repo and workflow scopes, then overwrite D:\secrets\github_token.txt. Do not paste the token into chat. | Validate scopes, push codex/sheafsignal-hardening-release to the public repo, create v0.1.0 tag/release, and record the release URL. | `python scripts/check_external_release_authorization.py` |
| `P0` | `user_or_codex_after_token` | Zenodo DOI minting | `zenodo_archive_sha256=pass; zenodo_token_file=pending` | Either upload release/archives/sheafsignal_zenodo_upload.zip manually to Zenodo and provide the DOI, or save a Zenodo API token to D:\secrets\zenodo_token.txt. | Insert the minted DOI into metadata/datasets.tsv, Data Availability, release metadata, and rerun placeholder/final blocker audits. | `python scripts/check_zenodo_upload_preflight.py` |
| `P0` | `authors` | Author-owned submission facts | `blocking=2; pending=8` | Provide Han Yan email, final equal-contribution wording, final author order, CRediT approval, funding statement, COI statement, ethics/data-use wording, and explicit GitHub/Zenodo public-release approval. | Update submission metadata templates, rerun author preflight, and regenerate final submission blocker report. | `python scripts/check_author_confirmation_preflight.py` |
| `P1` | `codex_after_public_release` | Public clean-clone reproduction | `release_blocking_gates=7` | No manual analysis needed after GitHub and Zenodo identifiers are real. | Clone the public repository into a fresh directory, install locked dependencies, run demo/tests/audits, and write clean-clone evidence. | `python -m pytest -q; python scripts/release_audit.py` |
| `P1` | `codex` | Submission-day journal metric and warning-list check | `pending_submission_day` | Pick the target journal route only after the final GO/NO-GO report is green. | Recheck latest JIF, CAS zone, and warning-list status for the chosen journal before submission. | `rerun journal metric audit immediately before submission` |

## 20-50 IF 解释边界

这些 P0 blocker 清除后，项目才进入正式 20-50 IF submission package 阶段。清除它们会提高可复现性和投稿合规性，但不能保证任何期刊接收。

## 已准备好的自动化链条

- `manuscript/submission_metadata/AUTHOR_CONFIRMATION_RESPONSE_TEMPLATE.tsv`
- `scripts/apply_author_confirmation_response.py`
- `release/POST_UNBLOCK_RELEASE_PIPELINE_PLAN.tsv`
- `release/POST_UNBLOCK_RELEASE_PIPELINE_REPORT.md`

默认命令只生成计划，不执行外部发布：

```bash
python scripts/build_post_unblock_release_pipeline.py
```

只有 GitHub、Zenodo、作者确认都解除后，才允许显式执行：

```bash
python scripts/build_post_unblock_release_pipeline.py --doi <REAL_ZENODO_DOI> --execute
```
