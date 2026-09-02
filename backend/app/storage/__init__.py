from app.config import get_settings
from app.storage.base import StorageBackend
from app.storage.local import LocalDiskStorage
from app.storage.r2 import R2Storage

_storage: StorageBackend | None = None


def get_storage() -> StorageBackend:
    global _storage
    if _storage is None:
        backend = get_settings().storage_backend.lower()
        if backend == "r2":
            _storage = R2Storage()
        else:
            _storage = LocalDiskStorage()
    return _storage


def reset_storage() -> None:
    global _storage
    _storage = None
