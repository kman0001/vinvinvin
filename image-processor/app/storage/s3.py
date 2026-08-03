import os
from pathlib import Path
from app.storage.base import Storage


class S3Storage(Storage):
    """S3-compatible storage for AWS S3 and Cloudflare R2."""

    def __init__(self, config, name="s3"):
        super().__init__(config)
        try:
            import boto3
        except ImportError as exc:
            raise ValueError("boto3 is required for S3/R2 storage") from exc

        self.bucket = config.get("bucket", "").strip()
        self.prefix = config.get("path", "").strip().strip("/")
        access_key = os.environ.get(config.get("access_key_env", ""), "").strip() or config.get("access_key", "").strip()
        secret_key = os.environ.get(config.get("secret_key_env", ""), "").strip() or config.get("secret_key", "").strip()
        if not self.bucket:
            raise ValueError(f"{name}.bucket is required")
        if not access_key or not secret_key:
            raise ValueError(f"{name} access credentials are required")

        kwargs = {
            "aws_access_key_id": access_key,
            "aws_secret_access_key": secret_key,
        }
        region = config.get("region", "").strip()
        endpoint = config.get("endpoint", "").strip()
        if region:
            kwargs["region_name"] = region
        if endpoint:
            kwargs["endpoint_url"] = endpoint
        self.client = boto3.client("s3", **kwargs)

    def _key(self, destination):
        return "/".join(part for part in (self.prefix, destination.strip("/")) if part)

    def upload(self, source: Path, destination: str):
        content_type = "image/webp" if destination.lower().endswith(".webp") else "image/jpeg"
        self.client.upload_file(
            str(source),
            self.bucket,
            self._key(destination),
            ExtraArgs={"ContentType": content_type},
        )

    def delete(self, destination: str):
        self.client.delete_object(Bucket=self.bucket, Key=self._key(destination))

    def exists(self, destination: str) -> bool:
        try:
            self.client.head_object(Bucket=self.bucket, Key=self._key(destination))
            return True
        except self.client.exceptions.ClientError as exc:
            if exc.response.get("ResponseMetadata", {}).get("HTTPStatusCode") == 404:
                return False
            raise
