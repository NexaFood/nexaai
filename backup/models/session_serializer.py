"""
Custom session serializer that supports string user IDs from MongoDB.
"""
from django.contrib.sessions.serializers import JSONSerializer
from django.core.signing import b64_encode, b64_decode
import pickle


class MongoSessionSerializer:
    """
    Session serializer that uses pickle to support MongoDB string user IDs.
    Falls back to JSON for non-user session data.
    """
    
    def dumps(self, obj):
        """Serialize session data using pickle."""
        pickled = pickle.dumps(obj, pickle.HIGHEST_PROTOCOL)
        return b64_encode(pickled)
    
    def loads(self, data):
        """Deserialize session data from pickle."""
        # Handle both bytes and string input
        if isinstance(data, str):
            data = data.encode('ascii')
        return pickle.loads(b64_decode(data))
