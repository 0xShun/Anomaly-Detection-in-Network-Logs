"""
API Key Authentication for Django REST Framework.

Uses environment variables for API key validation.
Set LOGBERT_API_KEYS in environment as comma-separated keys.
"""
import os
from rest_framework import authentication, exceptions


class APIKeyAuthentication(authentication.BaseAuthentication):
    """
    Custom authentication class that validates API keys from headers.
    
    Usage in views:
        authentication_classes = [APIKeyAuthentication]
        permission_classes = [IsAuthenticated]
    
    Client must send:
        Authorization: Bearer <api_key>
    or
        X-API-Key: <api_key>
    """
    
    def authenticate(self, request):
        # Try Authorization header first
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        if auth_header.startswith('Bearer '):
            api_key = auth_header[7:]  # Remove 'Bearer ' prefix
        else:
            # Try X-API-Key header
            api_key = request.META.get('HTTP_X_API_KEY', '')
        
        if not api_key:
            return None  # No credentials provided
        
        if self.is_valid_api_key(api_key):
            # Return a dummy user object (API key is valid)
            # DRF requires a user and auth tuple
            return (APIKeyUser(), api_key)
        
        raise exceptions.AuthenticationFailed('Invalid API key')
    
    def is_valid_api_key(self, api_key):
        """
        Validate API key against environment variables.
        
        Set LOGBERT_API_KEYS in environment:
            export LOGBERT_API_KEYS="key1,key2,key3"
        
        Or in PythonAnywhere:
            Add to .env file or set in web app config
        """
        valid_keys = os.environ.get('LOGBERT_API_KEYS', '').split(',')
        valid_keys = [key.strip() for key in valid_keys if key.strip()]
        
        if not valid_keys:
            # No keys configured - reject all API calls
            raise exceptions.AuthenticationFailed(
                'API keys not configured. Contact administrator.'
            )
        
        return api_key in valid_keys


class APIKeyUser:
    """
    Dummy user object for API key authentication.
    
    DRF requires authentication to return a user object.
    This represents an authenticated API client.
    """
    
    @property
    def is_authenticated(self):
        return True
    
    @property
    def is_anonymous(self):
        return False
    
    def __str__(self):
        return 'APIKeyUser'
