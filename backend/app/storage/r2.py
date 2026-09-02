from __future__ import annotations

from typing import BinaryIO

import boto3
from botocore.config import Config

from app.config import get_settings
from app.storage.base import StorageBackend


class R2Storage(StorageBackend):
    """Cloudflare R2 via the S3 API.

    To switch from local disk: set STORAGE_BACKEND=r2 and the R2_* env vars.
    Nothing in the routers changes — they only talk to StorageBackend.
    """

    def __init__(self):
        s = get_settings()
        if not s.r2_account_id or not s.r2_access_key_id:
            raise RuntimeError("R2 storage selected but R2 credentials are missing.")
        endpoint = f"https://{s.r2_account_id}.r2.cloudflarestorage.com"
        self.client = boto3.client(
            "s3",
            endpoint_url=endpoint,
            aws_access_key_id=s.r2_access_key_id,
            aws_secret_access_key=s.r2_secret_access_key,
            config=Config(signature_version="s3v4"),
            region_name="auto",
        )
        self.bucket = s.r2_bucket
        self.public_base = s.r2_public_base_url.rstrip("/")

    def put(self, key: str, data: bytes, content_type: str) -> str:
        self.client.put_object(Bucket=self.bucket, Key=key, Body=data, ContentType=content_type)
        return key

    def put_file(self, key: str, fileobj: BinaryIO, content_type: str) -> str:
        self.client.upload_fileobj(
            fileobj, self.bucket, key, ExtraArgs={"ContentType": content_type}
        )
        return key

    def get(self, key: str) -> bytes:
        obj = self.client.get_object(Bucket=self.bucket, Key=key)
        return obj["Body"].read()

    def exists(self, key: str) -> bool:
        try:
            self.client.head_object(Bucket=self.bucket, Key=key)
            return True
        except Exception:
            return False

    def url(self, key: str) -> str:
        if self.public_base:
            return f"{self.public_base}/{key}"
        return f"https://{self.bucket}/{key}"

    def delete(self, key: str) -> None:
        self.client.delete_object(Bucket=self.bucket, Key=key)

    def atomic_put_json(self, live_key: str, version_key: str, payload: bytes) -> None:
        """R2/S3 PUTs are atomic per key (a GET never sees a partial object).

        We still write the versioned object first, then overwrite the live key
        in a second PUT. There is no cross-key rename; a crash between the two
        leaves live pointing at the previous complete object.
        """
        self.put(version_key, payload, "application/json")
        self.put(live_key, payload, "application/json")
