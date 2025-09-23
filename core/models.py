from django.db import models
from django.contrib.auth.models import AbstractUser, Group, Permission
from django.utils import timezone
import secrets
import string

# Utility Functions
def generate_custom_user_id():
    chars = string.ascii_letters + string.digits + "-_.~!$'()*@"
    random_id = ''.join(secrets.choice(chars) for _ in range(10))
    return f"user_{random_id}"

def generate_custom_question_id():
    chars = string.ascii_letters + string.digits
    return f"user{''.join(secrets.choice(chars) for _ in range(10))}"

def generate_custom_schedule_id():
    chars = string.ascii_letters + string.digits
    return f"schdle{''.join(secrets.choice(chars) for _ in range(10))}"

# ------------------------------
# ExamSchedule Model
# ------------------------------
class ExamSchedule(models.Model):
    id = models.CharField(
        primary_key=True,
        default=generate_custom_schedule_id,
        editable=False,
        max_length=20,
        unique=True
    )

    exam_name = models.CharField(max_length=255, null=True, blank=True)
    exam_date = models.DateField(null=True, blank=True)
    exam_start_time = models.CharField(max_length=8, null=True, blank=True)  # Format: 'HH:MM:SS'
    exam_end_time = models.CharField(max_length=8, null=True, blank=True)   
    def __str__(self):
        return f"Schedule for {self.exam_name} on {self.exam_date} at {self.exam_time}"

    class Meta:
        db_table = 'Schedules'

# ------------------------------
# User   Model
# ------------------------------
class User(AbstractUser):
    id = models.CharField(
        primary_key=True,
        default=generate_custom_user_id,
        editable=False,
        max_length=20,
        unique=True
    )

    full_name = models.CharField(max_length=255)
    roll_number = models.CharField(max_length=225, blank=True, null=True)
    email = models.EmailField(unique=True)
    college_code = models.CharField(max_length=225, blank=True, null=True)
    score = models.CharField(max_length=225, blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)

    exam = models.ForeignKey(
        ExamSchedule,
        on_delete=models.CASCADE,
        related_name='user_sessions',
        null=True, blank=True
    )

    groups = models.ManyToManyField(
        Group,
        related_name='user_groups',
        blank=True,
        help_text='The groups this user belongs to.',
        verbose_name='groups'
    )
    user_permissions = models.ManyToManyField(
        Permission,
        related_name='user_permissions_set',
        blank=True,
        help_text='Specific permissions for this user.',
        verbose_name='user permissions'
    )

    def __str__(self):
        return f"{self.full_name}"

    class Meta:
        db_table = 'users'

# ------------------------------
# Admins Model
# ------------------------------
class Admins(AbstractUser):
    id = models.CharField(
        primary_key=True,
        default=generate_custom_user_id,
        editable=False,
        max_length=20,
        unique=True
    )



    username = models.CharField(max_length=225)  # Remove the username field
    email = models.EmailField(unique=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    password = models.CharField(max_length=225)

    groups = models.ManyToManyField(
        Group,
        related_name='admin_groups',
        blank=True,
        help_text='The groups this admin belongs to.',
        verbose_name='groups'
    )
    user_permissions = models.ManyToManyField(
        Permission,
        related_name='admin_permissions_set',
        blank=True,
        help_text='Specific permissions for this admin.',
        verbose_name='user permissions'
    )

    def __str__(self):
        return f"{self.email}"

    class Meta:
        db_table = 'admin'

# ------------------------------
# ExamQuestion Model
# ------------------------------
class ExamQuestion(models.Model):
    id = models.CharField(
        primary_key=True,
        default=generate_custom_question_id,
        editable=False,
        max_length=20,
        unique=True
    )
    question = models.TextField()
    option_1 = models.CharField(max_length=255)
    option_2 = models.CharField(max_length=255)
    option_3 = models.CharField(max_length=255)
    option_4 = models.CharField(max_length=255)
    correct_answer = models.CharField(max_length=255)

    def __str__(self):
        return self.question

    class Meta:
        db_table = 'Questions'
