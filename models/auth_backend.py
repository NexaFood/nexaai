"""
Custom authentication backend for MongoDB.
Stores users in MongoDB instead of SQLite.
"""
from django.contrib.auth.backends import BaseBackend
from django.contrib.auth.hashers import check_password, make_password
from models.mongodb import db
from bson import ObjectId
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class MongoUser:
    """
    Custom user class that mimics Django's User model.
    Stores data in MongoDB instead of SQLite.
    """
    
    # Django requires these class attributes
    pk = None
    backend = None
    
    def __init__(self, user_doc):
        self._doc = user_doc
        self.id = str(user_doc['_id'])
        self.pk = self.id  # Django uses pk as primary key
        self.username = user_doc['username']
        self.email = user_doc.get('email', '')
        self.first_name = user_doc.get('first_name', '')
        self.last_name = user_doc.get('last_name', '')
        self.is_active = user_doc.get('is_active', True)
        self.is_staff = user_doc.get('is_staff', False)
        self.is_superuser = user_doc.get('is_superuser', False)
        self.date_joined = user_doc.get('date_joined')
        self.last_login = user_doc.get('last_login')
        self._password = user_doc.get('password')
        self.backend = 'models.auth_backend.MongoDBAuthBackend'
    
    def __str__(self):
        return self.username
    
    def get_username(self):
        return self.username
    
    def is_authenticated(self):
        return True
    
    def is_anonymous(self):
        return False
    
    def set_password(self, raw_password):
        """Hash and set password."""
        self._password = make_password(raw_password)
        db.users.update_one(
            {'_id': ObjectId(self.id)},
            {'$set': {'password': self._password, 'updated_at': datetime.utcnow()}}
        )
    
    def check_password(self, raw_password):
        """Check if password matches."""
        return check_password(raw_password, self._password)
    
    def save(self):
        """Save user to MongoDB."""
        if hasattr(self, '_id'):
            # Update existing
            db.users.update_one(
                {'_id': ObjectId(self.id)},
                {'$set': {
                    'username': self.username,
                    'email': self.email,
                    'first_name': self.first_name,
                    'last_name': self.last_name,
                    'is_active': self.is_active,
                    'is_staff': self.is_staff,
                    'is_superuser': self.is_superuser,
                    'updated_at': datetime.utcnow()
                }}
            )
        else:
            # Create new
            doc = {
                'username': self.username,
                'email': self.email,
                'password': self._password,
                'first_name': self.first_name,
                'last_name': self.last_name,
                'is_active': self.is_active,
                'is_staff': self.is_staff,
                'is_superuser': self.is_superuser,
                'date_joined': datetime.utcnow(),
                'last_login': None,
                'updated_at': datetime.utcnow()
            }
            result = db.users.insert_one(doc)
            self.id = str(result.inserted_id)
    
    def update_last_login(self):
        """Update last login timestamp."""
        db.users.update_one(
            {'_id': ObjectId(self.id)},
            {'$set': {'last_login': datetime.utcnow()}}
        )
        self.last_login = datetime.utcnow()


class MongoDBAuthBackend(BaseBackend):
    """
    Custom authentication backend that uses MongoDB.
    """
    
    def authenticate(self, request, username=None, password=None, **kwargs):
        """
        Authenticate user against MongoDB.
        """
        if username is None or password is None:
            return None
        
        try:
            # Find user in MongoDB
            user_doc = db.users.find_one({'username': username})
            
            if not user_doc:
                logger.debug(f"User not found: {username}")
                return None
            
            # Check password
            if not check_password(password, user_doc['password']):
                logger.debug(f"Invalid password for user: {username}")
                return None
            
            # Check if active
            if not user_doc.get('is_active', True):
                logger.debug(f"User is inactive: {username}")
                return None
            
            # Create MongoUser instance
            user = MongoUser(user_doc)
            user.update_last_login()
            
            logger.info(f"User authenticated: {username}")
            return user
        
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return None
    
    def get_user(self, user_id):
        """
        Get user by ID from MongoDB.
        """
        try:
            user_doc = db.users.find_one({'_id': ObjectId(user_id)})
            
            if not user_doc:
                return None
            
            return MongoUser(user_doc)
        
        except Exception as e:
            logger.error(f"Error getting user: {e}")
            return None


def create_user(username, email, password, is_superuser=False, is_staff=False):
    """
    Helper function to create a new user in MongoDB.
    """
    # Check if user exists
    if db.users.find_one({'username': username}):
        raise ValueError(f"User '{username}' already exists")
    
    # Create user document
    user_doc = {
        'username': username,
        'email': email,
        'password': make_password(password),
        'first_name': '',
        'last_name': '',
        'is_active': True,
        'is_staff': is_staff,
        'is_superuser': is_superuser,
        'date_joined': datetime.utcnow(),
        'last_login': None,
        'updated_at': datetime.utcnow()
    }
    
    result = db.users.insert_one(user_doc)
    user_doc['_id'] = result.inserted_id
    
    return MongoUser(user_doc)
