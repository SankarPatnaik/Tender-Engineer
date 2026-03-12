import os
import boto3
import logging
from datetime import datetime
from typing import Optional, Dict, Any
from botocore.exceptions import ClientError, NoCredentialsError
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

class S3TenderStorage:
    """Handle S3 operations for tender document storage"""
    
    def __init__(self):
        """Initialize S3 client with credentials from environment"""
        self.aws_access_key = os.getenv("AWS_ACCESS_KEY_ID")
        self.aws_secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")  
        self.aws_region = os.getenv("AWS_REGION", "us-east-1")
        self.bucket_name = os.getenv("TENDER_S3_BUCKET_NAME")
        
        # Validate required environment variables
        if not all([self.aws_access_key, self.aws_secret_key, self.bucket_name]):
            raise ValueError("Missing required S3 environment variables. Check AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, and TENDER_S3_BUCKET_NAME")
        
        # Initialize S3 client
        try:
            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=self.aws_access_key,
                aws_secret_access_key=self.aws_secret_key,
                region_name=self.aws_region
            )
            logger.info(f"✅ S3 client initialized for bucket: {self.bucket_name}")
        except NoCredentialsError:
            logger.error("❌ AWS credentials not found")
            raise
        except Exception as e:
            logger.error(f"❌ Error initializing S3 client: {e}")
            raise
    
    def upload_tender_document(self, local_file_path: str, original_filename: str) -> Optional[Dict[str, Any]]:
        """
        Upload tender document to S3 bucket
        
        Args:
            local_file_path (str): Path to the local file to upload
            original_filename (str): Original filename from upload
            
        Returns:
            Dict with upload details or None if failed
        """
        try:
            # Validate file exists
            if not os.path.exists(local_file_path):
                logger.error(f"❌ File not found: {local_file_path}")
                return None
            
            # Generate S3 key with timestamp and original filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_extension = os.path.splitext(original_filename)[1]
            sanitized_name = "".join(c for c in os.path.splitext(original_filename)[0] if c.isalnum() or c in (' ', '-', '_')).rstrip()
            s3_key = f"tender_documents/{timestamp}_{sanitized_name}{file_extension}"
            
            # Get file size
            file_size = os.path.getsize(local_file_path)
            
            # Upload file to S3
            logger.info(f"📤 Uploading {original_filename} to S3...")
            self.s3_client.upload_file(
                local_file_path,
                self.bucket_name, 
                s3_key,
                ExtraArgs={
                    'Metadata': {
                        'original_filename': original_filename,
                        'upload_timestamp': timestamp,
                        'file_size': str(file_size)
                    }
                }
            )
            
            # Generate S3 URL
            s3_url = f"s3://{self.bucket_name}/{s3_key}"
            
            logger.info(f"✅ Successfully uploaded to: {s3_url}")
            
            return {
                "s3_bucket": self.bucket_name,
                "s3_key": s3_key,
                "s3_url": s3_url,
                "original_filename": original_filename,
                "file_size": file_size,
                "upload_timestamp": timestamp,
                "upload_date": datetime.now().isoformat()
            }
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            logger.error(f"❌ AWS S3 Error ({error_code}): {e}")
            return None
        except Exception as e:
            logger.error(f"❌ Error uploading file: {e}")
            return None
    
    def download_tender_document(self, s3_key: str, local_download_path: str) -> bool:
        """
        Download tender document from S3
        
        Args:
            s3_key (str): S3 key of the file to download
            local_download_path (str): Local path where file should be saved
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            logger.info(f"📥 Downloading {s3_key} from S3...")
            
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(local_download_path), exist_ok=True)
            
            # Download file
            self.s3_client.download_file(
                self.bucket_name,
                s3_key,
                local_download_path
            )
            
            logger.info(f"✅ Successfully downloaded to: {local_download_path}")
            return True
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'NoSuchKey':
                logger.error(f"❌ File not found in S3: {s3_key}")
            else:
                logger.error(f"❌ AWS S3 Error ({error_code}): {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Error downloading file: {e}")
            return False
    
    def check_file_exists(self, s3_key: str) -> bool:
        """
        Check if file exists in S3
        
        Args:
            s3_key (str): S3 key to check
            
        Returns:
            bool: True if file exists, False otherwise
        """
        try:
            self.s3_client.head_object(Bucket=self.bucket_name, Key=s3_key)
            return True
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                return False
            else:
                logger.error(f"❌ Error checking file existence: {e}")
                return False
    
    def get_file_metadata(self, s3_key: str) -> Optional[Dict[str, Any]]:
        """
        Get metadata for a file in S3
        
        Args:
            s3_key (str): S3 key of the file
            
        Returns:
            Dict with file metadata or None if failed
        """
        try:
            response = self.s3_client.head_object(Bucket=self.bucket_name, Key=s3_key)
            
            return {
                "s3_key": s3_key,
                "file_size": response.get('ContentLength', 0),
                "last_modified": response.get('LastModified').isoformat() if response.get('LastModified') else None,
                "content_type": response.get('ContentType', ''),
                "metadata": response.get('Metadata', {})
            }
            
        except ClientError as e:
            logger.error(f"❌ Error getting file metadata: {e}")
            return None
    
    def delete_tender_document(self, s3_key: str) -> bool:
        """
        Delete tender document from S3
        
        Args:
            s3_key (str): S3 key of the file to delete
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            logger.info(f"🗑️ Deleting {s3_key} from S3...")
            
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=s3_key
            )
            
            logger.info(f"✅ Successfully deleted: {s3_key}")
            return True
            
        except ClientError as e:
            logger.error(f"❌ Error deleting file: {e}")
            return False

# Convenience functions for easy imports
def upload_tender_to_s3(file_path: str, original_filename: str) -> Optional[Dict[str, Any]]:
    """
    Convenience function to upload tender document to S3
    
    Args:
        file_path (str): Local file path
        original_filename (str): Original filename
        
    Returns:
        Dict with upload details or None if failed
    """
    try:
        s3_storage = S3TenderStorage()
        return s3_storage.upload_tender_document(file_path, original_filename)
    except Exception as e:
        logger.error(f"❌ Error in upload_tender_to_s3: {e}")
        return None

def download_tender_from_s3(s3_key: str, local_path: str) -> bool:
    """
    Convenience function to download tender document from S3
    
    Args:
        s3_key (str): S3 key
        local_path (str): Local download path
        
    Returns:
        bool: Success status
    """
    try:
        s3_storage = S3TenderStorage()
        return s3_storage.download_tender_document(s3_key, local_path)
    except Exception as e:
        logger.error(f"❌ Error in download_tender_from_s3: {e}")
        return False

# Test function
def test_s3_connection():
    """Test S3 connection and bucket access"""
    try:
        s3_storage = S3TenderStorage()
        
        # Test connection by listing bucket (limited to 1 object)
        response = s3_storage.s3_client.list_objects_v2(
            Bucket=s3_storage.bucket_name,
            MaxKeys=1
        )
        
        logger.info(f"✅ S3 connection successful. Bucket: {s3_storage.bucket_name}")
        logger.info(f"📊 Bucket contains {response.get('KeyCount', 0)} objects")
        return True
        
    except Exception as e:
        logger.error(f"❌ S3 connection test failed: {e}")
        return False

if __name__ == "__main__":
    # Test the S3 connection
    print("🧪 Testing S3 connection...")
    test_s3_connection()