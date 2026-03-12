import os
import logging
from datetime import datetime
from typing import Optional, Dict, Any, List
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, PyMongoError
from bson import ObjectId
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

class TenderMetadataManager:
    """Handle MongoDB operations for tender metadata storage"""
    
    def __init__(self):
        """Initialize MongoDB connection for tender metadata"""
        self.mongodb_uri = os.getenv("MONGODB_URI")
        self.mongodb_db = os.getenv("MONGODB_DB")
        self.tender_collection_name = os.getenv("TENDER_MONGODB_COLLECTION")
        
        # Validate required environment variables
        if not all([self.mongodb_uri, self.mongodb_db, self.tender_collection_name]):
            raise ValueError("Missing required MongoDB environment variables. Check MONGODB_URI, MONGODB_DB, and TENDER_MONGODB_COLLECTION")
        
        # Initialize MongoDB connection
        try:
            self.client = MongoClient(self.mongodb_uri)
            self.db = self.client[self.mongodb_db]
            self.collection = self.db[self.tender_collection_name]
            
            # Test connection
            self.client.admin.command('ping')
            logger.info(f"✅ Connected to MongoDB collection: {self.tender_collection_name}")
            
        except ConnectionFailure:
            logger.error("❌ Failed to connect to MongoDB")
            raise
        except Exception as e:
            logger.error(f"❌ Error initializing MongoDB connection: {e}")
            raise
    
    def save_tender_metadata(self, 
                           file_info: Dict[str, Any], 
                           s3_info: Dict[str, Any],
                           processing_status: str = "uploaded") -> Optional[str]:
        """
        Save tender metadata to MongoDB
        
        Args:
            file_info (Dict): Information about the original file
            s3_info (Dict): S3 storage information  
            processing_status (str): Current processing status
            
        Returns:
            str: MongoDB document ID if successful, None otherwise
        """
        try:
            # Create metadata document
            metadata_doc = {
                # File Information
                "original_filename": file_info.get("original_filename"),
                "file_size": file_info.get("file_size"),
                "file_type": file_info.get("file_type"),
                "file_extension": file_info.get("file_extension"),
                
                # S3 Information
                "s3_bucket": s3_info.get("s3_bucket"),
                "s3_key": s3_info.get("s3_key"),
                "s3_url": s3_info.get("s3_url"),
                "s3_upload_timestamp": s3_info.get("upload_timestamp"),
                
                # Processing Information
                "processing_status": processing_status,  # uploaded, processing, completed, failed
                "created_at": datetime.now(),
                "updated_at": datetime.now(),
                
                # Placeholder for future processing results
                "tender_data": None,
                "validation_results": None,
                "vendor_matches": None,
                "processing_logs": []
            }
            
            # Insert document
            result = self.collection.insert_one(metadata_doc)
            document_id = str(result.inserted_id)
            
            logger.info(f"✅ Tender metadata saved with ID: {document_id}")
            return document_id
            
        except PyMongoError as e:
            logger.error(f"❌ MongoDB error saving metadata: {e}")
            return None
        except Exception as e:
            logger.error(f"❌ Error saving tender metadata: {e}")
            return None
    
    def update_processing_status(self, document_id: str, status: str, additional_data: Optional[Dict] = None) -> bool:
        """
        Update processing status and optionally add additional data
        
        Args:
            document_id (str): MongoDB document ID
            status (str): New processing status
            additional_data (Dict, optional): Additional data to update
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            update_doc = {
                "processing_status": status,
                "updated_at": datetime.now()
            }
            
            # Add additional data if provided
            if additional_data:
                update_doc.update(additional_data)
            
            # Add processing log entry
            log_entry = {
                "timestamp": datetime.now(),
                "status": status,
                "message": f"Status updated to: {status}"
            }
            
            result = self.collection.update_one(
                {"_id": ObjectId(document_id)},
                {
                    "$set": update_doc,
                    "$push": {"processing_logs": log_entry}
                }
            )
            
            if result.modified_count > 0:
                logger.info(f"✅ Updated status to '{status}' for document: {document_id}")
                return True
            else:
                logger.warning(f"⚠️ No document found with ID: {document_id}")
                return False
                
        except PyMongoError as e:
            logger.error(f"❌ MongoDB error updating status: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Error updating processing status: {e}")
            return False
    
    def save_processing_results(self, document_id: str, 
                              tender_data: Optional[Dict] = None,
                              validation_results: Optional[Dict] = None,
                              vendor_matches: Optional[Dict] = None) -> bool:
        """
        Save processing results to the tender metadata document
        
        Args:
            document_id (str): MongoDB document ID
            tender_data (Dict, optional): Structured tender data
            validation_results (Dict, optional): Validation results
            vendor_matches (Dict, optional): Vendor matching results
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            update_doc = {
                "updated_at": datetime.now()
            }
            
            # Add results if provided
            if tender_data is not None:
                update_doc["tender_data"] = tender_data
            if validation_results is not None:
                update_doc["validation_results"] = validation_results
            if vendor_matches is not None:
                update_doc["vendor_matches"] = vendor_matches
            
            # Update processing status to completed if we have tender data
            if tender_data is not None:
                update_doc["processing_status"] = "completed"
            
            result = self.collection.update_one(
                {"_id": ObjectId(document_id)},
                {"$set": update_doc}
            )
            
            if result.modified_count > 0:
                logger.info(f"✅ Processing results saved for document: {document_id}")
                return True
            else:
                logger.warning(f"⚠️ No document found with ID: {document_id}")
                return False
                
        except PyMongoError as e:
            logger.error(f"❌ MongoDB error saving results: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Error saving processing results: {e}")
            return False
    
    def get_tender_metadata(self, document_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve tender metadata by document ID
        
        Args:
            document_id (str): MongoDB document ID
            
        Returns:
            Dict with tender metadata or None if not found
        """
        try:
            document = self.collection.find_one({"_id": ObjectId(document_id)})
            
            if document:
                # Convert ObjectId to string for JSON serialization
                document["_id"] = str(document["_id"])
                logger.info(f"✅ Retrieved metadata for document: {document_id}")
                return document
            else:
                logger.warning(f"⚠️ No document found with ID: {document_id}")
                return None
                
        except PyMongoError as e:
            logger.error(f"❌ MongoDB error retrieving metadata: {e}")
            return None
        except Exception as e:
            logger.error(f"❌ Error retrieving tender metadata: {e}")
            return None
    
    def list_tender_documents(self, status_filter: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """
        List tender documents with optional status filtering
        
        Args:
            status_filter (str, optional): Filter by processing status
            limit (int): Maximum number of documents to return
            
        Returns:
            List of tender metadata documents
        """
        try:
            # Build query
            query = {}
            if status_filter:
                query["processing_status"] = status_filter
            
            # Execute query with sorting (newest first)
            cursor = self.collection.find(query).sort("created_at", -1).limit(limit)
            documents = list(cursor)
            
            # Convert ObjectIds to strings
            for doc in documents:
                doc["_id"] = str(doc["_id"])
            
            logger.info(f"✅ Retrieved {len(documents)} tender documents")
            return documents
            
        except PyMongoError as e:
            logger.error(f"❌ MongoDB error listing documents: {e}")
            return []
        except Exception as e:
            logger.error(f"❌ Error listing tender documents: {e}")
            return []
    
    def delete_tender_metadata(self, document_id: str) -> bool:
        """
        Delete tender metadata document
        
        Args:
            document_id (str): MongoDB document ID
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            result = self.collection.delete_one({"_id": ObjectId(document_id)})
            
            if result.deleted_count > 0:
                logger.info(f"✅ Deleted tender metadata: {document_id}")
                return True
            else:
                logger.warning(f"⚠️ No document found with ID: {document_id}")
                return False
                
        except PyMongoError as e:
            logger.error(f"❌ MongoDB error deleting document: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Error deleting tender metadata: {e}")
            return False
    
    def get_processing_statistics(self) -> Dict[str, Any]:
        """
        Get processing statistics for tender documents
        
        Returns:
            Dict with processing statistics
        """
        try:
            # Aggregate processing status counts
            pipeline = [
                {"$group": {
                    "_id": "$processing_status",
                    "count": {"$sum": 1}
                }}
            ]
            
            status_counts = list(self.collection.aggregate(pipeline))
            
            # Get total count
            total_count = self.collection.count_documents({})
            
            # Format results
            stats = {
                "total_documents": total_count,
                "status_breakdown": {item["_id"]: item["count"] for item in status_counts},
                "generated_at": datetime.now().isoformat()
            }
            
            logger.info(f"✅ Generated processing statistics")
            return stats
            
        except PyMongoError as e:
            logger.error(f"❌ MongoDB error getting statistics: {e}")
            return {"error": str(e)}
        except Exception as e:
            logger.error(f"❌ Error getting processing statistics: {e}")
            return {"error": str(e)}

# Convenience functions for easy imports
def save_tender_upload_metadata(file_info: Dict, s3_info: Dict) -> Optional[str]:
    """
    Convenience function to save tender upload metadata
    
    Args:
        file_info (Dict): File information
        s3_info (Dict): S3 information
        
    Returns:
        str: Document ID if successful, None otherwise
    """
    try:
        metadata_manager = TenderMetadataManager()
        return metadata_manager.save_tender_metadata(file_info, s3_info)
    except Exception as e:
        logger.error(f"❌ Error in save_tender_upload_metadata: {e}")
        return None

def update_tender_status(document_id: str, status: str) -> bool:
    """
    Convenience function to update tender processing status
    
    Args:
        document_id (str): Document ID
        status (str): New status
        
    Returns:
        bool: Success status
    """
    try:
        metadata_manager = TenderMetadataManager()
        return metadata_manager.update_processing_status(document_id, status)
    except Exception as e:
        logger.error(f"❌ Error in update_tender_status: {e}")
        return False

# Test function
def test_mongodb_connection():
    """Test MongoDB connection and collection access"""
    try:
        metadata_manager = TenderMetadataManager()
        
        # Test by getting document count
        count = metadata_manager.collection.count_documents({})
        
        logger.info(f"✅ MongoDB connection successful.")
        logger.info(f"📊 Collection '{metadata_manager.tender_collection_name}' contains {count} documents")
        return True
        
    except Exception as e:
        logger.error(f"❌ MongoDB connection test failed: {e}")
        return False

if __name__ == "__main__":
    # Test the MongoDB connection
    print("🧪 Testing MongoDB connection...")
    test_mongodb_connection()