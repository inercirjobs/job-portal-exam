import boto3
import time
import os
import csv
import io
import re

import razorpay
import random
from botocore.exceptions import ClientError
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from django.conf import settings
from rest_framework.authtoken.models import Token
from rest_framework.permissions import IsAuthenticated
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

    def post(self, request):
        exam_id = request.data.get('exam')
        if not exam_id:
            return Response({'error': 'Exam ID is required.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            exam = ExamSchedule.objects.get(id=exam_id)
        except ExamSchedule.DoesNotExist:
            return Response({'error': 'Invalid exam ID.'}, status=status.HTTP_404_NOT_FOUND)

        # Get timezone
        ist = pytz.timezone('Asia/Kolkata')
        tz = get_current_timezone()

        # Convert string times to datetime.time
        try:
            start_time = datetime.strptime(exam.exam_start_time, "%H:%M:%S").time()
            end_time = datetime.strptime(exam.exam_end_time, "%H:%M:%S").time()
        except (ValueError, TypeError):
            return Response({'error': 'Invalid time format in exam schedule.'}, status=400)

        # Combine with date and make timezone-aware (IST)
        exam_start_dt = ist.localize(datetime.combine(exam.exam_date, start_time))
        exam_end_dt = ist.localize(datetime.combine(exam.exam_date, end_time))
        current_time = datetime.now(ist)

        # Debugging/logging (optional)
        print("IST Exam Start:", exam_start_dt.strftime("%Y-%m-%d %H:%M:%S %Z"))
        print("IST Exam End:  ", exam_end_dt.strftime("%Y-%m-%d %H:%M:%S %Z"))
        print("IST Now:       ", current_time.strftime("%Y-%m-%d %H:%M:%S %Z"))

        # If exam is over
        if current_time > exam_end_dt:
            return Response({
                "message": f"Exam '{exam.exam_name}' is already completed. Ended at {exam.exam_end_time} on {exam.exam_date} (IST)."
            }, status=status.HTTP_400_BAD_REQUEST)

        # If exam has not started
        if current_time < exam_start_dt:
            return Response({
                "message": f"Exam '{exam.exam_name}' has not started yet. Starts at {exam.exam_start_time} on {exam.exam_date} (IST)."
            }, status=status.HTTP_400_BAD_REQUEST)

        # Exam is ongoing — save user
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            time_left = exam_end_dt - current_time
            return Response({
                'message': 'Exam started.',
                'session_id': user.id,
                'email': user.email,
                'time_left': str(time_left).split('.')[0]  # Format as HH:MM:SS
            }, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SubmitScoreView(APIView):
    authentication_classes = []  # No auth required, optional
    permission_classes = [AllowAnyPermission]
    def post(self, request, session_id):
        try:
            user = User.objects.get(id=session_id)
        except User.DoesNotExist:
            return Response({'error': 'Invalid session ID'}, status=404)

        score = request.data.get('score')
        if not score:
            return Response({'error': 'Score is required'}, status=400)

        user.score = score
        user.save()

        return Response({'message': 'Score submitted successfully'}, status=200)



class ExamQuestionListView(APIView):
    authentication_classes = []  # No auth required, optional
    permission_classes = [AllowAnyPermission]
    def get(self, request):
        questions = ExamQuestion.objects.all()
        serializer = ExamQuestionSerializer(questions, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


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
    authentication_classes = []  # No auth required, optional
    permission_classes = [AllowAnyPermission]
    def get(self, request):
        users = User.objects.all()
        serializer = UserSerializer(users, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
