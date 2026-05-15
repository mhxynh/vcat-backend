import boto3
from botocore.config import Config

_S3_CLIENT = None


class S3Utils:
    @staticmethod
    def is_s3_event(event):
        if not isinstance(event, dict):
            return False

        records = event.get("Records") or []
        if not records:
            return False

        first_record = records[0] or {}
        return first_record.get("eventSource") == "aws:s3"

    @staticmethod
    def get_client():
        global _S3_CLIENT

        if _S3_CLIENT is None:
            _S3_CLIENT = boto3.client("s3", config=Config(signature_version="s3v4"))

        return _S3_CLIENT

    @staticmethod
    def get_object_bytes(bucket_name, object_key, max_file_size_mb=None):
        response = S3Utils.get_client().get_object(Bucket=bucket_name, Key=object_key)
        body = response["Body"]
        content_type = response.get("ContentType")
        content_length = response.get("ContentLength")

        if max_file_size_mb is not None and content_length is not None:
            max_file_size_bytes = int(max_file_size_mb) * 1024 * 1024
            if content_length > max_file_size_bytes:
                body.close()
                raise ValueError(
                    f"File exceeds the maximum supported size of {max_file_size_mb} MB"
                )

        try:
            body_bytes = body.read()
        finally:
            body.close()

        content_length = response.get("ContentLength", len(body_bytes))
        return body_bytes, content_type, content_length

    @staticmethod
    def get_file_from_s3(bucket_name, object_key, max_file_size_mb=None):
        body_bytes, content_type, content_length = S3Utils.get_object_bytes(
            bucket_name,
            object_key,
            max_file_size_mb=max_file_size_mb,
        )

        if max_file_size_mb is not None:
            max_file_size_bytes = int(max_file_size_mb) * 1024 * 1024
            if len(body_bytes) > max_file_size_bytes:
                raise ValueError(
                    f"File exceeds the maximum supported size of {max_file_size_mb} MB"
                )

        return body_bytes, content_type

    @staticmethod
    def generate_presigned_put_url(bucket_name, object_key, content_type, expires_in):
        return S3Utils.get_client().generate_presigned_url(
            "put_object",
            Params={
                "Bucket": bucket_name,
                "Key": object_key,
                "ContentType": content_type,
            },
            ExpiresIn=expires_in,
        )

    @staticmethod
    def generate_presigned_get_url(bucket_name, object_key, expires_in):
        return S3Utils.get_client().generate_presigned_url(
            "get_object",
            Params={
                "Bucket": bucket_name,
                "Key": object_key,
            },
            ExpiresIn=expires_in,
        )
