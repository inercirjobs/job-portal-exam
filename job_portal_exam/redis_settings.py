# Redis Cache Settings
import os
from urllib.parse import urlparse

# Get Redis URL from environment variable, fallback to local Redis if not available
import os
from urllib.parse import urlparse
from django_redis import get_redis_connection
import redis

# Redis Settings
# For production, set the REDIS_URL environment variable to your Redis server URL
# Format: redis://[:password@]host[:port][/db-number]
# Examples:
# - Local: redis://localhost:6379/0
# - Redis Cloud: redis://default:password@hostname:port
REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')

def get_redis():
    """
    Get a Redis connection instance
    """
    try:
        # Try to get connection from django-redis pool
        return get_redis_connection("default")
    except:
        # Fallback to direct Redis connection
        redis_url = urlparse(REDIS_URL)
        return redis.Redis(
            host=redis_url.hostname or 'localhost',
            port=int(redis_url.port or 6379),
            db=int(redis_url.path.lstrip('/') or 0),
            password=redis_url.password,
            decode_responses=True
        )

# Parse Redis URL for connection settings
redis_url = urlparse(REDIS_URL)
REDIS_HOST = redis_url.hostname or 'localhost'
REDIS_PORT = int(redis_url.port or 6379)
REDIS_DB = int(redis_url.path.lstrip('/') or 0)
REDIS_PASSWORD = redis_url.password

# Cache Configuration
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": REDIS_URL,
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
            "CONNECTION_POOL_CLASS_KWARGS": {
                "max_connections": 100,
                "timeout": 20
            },
            "SOCKET_TIMEOUT": 5,
            "SOCKET_CONNECT_TIMEOUT": 5,
            "RETRY_ON_TIMEOUT": True
        },
        "KEY_PREFIX": "exam_portal"
    }
}

# Cache timeouts
CACHE_TTL = 60 * 15  # 15 minutes default
CACHE_LONG_TTL = 60 * 60 * 24  # 24 hours
CACHE_SHORT_TTL = 60 * 5  # 5 minutes

# Session Configuration
SESSION_ENGINE = "django.contrib.sessions.backends.cache"
SESSION_CACHE_ALIAS = "default"

# Rate Limiting Configuration
REST_FRAMEWORK = {
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/minute',
        'user': '1000/minute',
    }
}

# Cache time to live is 15 minutes (in seconds)
CACHE_TTL = 60 * 15

# Use Redis for Session Store
SESSION_ENGINE = "django.contrib.sessions.backends.cache"
SESSION_CACHE_ALIAS = "default"

# Redis as cache backend
DJANGO_REDIS_IGNORE_EXCEPTIONS = True
DJANGO_REDIS_LOG_IGNORED_EXCEPTIONS = True

# Rate Limiting
REST_FRAMEWORK = {
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle'
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/minute',
        'user': '1000/minute'
    }
}