from pathlib import Path
import importlib.util
import json


def _load_script():
    root = Path(__file__).resolve().parents[1]
    path = root / "scripts" / "upload_zenodo_deposition.py"
    spec = importlib.util.spec_from_file_location("upload_zenodo_deposition", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class FakeZenodoClient:
    def __init__(self) -> None:
        self.calls = []

    def create_deposition(self):
        self.calls.append("create")
        return {
            "id": 123,
            "links": {
                "bucket": "https://zenodo.org/api/files/fake-bucket",
                "html": "https://zenodo.org/deposit/123",
            },
            "metadata": {"prereserve_doi": {"doi": "10.5281/zenodo.123"}},
        }

    def update_metadata(self, deposition_id, metadata):
        self.calls.append(("metadata", deposition_id, metadata["title"]))
        return {
            "id": deposition_id,
            "links": {"html": "https://zenodo.org/deposit/123"},
            "metadata": {"prereserve_doi": {"doi": "10.5281/zenodo.123"}},
        }

    def upload_file(self, bucket_url, file_path):
        self.calls.append(("upload", bucket_url, file_path.name))
        return {"filename": file_path.name}

    def publish(self, deposition_id):
        self.calls.append(("publish", deposition_id))
        return {
            "id": deposition_id,
            "doi": "10.5281/zenodo.123",
            "links": {"html": "https://zenodo.org/records/123"},
        }


def _write_metadata(path: Path, *, tbd: bool = False) -> None:
    metadata = {
        "title": "SheafSignal test",
        "upload_type": "dataset",
        "description": "Test deposition",
        "creators": [{"name": "TBD" if tbd else "Doe, Jane"}],
        "license": "cc-by-4.0",
        "related_identifiers": [
            {
                "identifier": "https://github.com/example/SheafSignal",
                "relation": "isSupplementTo",
                "resource_type": "software",
            }
        ],
    }
    path.write_text(json.dumps(metadata), encoding="utf-8")


def test_validate_upload_inputs_rejects_tbd_metadata_for_publish(tmp_path):
    script = _load_script()
    archive = tmp_path / "upload.zip"
    metadata_path = tmp_path / "metadata.json"
    archive.write_bytes(b"zip")
    _write_metadata(metadata_path, tbd=True)
    metadata = script.load_metadata(metadata_path)

    issues = script.validate_upload_inputs(
        archive_path=archive,
        metadata_path=metadata_path,
        metadata=metadata,
        publish=True,
        allow_tbd_metadata=False,
    )

    assert any("TBD" in issue for issue in issues)


def test_dry_run_writes_summary_without_token_or_network(tmp_path):
    script = _load_script()
    archive = tmp_path / "upload.zip"
    metadata_path = tmp_path / "metadata.json"
    summary_json = tmp_path / "summary.json"
    summary_md = tmp_path / "summary.md"
    archive.write_bytes(b"zip")
    _write_metadata(metadata_path)

    summary = script.run_upload_workflow(
        root=tmp_path,
        client=None,
        base_url="https://zenodo.org",
        archive_path=archive,
        metadata_path=metadata_path,
        summary_json_path=summary_json,
        summary_md_path=summary_md,
        publish=False,
        confirm_publish=None,
        allow_tbd_metadata=False,
        dry_run=True,
        finalize_local=False,
    )

    assert summary["mode"] == "dry_run"
    assert summary_json.exists()
    assert summary_md.exists()


def test_draft_upload_uses_create_metadata_and_file_upload(tmp_path):
    script = _load_script()
    archive = tmp_path / "upload.zip"
    metadata_path = tmp_path / "metadata.json"
    summary_json = tmp_path / "summary.json"
    summary_md = tmp_path / "summary.md"
    archive.write_bytes(b"zip")
    _write_metadata(metadata_path)
    client = FakeZenodoClient()

    summary = script.run_upload_workflow(
        root=tmp_path,
        client=client,
        base_url="https://zenodo.org",
        archive_path=archive,
        metadata_path=metadata_path,
        summary_json_path=summary_json,
        summary_md_path=summary_md,
        publish=False,
        confirm_publish=None,
        allow_tbd_metadata=False,
        dry_run=False,
        finalize_local=False,
    )

    assert summary["mode"] == "draft_upload"
    assert summary["reserved_doi"] == "10.5281/zenodo.123"
    assert "create" in client.calls
    assert any(call[0] == "upload" for call in client.calls if isinstance(call, tuple))
    assert not any(call[0] == "publish" for call in client.calls if isinstance(call, tuple))


def test_publish_requires_explicit_confirmation(tmp_path):
    script = _load_script()
    archive = tmp_path / "upload.zip"
    metadata_path = tmp_path / "metadata.json"
    archive.write_bytes(b"zip")
    _write_metadata(metadata_path)

    try:
        script.run_upload_workflow(
            root=tmp_path,
            client=FakeZenodoClient(),
            base_url="https://zenodo.org",
            archive_path=archive,
            metadata_path=metadata_path,
            summary_json_path=tmp_path / "summary.json",
            summary_md_path=tmp_path / "summary.md",
            publish=True,
            confirm_publish=None,
            allow_tbd_metadata=False,
            dry_run=False,
            finalize_local=False,
        )
    except ValueError as exc:
        assert script.PUBLISH_CONFIRMATION in str(exc)
    else:
        raise AssertionError("publish without confirmation should fail")
