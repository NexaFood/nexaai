"""
AWS S3 storage service for file uploads and management.
"""
import boto3
from botocore.exceptions import ClientError
from django.conf import settings
import logging
import os
from uuid import uuid4

logger = logging.getLogger(__name__)


class S3Client:
    """Client for AWS S3 operations."""
    
    def __init__(self):
        """Initialize S3 client with AWS credentials from settings."""
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_S3_REGION_NAME
        )
        self.bucket_name = settings.AWS_STORAGE_BUCKET_NAME
    
    def upload_file(self, file_path, s3_key, content_type=None):
        """
        Upload a file to S3.
        
        Args:
            file_path: Local file path
            s3_key: S3 object key (path in bucket)
            content_type: MIME type of the file
        
        Returns:
            str: Public URL of uploaded file
        """
        try:
            extra_args = {}
            if content_type:
                extra_args['ContentType'] = content_type
            
            self.s3_client.upload_file(
                file_path,
                self.bucket_name,
                s3_key,
                ExtraArgs=extra_args
            )
            
            # Generate public URL
            if settings.AWS_S3_CUSTOM_DOMAIN:
                url = f"https://{settings.AWS_S3_CUSTOM_DOMAIN}/{s3_key}"
            else:
                url = f"https://{self.bucket_name}.s3.{settings.AWS_S3_REGION_NAME}.amazonaws.com/{s3_key}"
            
            logger.info(f"Uploaded file to S3: {s3_key}")
            return url
        
        except ClientError as e:
            logger.error(f"Failed to upload file to S3: {e}")
            raise Exception(f"S3 upload error: {str(e)}")
    
    def upload_file_object(self, file_obj, s3_key, content_type=None):
        """
        Upload a file object to S3.
        
        Args:
            file_obj: File-like object
            s3_key: S3 object key
            content_type: MIME type
        
        Returns:
            str: Public URL of uploaded file
        """
        try:
            extra_args = {}
            if content_type:
                extra_args['ContentType'] = content_type
            
            self.s3_client.upload_fileobj(
                file_obj,
                self.bucket_name,
                s3_key,
                ExtraArgs=extra_args
            )
            
            # Generate public URL
            if settings.AWS_S3_CUSTOM_DOMAIN:
                url = f"https://{settings.AWS_S3_CUSTOM_DOMAIN}/{s3_key}"
            else:
                url = f"https://{self.bucket_name}.s3.{settings.AWS_S3_REGION_NAME}.amazonaws.com/{s3_key}"
            
            logger.info(f"Uploaded file object to S3: {s3_key}")
            return url
        
        except ClientError as e:
            logger.error(f"Failed to upload file object to S3: {e}")
            raise Exception(f"S3 upload error: {str(e)}")
    
    def delete_file(self, s3_key):
        """
        Delete a file from S3.
        
        Args:
            s3_key: S3 object key to delete
        
        Returns:
            bool: True if successful
        """
        try:
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=s3_key
            )
            logger.info(f"Deleted file from S3: {s3_key}")
            return True
        
        except ClientError as e:
            logger.error(f"Failed to delete file from S3: {e}")
            return False
    
    def generate_presigned_url(self, s3_key, expiration=3600):
        """
        Generate a presigned URL for temporary access.
        
        Args:
            s3_key: S3 object key
            expiration: URL expiration time in seconds
        
        Returns:
            str: Presigned URL
        """
        try:
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': self.bucket_name,
                    'Key': s3_key
                },
                ExpiresIn=expiration
            )
            return url
        
        except ClientError as e:
            logger.error(f"Failed to generate presigned URL: {e}")
            raise Exception(f"S3 error: {str(e)}")


def upload_to_s3(file_path, folder='models', filename=None):
    """
    Helper function to upload a file to S3.
    
    Args:
        file_path: Local file path
        folder: S3 folder/prefix
        filename: Custom filename (auto-generated if not provided)
    
    Returns:
        tuple: (s3_key, public_url)
    """
    if not filename:
        ext = os.path.splitext(file_path)[1]
        filename = f"{uuid4()}{ext}"
    
    s3_key = f"{folder}/{filename}"
    
    # Determine content type
    content_type = None
    if file_path.endswith('.glb'):
        content_type = 'model/gltf-binary'
    elif file_path.endswith('.obj'):
        content_type = 'model/obj'
    elif file_path.endswith('.fbx'):
        content_type = 'application/octet-stream'
    elif file_path.endswith('.usdz'):
        content_type = 'model/vnd.usdz+zip'
    
    client = S3Client()
    url = client.upload_file(file_path, s3_key, content_type)
    
    return s3_key, url


def delete_from_s3(s3_key):
    """
    Helper function to delete a file from S3.
    
    Args:
        s3_key: S3 object key
    
    Returns:
        bool: True if successful
    """
    client = S3Client()
    return client.delete_file(s3_key)
