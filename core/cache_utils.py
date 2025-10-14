from django.core.cache import cache
import json
import redis
from django.conf import settings
import os

def get_redis_client():
    """Get Redis client instance"""
    redis_url = os.getenv('REDIS_URL', 'redis://127.0.0.1:6379/1')
    return redis.Redis.from_url(redis_url, decode_responses=True)

def cache_exam_questions():
    """Cache all exam questions"""
    try:
        from core.models import ExamQuestion
        from core.serializers import ExamQuestionSerializer
        
        # Use Django's cache framework instead of direct Redis
        questions = ExamQuestion.objects.all().order_by('id')
        
        # Batch process questions
        question_data = {}
        question_ids = []
        
        for question in questions:
            serializer = ExamQuestionSerializer(question)
            question_data[f'question:{question.id}'] = json.dumps(serializer.data)
            question_ids.append(str(question.id))
        
        # Use Django's cache to store everything
        if question_data:
            cache.set_many(question_data, timeout=86400)  # 24 hours
            cache.set('question_ids', json.dumps(question_ids), timeout=86400)
            cache.set('total_questions', len(questions), timeout=86400)
            
        return len(questions)
    except Exception as e:
        print(f"Error caching exam questions: {str(e)}")
        return 0

def get_cached_exam_questions():
    """Get cached exam questions efficiently"""
    try:
        # Get question IDs from cache
        question_ids = cache.get('question_ids')
        if not question_ids:
            total_questions = cache_exam_questions()
            if total_questions == 0:
                return []
            question_ids = cache.get('question_ids')
        
        if not question_ids:
            return []
            
        # Get questions from cache
        question_ids = json.loads(question_ids)
        keys = [f'question:{qid}' for qid in question_ids]
        question_data = cache.get_many(keys)
        
        # Process results
        questions = []
        for key in keys:
            if key in question_data:
                questions.append(json.loads(question_data[key]))
        
        return questions
    except Exception as e:
        print(f"Error retrieving cached questions: {str(e)}")
        return []

def prepare_exam_session(user_id, exam_id, start_time, end_time, questions):
    """Prepare and cache exam session data"""
    session_data = {
        'exam_id': exam_id,
        'start_time': start_time.isoformat(),
        'end_time': end_time.isoformat(),
        'questions': questions,
        'current_question': 0,
        'answers': {},
        'is_active': True
    }
    
    # Cache session for exam duration + 1 hour
    duration = int((end_time - start_time).total_seconds()) + 3600
    cache.set(f'exam_session:{user_id}', json.dumps(session_data), timeout=duration)
    cache.set(f'active_exam_sessions:{user_id}', '1', timeout=duration)
    
    return session_data