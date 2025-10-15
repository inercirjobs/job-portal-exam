from job_portal_exam.redis_settings import get_redis
def queue_score_submission(session_id, score_data):
    """Queue a score submission for batch processing"""
    redis = get_redis()
    submission_key = f'score_submission:{session_id}'
    redis.setex(submission_key, 3600, json.dumps(score_data))  # Store for 1 hour
    redis.sadd('pending_submissions', session_id)

def process_pending_submissions(batch_size=50):
    """Process pending submissions in batches"""
    from core.models import User
    redis = get_redis()
    
    while True:
        # Pop up to batch_size pending submissions one by one
        pending = []
        for _ in range(batch_size):
            sid = redis.spop('pending_submissions')
            if not sid:
                break
            pending.append(sid)
        if not pending:
            break
        submissions_to_process = []
        for session_id in pending:
            session_id = session_id.decode('utf-8') if isinstance(session_id, bytes) else session_id
            submission_key = f'score_submission:{session_id}'
            submission_data = redis.get(submission_key)
            
            if submission_data:
                submission_data = json.loads(submission_data)
                submissions_to_process.append({
                    'session_id': session_id,
                    'score': submission_data.get('score'),
                    'submission_time': submission_data.get('submission_time')
                })
                redis.delete(submission_key)
        
        # Bulk update users
        if submissions_to_process:
            user_updates = []
            for submission in submissions_to_process:
                try:
                    user = User.objects.get(id=submission['session_id'])
                    user.score = submission['score']
                    user_updates.append(user)
                except User.DoesNotExist:
                    continue
            
            if user_updates:
                User.objects.bulk_update(user_updates, ['score'])