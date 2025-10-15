"""
Redis utility functions for exam management
"""
from django.core.cache import cache
import json
from datetime import datetime, timedelta
import random

def get_or_cache_exam_questions(exam_id):
    """Get cached questions for an exam or cache them if not present"""
    from core.models import ExamQuestion
    from core.serializers import ExamQuestionSerializer
    
    redis = get_redis()
    
    # Try to get cached questions for this exam
    questions_key = f'exam_questions:{exam_id}'
    cached_questions = redis.get(questions_key)
    
    if cached_questions:
        return json.loads(cached_questions)
    
    # If not in cache, get from DB and cache them
    questions = ExamQuestion.objects.all().order_by('?')[:99]  # Random 99 questions
    serializer = ExamQuestionSerializer(questions, many=True)
    questions_data = serializer.data
    
    # Cache for 24 hours
    redis.setex(questions_key, 86400, json.dumps(questions_data))
    
    return questions_data

def prepare_exam_session(user_id, exam_id, start_time, end_time, questions):
    """Prepare and cache exam session data"""
    redis = get_redis()
    session_key = f'exam_session:{user_id}'
    
    # Create session data with questions
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
    duration = (end_time - start_time).seconds + 3600
    redis.setex(session_key, duration, json.dumps(session_data))
    
    # Add to active sessions
    redis.sadd('active_exam_sessions', user_id)
    
    return session_data

def get_exam_progress(user_id):
    """Get user's exam progress"""
    redis = get_redis()
    session_key = f'exam_session:{user_id}'
    session_data = redis.get(session_key)
    
    if not session_data:
        return None
        
    return json.loads(session_data)

def update_exam_progress(user_id, question_number, answer):
    """Update user's exam progress"""
    redis = get_redis()
    session_key = f'exam_session:{user_id}'
    session_data = redis.get(session_key)
    
    if not session_data:
        return False
        
    session_data = json.loads(session_data)
    session_data['current_question'] = question_number
    session_data['answers'][str(question_number)] = answer
    
    # Update with remaining TTL
    ttl = redis.ttl(session_key)
    if ttl > 0:
        redis.setex(session_key, ttl, json.dumps(session_data))
        return True
    
    return False