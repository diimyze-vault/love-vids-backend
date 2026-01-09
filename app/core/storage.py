import boto3
from botocore.config import Config
from app.core.config import settings
from typing import Optional

class StorageService:
    def __init__(self):
        self.s3 = None
        if all([settings.B2_KEY_ID, settings.B2_APPLICATION_KEY, settings.B2_ENDPOINT]):
            self.s3 = boto3.client(
                's3',
                endpoint_url=settings.B2_ENDPOINT,
                aws_access_key_id=settings.B2_KEY_ID,
                aws_secret_access_key=settings.B2_APPLICATION_KEY,
                config=Config(signature_version='s3v4'),
                region_name=settings.B2_REGION_NAME
            )

    def generate_presigned_url(self, object_name: str, expiration: int = 3600) -> Optional[str]:
        """
        Generate a presigned URL to share an S3 object (video download).
        """
        if not self.s3:
            return None
        try:
            response = self.s3.generate_presigned_url(
                'get_object',
                Params={'Bucket': settings.B2_BUCKET_NAME, 'Key': object_name},
                ExpiresIn=expiration
            )
            return response
        except Exception:
            return None

    def generate_upload_url(self, object_name: str, content_type: str, expiration: int = 3600) -> dict:
        """
        Generate a presigned URL for PUT uploading a file.
        """
        if not self.s3:
            raise Exception("Storage service not configured")
        
        try:
            url = self.s3.generate_presigned_url(
                'put_object',
                Params={
                    'Bucket': settings.B2_BUCKET_NAME,
                    'Key': object_name,
                    'ContentType': content_type
                },
                ExpiresIn=expiration
            )
            
            clean_endpoint = settings.B2_ENDPOINT.replace('https://', '')
            file_url = f"https://{settings.B2_BUCKET_NAME}.{clean_endpoint}/{object_name}"
            
            return {
                "url": url,
                "file_url": file_url
            }
        except Exception as e:
            raise e

    def upload_file(self, file_obj, object_name: str, content_type: str) -> str:
        """
        Upload a file directly from the backend to B2.
        """
        if not self.s3:
            raise Exception("Storage service not configured")
        
        try:
            self.s3.upload_fileobj(
                file_obj,
                settings.B2_BUCKET_NAME,
                object_name,
                ExtraArgs={'ContentType': content_type}
            )
            
            clean_endpoint = settings.B2_ENDPOINT.replace('https://', '')
            return f"https://{settings.B2_BUCKET_NAME}.{clean_endpoint}/{object_name}"
        except Exception as e:
            raise e

    def delete_file(self, object_name: str) -> bool:
        """
        Delete a file from B2.
        """
        if not self.s3:
            return False
        try:
            self.s3.delete_object(Bucket=settings.B2_BUCKET_NAME, Key=object_name)
            return True
        except Exception:
            return False

storage_service = StorageService()
