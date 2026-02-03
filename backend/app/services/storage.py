from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


class StorageError(RuntimeError):
    pass


@dataclass(frozen=True)
class StoredObject:
    url: str
    path: Path


class LocalMediaStorage:
    """Very small local object storage abstraction.

    Saves bytes under a configured media_root and returns a stable URL.

    This is a stand-in for S3/GCS; callers should treat returned URLs as opaque.
    """

    def __init__(self, media_root: str, media_base_url: str):
        self.media_root = Path(media_root)
        self.media_base_url = media_base_url.rstrip("/")

    def save_bytes(self, *, rel_path: str, content: bytes) -> StoredObject:
        if not rel_path or rel_path.startswith("/"):
            raise StorageError("rel_path must be a relative path")

        abs_path = (self.media_root / rel_path).resolve()
        # prevent path traversal
        if self.media_root.resolve() not in abs_path.parents and abs_path != self.media_root.resolve():
            raise StorageError("rel_path escapes media_root")

        abs_path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = abs_path.with_suffix(abs_path.suffix + ".tmp")
        tmp_path.write_bytes(content)
        os.replace(tmp_path, abs_path)

        url = f"{self.media_base_url}/{rel_path}"
        return StoredObject(url=url, path=abs_path)
