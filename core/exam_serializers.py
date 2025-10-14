from rest_framework import serializers

class ExamStartResponseSerializer(serializers.Serializer):
    message = serializers.CharField()
    session_id = serializers.CharField()
    email = serializers.CharField()
    time_left = serializers.CharField()
    total_questions = serializers.IntegerField()
    first_question = serializers.DictField(allow_null=True)