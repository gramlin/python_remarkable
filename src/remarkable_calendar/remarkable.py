from __future__ import annotations

from pathlib import Path

from rm_api import API, models


def _normalize_remote_dir(remote_dir: str | None) -> list[str]:
    if not remote_dir:
        return []
    return [part for part in remote_dir.split("/") if part]


def _find_or_create_remote_dir(api, remote_dir: str | None) -> str | None:
    parts = _normalize_remote_dir(remote_dir)
    if not parts:
        return None

    api.get_documents()
    parent_uuid: str | None = None
    for part in parts:
        matching = next(
            (
                collection
                for collection in api.document_collections.values()
                if collection.metadata.visible_name == part
                and (collection.parent or None) == parent_uuid
            ),
            None,
        )
        if matching is None:
            new_collection = models.DocumentCollection.create(api, part, parent_uuid)
            api.upload(new_collection)
            api.document_collections[new_collection.uuid] = new_collection
            parent_uuid = new_collection.uuid
        else:
            parent_uuid = matching.uuid
    return parent_uuid


def upload_pdf_with_rmapi(
    pdf_path: Path,
    remote_dir: str | None = None,
    token_file: str = "token",
    sync_dir: str = "sync",
    log_file: str = "rm_api.log",
) -> None:
    api = API(token_file_path=token_file, sync_file_path=sync_dir, log_file=log_file)
    parent_uuid = _find_or_create_remote_dir(api, remote_dir)
    pdf_data = pdf_path.read_bytes()
    document = models.Document.new_pdf(api, pdf_path.name, pdf_data, parent=parent_uuid)
    api.upload(document)
