import json
import hashlib
from functools import wraps
from django.core.cache import cache
from core.responses import StandardResponse

def idempotent(timeout=86400):
    """
    Idempotency decorator for Django Ninja APIs.
    Caches the response based on the Idempotency-Key header.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(request, *args, **kwargs):
            idempotency_key = request.headers.get('Idempotency-Key')
            
            if not idempotency_key:
                # If no idempotency key is provided, execute normally
                return func(request, *args, **kwargs)
                
            # Create a unique cache key based on the user (if authenticated) and the idempotency key
            user_id = request.user.id if request.user and request.user.is_authenticated else 'anonymous'
            cache_key = f"idempotency:{user_id}:{idempotency_key}"
            
            cached_response = cache.get(cache_key)
            if cached_response:
                return cached_response
                
            # Execute the function
            response = func(request, *args, **kwargs)
            
            # Cache the response
            cache.set(cache_key, response, timeout=timeout)
            
            return response
        return wrapper
    return decorator
