from __future__ import annotations

import pytest

from app.services.storage import LocalMediaStorage, StorageError


def test_save_bytes_writes_file_and_returns_url(tmp_path):
    storage = LocalMediaStorage(str(tmp_path), "http://example/media")
    stored = storage.save_bytes(rel_path="sessions/1/infographic.svg", content=b"hello")

    assert stored.path.exists()
    assert stored.path.read_bytes() == b"hello"
    assert stored.url == "http://example/media/sessions/1/infographic.svg"


@pytest.mark.parametrize(
    "rel_path",
    [
        "",  # empty
        "/abs.svg",  # absolute
        "../escape.svg",  # traversal
    ],
)
def test_save_bytes_rejects_bad_rel_paths(tmp_path, rel_path):
    storage = LocalMediaStorage(str(tmp_path), "http://example/media")
    with pytest.raises(StorageError):
        storage.save_bytes(rel_path=rel_path, content=b"x")
