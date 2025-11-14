"""Score processing utilities without Redis dependency.

This module removes Redis usage and updates user scores directly in the database.
Queued processing via Redis is no longer used in local development; the functions
remain as safe fallbacks that won't raise on missing infrastructure.
"""

import logging

logger = logging.getLogger(__name__)


def queue_score_submission(session_id, score_data):
    """Directly write score data to the database as a fallback for environments without Redis.

    This will create or update the User.score field (if a User with that id exists). The function
    logs failures but does not raise so scheduled tasks remain resilient.
    """
    try:
        from core.models import User
        try:
            user = User.objects.get(id=session_id)
            # Expect score to be present in score_data
            user.score = score_data.get('score')
            user.save(update_fields=['score'])
        except User.DoesNotExist:
            logger.warning("queue_score_submission: User with id %s does not exist", session_id)
    except Exception:
        logger.exception("Unexpected error when directly saving score for session %s", session_id)


def process_pending_submissions(batch_size=50):
    """No-op processor for environments without Redis.

    The scheduled job will call this function periodically. Since there is no Redis queue,
    this function currently performs no work but exists to maintain the scheduler contract.
    """
    logger.debug("process_pending_submissions called but Redis queue is disabled; nothing to do")
    return