import aioboto3
from botocore.client import Config
from app.core.config import settings


class S3Client:
    def __init__(self):
        self.session = aioboto3.Session()
        self.config = Config(signature_version="s3v4")
        self.endpoint = settings.S3_ENDPOINT_URL
        self.access_key = settings.S3_ACCESS_KEY
        self.secret_key = settings.S3_SECRET_KEY
        self.bucket = settings.S3_BUCKET_NAME

    def get_client(self):
        return self.session.client(
            "s3",
            endpoint_url=self.endpoint,
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
            config=self.config,
            region_name="us-east-1",
        )

    async def upload_file(self, file_obj, object_name, content_type=None):
        extra_args = {}
        if content_type:
            extra_args["ContentType"] = content_type

        async with self.get_client() as s3:
            await s3.upload_fileobj(
                file_obj, self.bucket, object_name, ExtraArgs=extra_args
            )

    async def get_file_iterator(self, object_name):
        pass

    async def delete_file(self, object_name):
        async with self.get_client() as s3:
            await s3.delete_object(Bucket=self.bucket, Key=object_name)


s3_client = S3Client()
