from __future__ import annotations

import os
from pathlib import Path
from typing import BinaryIO

from app.config import get_settings
from app.storage.base import StorageBackend


class LocalDiskStorage(StorageBackend):
    def __init__(self, root: Path | None = None, public_base: str | None = None):
        settings = get_settings()
        self.root = Path(root or settings.storage_local_path)
        self.public_base = (public_base or settings.public_base_url).rstrip("/")
        self.root.mkdir(parents=True, exist_ok=True)

    def _path(self, key: str) -> Path:
        # prevent path traversal
        key = key.lstrip("/")
        path = (self.root / key).resolve()
        if not str(path).startswith(str(self.root.resolve())):
            raise ValueError("Invalid storage key")
        return path

    def put(self, key: str, data: bytes, content_type: str) -> str:
        path = self._path(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(path.suffix + ".tmp")
        tmp.write_bytes(data)
        os.replace(tmp, path)
        return key

    def put_file(self, key: str, fileobj: BinaryIO, content_type: str) -> str:
        return self.put(key, fileobj.read(), content_type)

    def get(self, key: str) -> bytes:
        return self._path(key).read_bytes()

    def exists(self, key: str) -> bool:
        return self._path(key).exists()

    def url(self, key: str) -> str:
        return f"{self.public_base}/media/{key}"

    def delete(self, key: str) -> None:
        path = self._path(key)
        if path.exists():
            path.unlink()

    def atomic_put_json(self, live_key: str, version_key: str, payload: bytes) -> None:
        """Write the versioned file, then os.replace onto the live key.

        os.replace is atomic on POSIX when source and dest share a filesystem.
        If we crash after writing version_key but before replace, the live
        catalogue is unchanged. A later publish (or rollback) can pick it up.
        """
        self.put(version_key, payload, "application/json")
        live = self._path(live_key)
        version = self._path(version_key)
        live.parent.mkdir(parents=True, exist_ok=True)
        tmp = live.with_suffix(".json.tmp")
        tmp.write_bytes(version.read_bytes())
        os.replace(tmp, live)
