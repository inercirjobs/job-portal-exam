# Redis Cache Settings
import os
from urllib.parse import urlparse

# Get Redis URL from environment variable, fallback to local Redis if not available
import os
from urllib.parse import urlparse
from django_redis import get_redis_connection
import redis
import logging

logger = logging.getLogger(__name__)

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
        client = get_redis_connection("default")
    except Exception as e:
        # Fallback to direct Redis connection
        logger.debug("django-redis pool unavailable: %s", e)
        redis_url = urlparse(REDIS_URL)
        client = redis.Redis(
            host=redis_url.hostname or 'localhost',
            port=int(redis_url.port or 6379),
            db=int(redis_url.path.lstrip('/') or 0),
            password=redis_url.password,
            decode_responses=True
        )

    # Check connectivity. If Redis is not reachable, fallback to fakeredis for local development
    try:
        # ping may raise a ConnectionError if Redis is not running
        client.ping()
        return client
    except Exception as e:
        logger.warning("Could not connect to Redis at %s (using fakeredis fallback): %s", REDIS_URL, e)
        try:
            import fakeredis

            fake = fakeredis.FakeRedis(decode_responses=True)
            return fake
        except Exception as fe:
            # If fakeredis is not available, return the original client and let callers handle errors
            logger.error("fakeredis not available, returning original redis client which may raise on use: %s", fe)
            return client

# Parse Redis URL for connection settings
redis_url = urlparse(REDIS_URL)
"""Fallback cache/settings used when Redis is not required in local development.

This file intentionally avoids importing `redis` or `django_redis` so importing
`job_portal_exam.settings` does not attempt to connect to Redis during app startup.
It provides a safe `get_redis()` that returns None and configures Django to use
the local memory cache backend by default.
"""

from django.core.cache import caches
import logging

logger = logging.getLogger(__name__)

# Use Django's local-memory cache in development by default.
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'exam-portal-cache',
    }
}

# Simple TTL settings (kept for compatibility)
CACHE_TTL = 60 * 15
CACHE_LONG_TTL = 60 * 60 * 24
CACHE_SHORT_TTL = 60 * 5

# Session config using cache
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'

# Provide a noop get_redis so code importing this module can still call it safely.
def get_redis():
    """Return None — Redis is disabled for local development in this configuration."""
    logger.debug('get_redis called but Redis is disabled in local settings')
    return None

# For backwards-compatibility, expose a small helper to access the configured cache
def get_cache():
    try:
        return caches['default']
    except Exception:
        logger.exception('Failed to get default cache')
        return None

# Provide sensible defaults for DRF throttling in local development so
# classes like UserRateThrottle have the required scopes.
REST_FRAMEWORK = {
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/minute',
        'user': '1000/minute',
    },
}