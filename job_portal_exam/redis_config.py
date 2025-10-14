from django_redis import get_redis_connection
from django.core.cache import cache
import json

# Redis connection helper
def get_redis():
    return get_redis_connection("default")

# Cache decorators and helpers
def cache_exam_questions():
    """Cache all exam questions and maintain question sets"""
    from core.models import ExamQuestion
    from core.serializers import ExamQuestionSerializer
    redis = get_redis()
    
    # Get all questions and cache them individually
    questions = ExamQuestion.objects.all().order_by('id')
    for question in questions:
        serializer = ExamQuestionSerializer(question)
        question_key = f'question:{question.id}'
        redis.set(question_key, json.dumps(serializer.data), ex=86400)  # Cache for 24 hours
    
    # Cache the list of question IDs
    question_ids = [str(q.id) for q in questions]
    redis.set('question_ids', json.dumps(question_ids), ex=86400)
    
    # Cache total question count
    redis.set('total_questions', len(questions), ex=86400)
    
    return len(questions)

def get_cached_exam_questions():
    """Get cached exam questions efficiently"""
    redis = get_redis()
    
    # Get question IDs from cache
    question_ids = redis.get('question_ids')
    if not question_ids:
        # If no cached questions, rebuild cache
        cache_exam_questions()
        question_ids = redis.get('question_ids')
        if not question_ids:
            return []
    
    # Get questions from cache in pipeline for efficiency
    question_ids = json.loads(question_ids)
    pipe = redis.pipeline()
    for qid in question_ids:
        pipe.get(f'question:{qid}')
    
    # Execute pipeline and collect results
    questions = []
    for question_data in pipe.execute():
        if question_data:
            questions.append(json.loads(question_data))
    
    return questions

def get_active_exam_sessions():
    """Get all active exam sessions"""
    redis = get_redis()
    sessions = redis.keys('exam_session:*')
    return [session.decode('utf-8').split(':')[1] for session in sessions]

def create_exam_session(session_id, exam_data, timeout=7200):  # 2 hours timeout
    """Create a new exam session"""
    redis = get_redis()
    redis.setex(
        f'exam_session:{session_id}',
        timeout,
        json.dumps(exam_data)
    )

def get_exam_session(session_id):
    """Get exam session data"""
    redis = get_redis()
    session = redis.get(f'exam_session:{session_id}')
    return json.loads(session) if session else None

def update_exam_session(session_id, exam_data):
    """Update exam session data"""
    redis = get_redis()
    if redis.exists(f'exam_session:{session_id}'):
        ttl = redis.ttl(f'exam_session:{session_id}')
        if ttl > 0:
            redis.setex(
                f'exam_session:{session_id}',
                ttl,
                json.dumps(exam_data)
            )
            return True
    return False