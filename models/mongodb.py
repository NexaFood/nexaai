"""
MongoDB database helper using PyMongo.
Provides direct access to MongoDB collections for app data.
"""
from pymongo import MongoClient, ASCENDING, DESCENDING
from django.conf import settings
from datetime import datetime
from bson import ObjectId
import logging

logger = logging.getLogger(__name__)


class MongoDB:
    """
    MongoDB connection and collection access.
    Singleton pattern to reuse connection.
    """
    _instance = None
    _client = None
    _db = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MongoDB, cls).__new__(cls)
            cls._instance._connect()
        return cls._instance
    
    def _connect(self):
        """Establish MongoDB connection."""
        try:
            self._client = MongoClient(settings.MONGO_URI)
            self._db = self._client[settings.MONGO_DB_NAME]
            logger.info(f"Connected to MongoDB: {settings.MONGO_DB_NAME}")
            self._create_indexes()
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise
    
    def _create_indexes(self):
        """Create indexes for better query performance."""
        try:
            # Models collection indexes
            self.models.create_index([("user_id", ASCENDING), ("created_at", DESCENDING)])
            self.models.create_index([("status", ASCENDING)])
            
            # Printers collection indexes
            self.printers.create_index([("user_id", ASCENDING), ("name", ASCENDING)])
            self.printers.create_index([("status", ASCENDING)])
            
            # Print jobs collection indexes
            self.print_jobs.create_index([('user_id', ASCENDING), ('created_at', DESCENDING)])
            self.print_jobs.create_index([('printer_id', ASCENDING), ('status', ASCENDING)])
            self.print_jobs.create_index([('status', ASCENDING)])
            
            # Users collection indexes
            # Case-insensitive unique index on username
            self.users.create_index(
                [('username', ASCENDING)], 
                unique=True,
                collation={'locale': 'en', 'strength': 2}
            )
            self.users.create_index([('email', ASCENDING)])
            
            # Design workflow collection indexes
            self.design_projects.create_index([('user_id', ASCENDING), ('created_at', DESCENDING)])
            self.design_projects.create_index([('stage', ASCENDING), ('status', ASCENDING)])
            self.design_concepts.create_index([('project_id', ASCENDING)])
            self.part_breakdowns.create_index([('project_id', ASCENDING)])
            
            logger.info("MongoDB indexes created successfully")
        except Exception as e:
            logger.warning(f"Failed to create indexes: {e}")
    
    @property
    def models(self):
        """3D models collection."""
        return self._db.models_3d
    
    @property
    def printers(self):
        """Printers collection."""
        return self._db.printers
    
    @property
    def print_jobs(self):
        """Print jobs collection."""
        return self._db.print_jobs
    
    @property
    def generation_jobs(self):
        """Generation jobs collection."""
        return self._db.generation_jobs
    
    @property
    def users(self):
        """Users collection."""
        return self._db.users
    
    @property
    def design_projects(self):
        """Design projects collection (3-stage workflow)."""
        return self._db.design_projects
    
    @property
    def design_concepts(self):
        """Design concepts collection (Stage 1)."""
        return self._db.design_concepts
    
    @property
    def part_breakdowns(self):
        """Part breakdowns collection (Stage 2)."""
        return self._db.part_breakdowns
    
    def close(self):
        """Close MongoDB connection."""
        if self._client:
            self._client.close()
            logger.info("MongoDB connection closed")


# Global MongoDB instance
db = MongoDB()


# Helper functions for common operations

def to_object_id(id_str):
    """Convert string to ObjectId, return None if invalid."""
    try:
        return ObjectId(id_str) if id_str else None
    except:
        return None


def doc_to_dict(doc):
    """Convert MongoDB document to dict with _id as string."""
    if not doc:
        return None
    doc['id'] = str(doc['_id'])
    return doc


def docs_to_list(cursor):
    """Convert MongoDB cursor to list of dicts."""
    return [doc_to_dict(doc) for doc in cursor]
