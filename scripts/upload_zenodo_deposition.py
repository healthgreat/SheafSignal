#!/usr/bin/env python
"""Upload SheafSignal release archive to Zenodo through the REST API.

Author: SheafSignal contributors
Date: 2026-05-01
Purpose: create a Zenodo deposition draft, upload the frozen Zenodo archive,
optionally publish it, and finalize local DOI metadata after publication.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

from finalize_zenodo_doi import finalize_release, validate_doi


PUBLISH_CONFIRMATION = "I_UNDERSTAND_ZENODO_PUBLISH_IS_FINAL"
DEFAULT_ARCHIVE = "release/archives/sheafsignal_zenodo_upload.zip"
DEFAULT_METADATA = "release/zenodo_deposition_metadata.json"
DEFAULT_SUMMARY_JSON = "release/ZENODO_API_UPLOAD_SUMMARY.json"
DEFAULT_SUMMARY_MD = "release/ZENODO_API_UPLOAD_SUMMARY.md"


class ZenodoApiError(RuntimeError):
    """Raised when Zenodo API returns an error response."""


class ZenodoClient:
    """Minimal Zenodo REST API client using the standard library."""

    def __init__(self, *, base_url: str, token: str, timeout: int = 600) -> None:
        self.base_url = base_url.rstrip("/")
        self.token = token
        self.timeout = timeout

    def _request(
        self,
        method: str,
        url: str,
        *,
        payload: dict[str, Any] | None = None,
        file_path: Path | None = None,
    ) -> dict[str, Any]:
        headers = {"Authorization": f"Bearer {self.token}"}
        data: bytes | None = None
        if payload is not None:
            data = json.dumps(payload).encode("utf-8")
            headers["Content-Type"] = "application/json"
        if file_path is not None:
            data = file_path.read_bytes()
            headers["Content-Type"] = "application/octet-stream"
        request = Request(url, data=data, headers=headers, method=method)
        try:
            with urlopen(request, timeout=self.timeout) as response:
                text = response.read().decode("utf-8")
                return json.loads(text) if text else {}
        except HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            raise ZenodoApiError(f"Zenodo API HTTP {exc.code}: {body}") from exc
        except URLError as exc:
            raise ZenodoApiError(f"Zenodo API connection error: {exc}") from exc

    def create_deposition(self) -> dict[str, Any]:
        return self._request(
            "POST",
            f"{self.base_url}/api/deposit/depositions",
            payload={},
        )

    def get_deposition(self, deposition_id: int) -> dict[str, Any]:
        return self._request(
            "GET",
            f"{self.base_url}/api/deposit/depositions/{deposition_id}",
        )

    def update_metadata(self, deposition_id: int, metadata: dict[str, Any]) -> dict[str, Any]:
        return self._request(
            "PUT",
            f"{self.base_url}/api/deposit/depositions/{deposition_id}",
            payload={"metadata": metadata},
        )

    def upload_file(self, bucket_url: str, file_path: Path) -> dict[str, Any]:
        upload_url = f"{bucket_url.rstrip('/')}/{quote(file_path.name)}"
        return self._request("PUT", upload_url, file_path=file_path)

    def publish(self, deposition_id: int) -> dict[str, Any]:
        return self._request(
            "POST",
            f"{self.base_url}/api/deposit/depositions/{deposition_id}/actions/publish",
        )


def _write_text_atomic(path: Path, text: str) -> None:
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    tmp_path.write_text(text, encoding="utf-8")
    tmp_path.replace(path)


def _write_json_atomic(path: Path, payload: dict[str, Any]) -> None:
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    tmp_path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    tmp_path.replace(path)


def load_metadata(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def metadata_tbd_issues(metadata: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    creators = metadata.get("creators", [])
    if not creators:
        issues.append("metadata.creators is empty")
    for idx, creator in enumerate(creators):
        name = str(creator.get("name", "")).strip()
        if not name or name.upper() == "TBD":
            issues.append(f"metadata.creators[{idx}].name is TBD")
    serialized = json.dumps(metadata, ensure_ascii=False)
    if "github.com/TBD" in serialized:
        issues.append("metadata.related_identifiers contains GitHub TBD URL")
    return issues


def validate_upload_inputs(
    *,
    archive_path: Path,
    metadata_path: Path,
    metadata: dict[str, Any],
    publish: bool,
    allow_tbd_metadata: bool,
) -> list[str]:
    issues: list[str] = []
    if not archive_path.exists():
        issues.append(f"archive missing: {archive_path}")
    if not metadata_path.exists():
        issues.append(f"metadata missing: {metadata_path}")
    tbd_issues = metadata_tbd_issues(metadata)
    if tbd_issues and (publish or not allow_tbd_metadata):
        issues.extend(tbd_issues)
    if publish and allow_tbd_metadata and tbd_issues:
        issues.extend(tbd_issues)
    return issues


def extract_doi(response: dict[str, Any]) -> str | None:
    candidates = [
        response.get("doi"),
        response.get("metadata", {}).get("doi")
        if isinstance(response.get("metadata"), dict)
        else None,
        response.get("metadata", {}).get("prereserve_doi", {}).get("doi")
        if isinstance(response.get("metadata"), dict)
        and isinstance(response.get("metadata", {}).get("prereserve_doi"), dict)
        else None,
    ]
    for candidate in candidates:
        if not candidate:
            continue
        try:
            return validate_doi(str(candidate))
        except ValueError:
            continue
    links = response.get("links", {})
    if isinstance(links, dict):
        doi_url = links.get("doi")
        if doi_url:
            try:
                return validate_doi(str(doi_url))
            except ValueError:
                return None
    return None


def build_summary_markdown(summary: dict[str, Any]) -> str:
    lines = [
        "# Zenodo API Upload Summary",
        "",
        f"- Mode: `{summary['mode']}`",
        f"- Base URL: `{summary['base_url']}`",
        f"- Archive: `{summary['archive_path']}`",
        f"- Metadata: `{summary['metadata_path']}`",
        f"- Deposition ID: `{summary.get('deposition_id', 'NA')}`",
        f"- Reserved DOI: `{summary.get('reserved_doi', 'NA')}`",
        f"- Published DOI: `{summary.get('published_doi', 'NA')}`",
        f"- HTML link: `{summary.get('html_link', 'NA')}`",
        "",
        "## Boundary",
        "",
        "This file never stores the Zenodo access token. Publishing a Zenodo record",
        "is irreversible through the normal deposit workflow; only use `--publish`",
        f"with `--confirm-publish {PUBLISH_CONFIRMATION}` after metadata review.",
        "",
    ]
    return "\n".join(lines)


def run_upload_workflow(
    *,
    root: Path,
    client: ZenodoClient | None,
    base_url: str,
    archive_path: Path,
    metadata_path: Path,
    summary_json_path: Path,
    summary_md_path: Path,
    publish: bool,
    confirm_publish: str | None,
    allow_tbd_metadata: bool,
    dry_run: bool,
    finalize_local: bool,
    existing_deposition_id: int | None = None,
) -> dict[str, Any]:
    metadata = load_metadata(metadata_path)
    issues = validate_upload_inputs(
        archive_path=archive_path,
        metadata_path=metadata_path,
        metadata=metadata,
        publish=publish,
        allow_tbd_metadata=allow_tbd_metadata,
    )
    if publish and confirm_publish != PUBLISH_CONFIRMATION:
        issues.append(f"publish requires --confirm-publish {PUBLISH_CONFIRMATION}")
    if issues:
        raise ValueError("Zenodo upload input validation failed: " + "; ".join(issues))

    summary: dict[str, Any] = {
        "mode": "dry_run" if dry_run else "publish" if publish else "draft_upload",
        "base_url": base_url,
        "archive_path": archive_path.relative_to(root).as_posix(),
        "metadata_path": metadata_path.relative_to(root).as_posix(),
        "archive_size_bytes": archive_path.stat().st_size,
        "metadata_tbd_issues": metadata_tbd_issues(metadata),
        "deposition_id": "NA",
        "existing_deposition_id": existing_deposition_id or "NA",
        "reserved_doi": "NA",
        "published_doi": "NA",
        "html_link": "NA",
        "finalized_local_metadata": False,
    }
    if dry_run:
        _write_json_atomic(summary_json_path, summary)
        _write_text_atomic(summary_md_path, build_summary_markdown(summary))
        return summary
    if client is None:
        raise ValueError("Zenodo client is required when dry_run is false")

    deposition = (
        client.get_deposition(existing_deposition_id)
        if existing_deposition_id is not None
        else client.create_deposition()
    )
    deposition_id = int(deposition["id"])
    bucket_url = deposition["links"]["bucket"]
    metadata_response = client.update_metadata(deposition_id, metadata)
    file_response = client.upload_file(bucket_url, archive_path)
    reserved_doi = extract_doi(metadata_response) or extract_doi(deposition)
    summary.update(
        {
            "deposition_id": deposition_id,
            "reused_existing_deposition": existing_deposition_id is not None,
            "reserved_doi": reserved_doi or "NA",
            "html_link": metadata_response.get("links", {}).get(
                "html",
                deposition.get("links", {}).get("html", "NA"),
            ),
            "uploaded_file": file_response.get("filename", archive_path.name),
        }
    )
    if publish:
        published = client.publish(deposition_id)
        published_doi = extract_doi(published)
        if published_doi is None:
            raise ZenodoApiError("Published deposition did not return a DOI")
        summary["published_doi"] = published_doi
        summary["html_link"] = published.get("links", {}).get(
            "html",
            summary["html_link"],
        )
        if finalize_local:
            finalize_release(root, published_doi)
            summary["finalized_local_metadata"] = True

    _write_json_atomic(summary_json_path, summary)
    _write_text_atomic(summary_md_path, build_summary_markdown(summary))
    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--archive", default=DEFAULT_ARCHIVE)
    parser.add_argument("--metadata", default=DEFAULT_METADATA)
    parser.add_argument("--summary-json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--summary-md", default=DEFAULT_SUMMARY_MD)
    parser.add_argument("--token-env", default="ZENODO_ACCESS_TOKEN")
    parser.add_argument("--timeout", type=int, default=600)
    parser.add_argument("--existing-deposition-id", type=int)
    parser.add_argument("--sandbox", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--publish", action="store_true")
    parser.add_argument("--confirm-publish")
    parser.add_argument("--allow-tbd-metadata", action="store_true")
    parser.add_argument(
        "--no-finalize-local",
        action="store_true",
        help="Do not write the published DOI back to local project files.",
    )
    args = parser.parse_args(argv)

    root = Path(args.root).resolve()
    base_url = "https://sandbox.zenodo.org" if args.sandbox else "https://zenodo.org"
    archive_path = root / args.archive
    metadata_path = root / args.metadata
    summary_json_path = root / args.summary_json
    summary_md_path = root / args.summary_md
    token = os.environ.get(args.token_env, "")
    if not args.dry_run and not token:
        raise SystemExit(
            f"Environment variable {args.token_env} is not set. "
            "Create a Zenodo token and set it before uploading."
        )
    client = None if args.dry_run else ZenodoClient(
        base_url=base_url,
        token=token,
        timeout=args.timeout,
    )
    summary = run_upload_workflow(
        root=root,
        client=client,
        base_url=base_url,
        archive_path=archive_path,
        metadata_path=metadata_path,
        summary_json_path=summary_json_path,
        summary_md_path=summary_md_path,
        publish=args.publish,
        confirm_publish=args.confirm_publish,
        allow_tbd_metadata=args.allow_tbd_metadata,
        dry_run=args.dry_run,
        finalize_local=not args.no_finalize_local,
        existing_deposition_id=args.existing_deposition_id,
    )
    print(f"wrote {summary_json_path}")
    print(f"wrote {summary_md_path}")
    print(f"mode: {summary['mode']}")
    print(f"reserved DOI: {summary.get('reserved_doi', 'NA')}")
    print(f"published DOI: {summary.get('published_doi', 'NA')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
