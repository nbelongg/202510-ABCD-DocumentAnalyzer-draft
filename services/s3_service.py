"""S3 service for file storage"""
from typing import Optional
import boto3
from botocore.exceptions import ClientError
from io import BytesIO
from config.settings import settings
from services.logger import get_logger
from services.exceptions import StorageError

logger = get_logger(__name__)


class S3Service:
    """Service for AWS S3 operations"""
    
    def __init__(self):
        """Initialize S3 client"""
        try:
            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                region_name=settings.AWS_REGION
            )
            self.bucket_name = settings.S3_BUCKET_NAME
            
            logger.info("s3_client_initialized", bucket=self.bucket_name)
        except Exception as e:
            logger.error("s3_initialization_failed", error=str(e))
            raise StorageError(f"Failed to initialize S3 client: {str(e)}")
    
    def upload_file(
        self,
        file_data: BytesIO,
        file_key: str,
        content_type: Optional[str] = None,
        make_public: bool = True
    ) -> str:
        """
        Upload file to S3
        
        Args:
            file_data: File data as BytesIO
            file_key: S3 key (path) for the file
            content_type: Content type (e.g., 'application/pdf')
            make_public: Make file publicly accessible
            
        Returns:
            S3 URL of uploaded file
        """
        try:
            extra_args = {}
            if content_type:
                extra_args['ContentType'] = content_type
            if make_public:
                extra_args['ACL'] = 'public-read'
            
            logger.info("uploading_to_s3", file_key=file_key)
            
            self.s3_client.upload_fileobj(
                file_data,
                self.bucket_name,
                file_key,
                ExtraArgs=extra_args
            )
            
            url = f"https://{self.bucket_name}.s3.{settings.AWS_REGION}.amazonaws.com/{file_key}"
            
            logger.info("s3_upload_success", url=url)
            return url
            
        except ClientError as e:
            logger.error("s3_upload_failed", error=str(e), file_key=file_key)
            raise StorageError(f"S3 upload failed: {str(e)}")
    
    def download_file(self, file_key: str) -> BytesIO:
        """
        Download file from S3
        
        Args:
            file_key: S3 key of the file
            
        Returns:
            File data as BytesIO
        """
        try:
            logger.info("downloading_from_s3", file_key=file_key)
            
            file_obj = BytesIO()
            self.s3_client.download_fileobj(
                self.bucket_name,
                file_key,
                file_obj
            )
            file_obj.seek(0)
            
            logger.info("s3_download_success", file_key=file_key)
            return file_obj
            
        except ClientError as e:
            logger.error("s3_download_failed", error=str(e), file_key=file_key)
            raise StorageError(f"S3 download failed: {str(e)}")
    
    def delete_file(self, file_key: str) -> None:
        """
        Delete file from S3
        
        Args:
            file_key: S3 key of the file to delete
        """
        try:
            logger.info("deleting_from_s3", file_key=file_key)
            
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=file_key
            )
            
            logger.info("s3_delete_success", file_key=file_key)
            
        except ClientError as e:
            logger.error("s3_delete_failed", error=str(e), file_key=file_key)
            raise StorageError(f"S3 delete failed: {str(e)}")
    
    def generate_presigned_url(
        self,
        file_key: str,
        expiration: int = 3600
    ) -> str:
        """
        Generate presigned URL for temporary access
        
        Args:
            file_key: S3 key of the file
            expiration: URL expiration time in seconds
            
        Returns:
            Presigned URL
        """
        try:
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.bucket_name, 'Key': file_key},
                ExpiresIn=expiration
            )
            
            logger.info("presigned_url_generated", file_key=file_key)
            return url
            
        except ClientError as e:
            logger.error("presigned_url_failed", error=str(e), file_key=file_key)
            raise StorageError(f"Failed to generate presigned URL: {str(e)}")

