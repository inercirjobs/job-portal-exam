from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import User,ExamQuestion,Admins,ExamSchedule
from django.db import models
from django.contrib.auth import get_user_model
from rest_framework.validators import UniqueValidator
from .utils import generate_presigned_url
from django.contrib.auth.hashers import make_password  
   
# serializers.py
from rest_framework import serializers
from .models import User

import uuid

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'full_name', 'roll_number', 'email', 'college_code', 'exam', 'created_at', 'score']
        read_only_fields = ['id', 'created_at', 'score']

    def create(self, validated_data):
        # Generate a dummy username since AbstractUser requires it
        validated_data['username'] = f"user_{uuid.uuid4().hex[:10]}"
        user = User(**validated_data)
        user.set_unusable_password()  # Disable login
        user.save()
        return user

class AdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = Admins
        fields = ['id', 'email', 'password']
        extra_kwargs = {
            'password': {'write_only': True}
        }

    def create(self, validated_data):
        validated_data['password'] = make_password(validated_data['password'])  # Hash password
        return super().create(validated_data)


class AdminLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

class ExamQuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExamQuestion
        fields = '__all__'
        read_only_fields = ['id']

class ExamScheduleSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExamSchedule
        fields = ['id', 'exam_name', 'exam_date', 'exam_start_time', 'exam_end_time']

