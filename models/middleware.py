"""
Custom middleware for session-based authentication with MongoDB
"""

class SessionUserMiddleware:
    """
    Middleware to replace Django's request.user with our session-based user.
    This runs after AuthenticationMiddleware and overwrites request.user.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Get user from session
        user_data = request.session.get('user', None)
        
        # Create a SessionUser object
        class SessionUser:
            def __init__(self, user_data):
                self._data = user_data or {}
                # Copy all user data as attributes for easy access
                if self._data:
                    for key, value in self._data.items():
                        if not key.startswith('_'):
                            setattr(self, key, value)
                    # Store _id as id for Django compatibility
                    if '_id' in self._data:
                        self.id = self._data['_id']
            
            @property
            def is_authenticated(self):
                """
                Return True if user has valid session data with _id.
                This MUST be a property, not a simple boolean attribute,
                because Django templates check for callable/property attributes.
                """
                return bool(self._data and '_id' in self._data)
            
            @property
            def is_anonymous(self):
                """Return True if user is not authenticated."""
                return not self.is_authenticated
            
            def __getitem__(self, key):
                # Don't intercept property/method lookups
                if key in ('is_authenticated', 'is_anonymous'):
                    raise KeyError(key)
                return self._data.get(key, None)
            
            def get(self, key, default=None):
                return self._data.get(key, default)
            
            def __str__(self):
                return self._data.get('username', 'Anonymous')
        
        # Replace request.user with our session user
        request.user = SessionUser(user_data)
        
        response = self.get_response(request)
        return response
