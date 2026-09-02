from __future__ import annotations

from abc import ABC, abstractmethod
from typing import BinaryIO


class StorageBackend(ABC):
    """Swap local disk for Cloudflare R2 by changing STORAGE_BACKEND=r2.

    Callers only ever see storage keys (e.g. artwork/shows/<id>/poster.jpg).
    Public URLs are derived by `url()`.
    """

    @abstractmethod
    def put(self, key: str, data: bytes, content_type: str) -> str:
        """Write bytes at key. Returns the key."""

    @abstractmethod
    def put_file(self, key: str, fileobj: BinaryIO, content_type: str) -> str:
        ...

    @abstractmethod
    def get(self, key: str) -> bytes:
        ...

    @abstractmethod
    def exists(self, key: str) -> bool:
        ...

    @abstractmethod
    def url(self, key: str) -> str:
        """Browser-reachable URL for this key."""

    @abstractmethod
    def delete(self, key: str) -> None:
        ...

    @abstractmethod
    def atomic_put_json(self, live_key: str, version_key: str, payload: bytes) -> None:
        """Write version_key first, then atomically replace live_key.

        Readers of live_key must never observe a partial file.
        """
