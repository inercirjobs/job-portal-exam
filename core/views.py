
import boto3
import time
import os
import csv
import io
import re

import razorpay
import random
import json
from botocore.exceptions import ClientError
from job_portal_exam.redis_settings import get_redis
from django.core.cache import cache
from .models import ExamQuestion, User
from job_portal_exam.redis_settings import get_redis, CACHE_TTL
from .serializers import UserSerializer

def cache_exam_questions():
    """Cache all exam questions in Redis"""
    redis = get_redis()
    questions = ExamQuestion.objects.all()
    total = questions.count()
    if total == 0:
        return 0
    # Cache each question
    for question in questions:
        question_data = {
            'id': question.id,
            'question': question.question,
            'option_1': question.option_1,
            'option_2': question.option_2,
            'option_3': question.option_3,
            'option_4': question.option_4,
            'correct_answer': question.correct_answer
        }
        redis.hset('questions', str(question.id), json.dumps(question_data))
    # Set total questions count
    redis.set('total_questions', total)
    return total
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle, AnonRateThrottle
from django.contrib.auth import get_user_model
from django.conf import settings
from rest_framework.authtoken.models import Token
from rest_framework.permissions import IsAuthenticated
from django.core.cache import cache
from django.db.models import Q
from .models import User,Admins,ExamQuestion,ExamSchedule
from django.utils import timezone
from .serializers import (
    UserSerializer,ExamQuestionSerializer,AdminSerializer,AdminLoginSerializer,ExamScheduleSerializer
)
from django.utils.timezone import now
# from .utils.s3_signed import generate_presigned_url
from core.utils import build_presigned_get_url, generate_presigned_url

from google.oauth2 import id_token
# from google.oauth2 import id_token
# from google.auth.transport import requests
import requests 
from google.auth.transport import requests as googleRequest

import hmac
from django.shortcuts import get_object_or_404
import hashlib
from rest_framework.parsers import MultiPartParser, FormParser,JSONParser
from .utils import get_redirect_url
import uuid
from rest_framework.views import APIView
from django.core.cache import cache
from django.core.mail import send_mail
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q
# from razorpay_client import client
from django.utils import timezone
from datetime import timedelta
import razorpay
from django.shortcuts import redirect
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.http import HttpResponseBadRequest
from razorpay.errors import SignatureVerificationError
client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
from django.http import StreamingHttpResponse
import pytz
from datetime import datetime, timedelta

import tempfile

ist = pytz.timezone('Asia/Kolkata')
schedule_time = datetime.now(ist) + timedelta(minutes=2)
payment_schedule_date = schedule_time.isoformat()

def verify_signature(payment_id, subscription_id, signature, secret):
    msg = f"{payment_id}|{subscription_id}".encode()
    generated_signature = hmac.new(
        key=secret.encode(),
        msg=msg,
        digestmod=hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(generated_signature, signature)
# Custom Permissions
class IsOwnerOrReadOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.user == request.user

class IsHROrAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in ['hr', 'admin']

class IsAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'admin'
class AllowAnyPermission(permissions.BasePermission):
    """
    Custom permission that always allows access.
    Equivalent to rest_framework.permissions.AllowAny
    """
    def has_permission(self, request, view):
        return True


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all().order_by('-created_at')
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser,JSONParser]
    
    def get_queryset(self):
        if self.request.user.role == 'admin':
            return User.objects.all().order_by('-created_at')
        else:
            return User.objects.filter(id=self.request.user.id)
        
        

        
 

    @action(detail=False, methods=['get'])
    def profile(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)
    
  

class AddAdminView(APIView):
    permission_classes = [AllowAnyPermission]
    authentication_classes = []  # Disable auth for login endpoint

    def post(self, request):
        serializer = AdminSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({'message': 'Admin created successfully', 'data': serializer.data}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class AdminLoginView(APIView):
    def post(self, request):
        from job_portal_exam.redis_settings import get_redis, CACHE_TTL
        import json
        redis = get_redis()
        email = request.data.get('email')
        password = request.data.get('password')
        cache_key = f'admin_login:{email}:{password}'
        cached_response = redis.get(cache_key)
        if cached_response:
            return Response(json.loads(cached_response))

        # Usual authentication logic
        # ...existing code for authenticating admin...
        # If authentication is successful:
        #   response_data = {...}
        #   redis.setex(cache_key, CACHE_TTL, json.dumps(response_data))
        #   return Response(response_data)
        # If authentication fails:
        #   return Response({'error': 'Invalid credentials'}, status=401)

        # Placeholder for actual logic:
        # Remove this block and use your real authentication
        if email == 'admin@example.com' and password == 'admin123':
            response_data = {
                'token': get_random_string(32),
                'admin': email
            }
            redis.setex(cache_key, CACHE_TTL, json.dumps(response_data))
            return Response(response_data)
        else:
            return Response({'error': 'Invalid credentials'}, status=401)
    permission_classes = [AllowAnyPermission]
    authentication_classes = []  # Disable auth for login endpoint

    def post(self, request):
        serializer = AdminLoginSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            password = serializer.validated_data['password']
            
            try:
                admin = Admins.objects.get(email=email)
            except Admins.DoesNotExist:
                return Response({'error': 'Invalid email or password'}, status=status.HTTP_401_UNAUTHORIZED)
            
            # Use check_password to verify hashed password
            if not admin.check_password(password):
                return Response({'error': 'Invalid email or password'}, status=status.HTTP_401_UNAUTHORIZED)
            
            # If login success, you can return admin info or token if you implement JWT etc.
            return Response({'message': 'Login successful', 'admin_id': admin.id, 'email': admin.email}, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class AddExamQuestionView(APIView):
    permission_classes = [AllowAnyPermission]
    authentication_classes = []  # Disable auth for login endpoint

    def post(self, request):
        serializer = ExamQuestionSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({'message': 'Question added successfully', 'data': serializer.data}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AddExamScheduleView(APIView):
    authentication_classes = []  # No auth required, optional
    permission_classes = [AllowAnyPermission]

    def post(self, request):
        serializer = ExamScheduleSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({
                'message': 'Exam schedule added successfully',
                'data': serializer.data
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from datetime import datetime, timedelta
from .models import ExamSchedule
from .serializers import UserSerializer
from django.utils.timezone import make_aware
from django.utils.timezone import make_aware, now as timezone_now
from django.utils.timezone import make_aware,is_aware, get_current_timezone, now as timezone_now

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.utils.timezone import (
    make_aware, is_aware, get_current_timezone, now as timezone_now
)
from datetime import datetime

from .models import ExamSchedule, User
from .serializers import UserSerializer
from pytz import timezone as pytz_timezone

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.utils.timezone import get_current_timezone, make_aware, now as timezone_now
from datetime import datetime
from .models import ExamSchedule, User
from .serializers import UserSerializer


class StartExamView(APIView):
    authentication_classes = []  # No authentication
    permission_classes = [AllowAnyPermission]  # Allow anyone
    throttle_classes = [UserRateThrottle]  # Add rate limiting

    def post(self, request):
        redis = get_redis()
        exam_id = request.data.get('exam')
        if not exam_id:
            return Response({'error': 'Exam ID is required.'}, status=status.HTTP_400_BAD_REQUEST)

        # Try to get exam from cache with pipeline
        pipe = redis.pipeline()
        pipe.get(f'exam:{exam_id}')
        pipe.get(f'exam_questions:{exam_id}')
        cached_exam, cached_questions = pipe.execute()

        if cached_exam:
            exam_data = json.loads(cached_exam)
        else:
            try:
                exam = ExamSchedule.objects.get(id=exam_id)
                exam_data = ExamScheduleSerializer(exam).data
                redis.setex(f'exam:{exam_id}', 3600, json.dumps(exam_data))
            except ExamSchedule.DoesNotExist:
                return Response({'error': 'Invalid exam ID.'}, status=status.HTTP_404_NOT_FOUND)

        # Get timezone and current time (do this early)
        ist = pytz.timezone('Asia/Kolkata')
        current_time = datetime.now(ist)

        # Convert and validate times (using try-except for validation)
        try:
            # exam_data['exam_date'] may be a string, so parse it
            exam_date = exam_data['exam_date']
            if isinstance(exam_date, str):
                exam_date = datetime.strptime(exam_date, "%Y-%m-%d").date()
            start_time = datetime.strptime(exam_data['exam_start_time'], "%H:%M:%S").time()
            end_time = datetime.strptime(exam_data['exam_end_time'], "%H:%M:%S").time()
            exam_start_dt = ist.localize(datetime.combine(exam_date, start_time))
            exam_end_dt = ist.localize(datetime.combine(exam_date, end_time))
        except (ValueError, TypeError, KeyError):
            return Response({'error': 'Invalid exam schedule times.'}, status=400)

        # Quick time validation
        if current_time > exam_end_dt:
            return Response({
                "message": f"Exam '{exam.exam_name}' has ended."
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if current_time < exam_start_dt:
            wait_time = exam_start_dt - current_time
            return Response({
                "message": f"Exam starts in {str(wait_time).split('.')[0]}"
            }, status=status.HTTP_400_BAD_REQUEST)

        # Check active sessions with pipeline
        pipe = redis.pipeline()
        pipe.scard('active_exam_sessions')
        pipe.get(f'exam_questions:{exam_id}')  # Try to get cached questions again
        active_count, questions = pipe.execute()

        if active_count >= 1000:
            return Response({
                "message": "Maximum users reached. Try again later."
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        # Get or prepare questions (moved after validation to avoid unnecessary work)
        if not cached_questions:
            questions = get_or_cache_exam_questions(exam_id)
        else:
            questions = json.loads(cached_questions)

        # Create user and prepare session
        serializer = UserSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user = serializer.save()
        time_left = exam_end_dt - current_time

        # Prepare exam session with questions using pipeline
        pipe = redis.pipeline()
        
        # Session data with questions
        session_data = prepare_exam_session(
            user.id, exam_id, current_time, 
            exam_end_dt, questions
        )

        return Response({
            'message': 'Exam started.',
            'session_id': user.id,
            'email': user.email,
            'time_left': str(time_left).split('.')[0]
        }, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SubmitScoreView(APIView):
    authentication_classes = []  # No auth required, optional
    permission_classes = [AllowAnyPermission]
    throttle_classes = [UserRateThrottle]  # Add rate limiting

    def post(self, request, session_id):
        redis = get_redis()
        # Check if session exists in Redis
        session_data = get_exam_session(session_id)
        if not session_data:
            return Response({'error': 'Invalid or expired session ID'}, status=404)

        score = request.data.get('score')
        if not score:
            return Response({'error': 'Score is required'}, status=400)

        try:
            # Prepare submission data
            submission_data = {
                'score': score,
                'submission_time': timezone.now().isoformat(),
                'user_id': session_id,
                'exam_id': session_data.get('exam_id')
            }

            active_count = redis.scard('active_exam_sessions')
            if active_count >= 1000:
                # Queue the submission for batch processing
                queue_score_submission(session_id, submission_data)
                # Update session data in Redis
                session_data['score'] = score
                session_data['submission_time'] = submission_data['submission_time']
                update_exam_session(session_id, session_data.get('exam_id'), {'score': score, 'submission_time': submission_data['submission_time']})
                # Remove from active sessions
                redis.srem('active_exam_sessions', session_id)
                return Response({
                    'message': 'Score submitted successfully',
                    'session_id': session_id,
                    'score': score,
                    'status': 'queued for processing'
                }, status=202)
            else:
                # Save directly to DB (example: update User or create Score model)
                user = User.objects.filter(id=session_id).first()
                if user:
                    user.score = str(score)
                    user.save()
                # Update session data in Redis
                session_data['score'] = score
                session_data['submission_time'] = submission_data['submission_time']
                update_exam_session(session_id, session_data.get('exam_id'), {'score': score, 'submission_time': submission_data['submission_time']})
                # Remove from active sessions
                redis.srem('active_exam_sessions', session_id)
                return Response({
                    'message': 'Score submitted successfully',
                    'session_id': session_id,
                    'score': score,
                    'status': 'saved'
                }, status=200)

        except Exception as e:
            # Log error and store failed submission for retry
            redis.sadd('failed_submissions', json.dumps({
                'session_id': session_id,
                'score': score,
                'error': str(e),
                'timestamp': timezone.now().isoformat()
            }))
            return Response({'error': str(e)}, status=500)



class ExamQuestionListView(APIView):
    authentication_classes = []  # No auth required, optional
    permission_classes = [AllowAnyPermission]
    throttle_classes = [UserRateThrottle]  # Add rate limiting

    def get(self, request):
        redis = get_redis()
        # Check if cache initialization is needed
        if not redis.exists('total_questions'):
            total = cache_exam_questions()
            if total == 0:
                return Response({
                    'error': 'No questions available'
                }, status=404)
        
        # Get all questions from cache
        questions_data = []
        for key in redis.hkeys('questions'):
            question_json = redis.hget('questions', key)
            if question_json:
                question_data = json.loads(question_json)
                # Ensure output format: id, question, option_1, option_2, option_3, option_4, correct_answer
                questions_data.append({
                    'id': question_data.get('id'),
                    'question': question_data.get('question'),
                    'option_1': question_data.get('option_1'),
                    'option_2': question_data.get('option_2'),
                    'option_3': question_data.get('option_3'),
                    'option_4': question_data.get('option_4'),
                    'correct_answer': question_data.get('correct_answer'),
                })
        return Response(questions_data)


class ExamScheduleListView(APIView):
    authentication_classes = []  # No auth required, optional
    permission_classes = [AllowAnyPermission]

    def get(self, request):
        schedules = ExamSchedule.objects.all()
        serializer = ExamScheduleSerializer(schedules, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class AdminListView(APIView):
    authentication_classes = []  # No auth required, optional
    permission_classes = [AllowAnyPermission]
    def get(self, request):
        admins = Admins.objects.all()
        serializer = AdminSerializer(admins, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class UserListView(APIView):
    def get(self, request):
        redis = get_redis()
        cache_key = 'user_list'
        cached_users = redis.get(cache_key)
        if cached_users:
            import json
            return Response(json.loads(cached_users))

        # Not cached, fetch from DB
        users = User.objects.all()
        serializer = UserSerializer(users, many=True)
        data = serializer.data
        # Cache the result
        redis.setex(cache_key, CACHE_TTL, json.dumps(data))
        return Response(data)
    authentication_classes = []  # No auth required, optional
    permission_classes = [AllowAnyPermission]
    def get(self, request):
        users = User.objects.all()
        serializer = UserSerializer(users, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)



from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
# ShowPendingRequestsView: List all pending score submissions in Redis
class ShowPendingRequestsView(APIView):
    authentication_classes = []
    permission_classes = [AllowAnyPermission]
    def get(self, request):
        redis = get_redis()
        pending_ids = list(redis.smembers('pending_submissions'))
        pending = []
        for sid in pending_ids:
            key = f'score_submission:{sid}'
            data = redis.get(key)
            if data:
                try:
                    pending.append(json.loads(data))
                except Exception:
                    pending.append({'session_id': sid, 'raw': data})
            else:
                pending.append({'session_id': sid, 'error': 'No data found'})
        return Response({'pending_requests': pending}, status=200)
def update_exam_session(session_id, exam_id, updates=None):
    """Update exam session data in Redis."""
    redis = get_redis()
    session_key = f'exam_session:{session_id}:{exam_id}'
    data = redis.get(session_key)
    if data:
        session_data = json.loads(data)
        if updates:
            session_data.update(updates)
            redis.setex(session_key, 3600, json.dumps(session_data))
        return session_data
    return None
def queue_score_submission(*args, **kwargs):
    """Queue score submission data in Redis for async processing."""
    # Accepts (data) or (request, data)
    if len(args) == 1:
        data = args[0]
    elif len(args) == 2:
        data = args[1]
    else:
        data = kwargs.get('data')
    redis = get_redis()
    redis.rpush('score_submission_queue', json.dumps(data))
def get_exam_session(session_id, exam_id=None):
    """Retrieve exam session data from Redis."""
    redis = get_redis()
    # If exam_id is not provided, try to find the session for any exam
    if exam_id:
        session_key = f'exam_session:{session_id}:{exam_id}'
        data = redis.get(session_key)
        if data:
            return json.loads(data)
    else:
        # Try all possible exam session keys for this user
        for key in redis.scan_iter(f'exam_session:{session_id}:*'):
            data = redis.get(key)
            if data:
                return json.loads(data)
    return None
def prepare_exam_session(user_id, exam_id, start_time, end_time, questions):
    """Prepare and store exam session data in Redis."""
    redis = get_redis()
    session_key = f'exam_session:{user_id}:{exam_id}'
    session_data = {
        'user_id': user_id,
        'exam_id': exam_id,
        'start_time': str(start_time),
        'end_time': str(end_time),
        'questions': questions
    }
    redis.setex(session_key, 3600, json.dumps(session_data))
    # Optionally add to active sessions set
    redis.sadd('active_exam_sessions', user_id)
    return session_data
def get_or_cache_exam_questions(exam_id):
    """Fetch and cache exam questions for a given exam_id."""
    redis = get_redis()
    cache_key = f'exam_questions:{exam_id}'
    cached = redis.get(cache_key)
    if cached:
        return json.loads(cached)
    # Fetch all questions (no exam_id field exists)
    questions = ExamQuestion.objects.all()
    data = []
    for q in questions:
        data.append({
            'id': q.id,
            'question': q.question,
            'option_1': q.option_1,
            'option_2': q.option_2,
            'option_3': q.option_3,
            'option_4': q.option_4,
            'correct_answer': q.correct_answer
        })
    redis.setex(cache_key, 3600, json.dumps(data))
    return data
from django.utils.crypto import get_random_string