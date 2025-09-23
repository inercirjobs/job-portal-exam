from django.urls import path, include,re_path
from rest_framework.routers import DefaultRouter
from . import views


router = DefaultRouter()
router.register(r'users', views.UserViewSet)

urlpatterns = [
    
    


    
    
    # path('contact', views.contact_view, name='contact'),
    path('add-admin/', views.AddAdminView.as_view(), name='add-admin'),
    path('admin-login/', views.AdminLoginView.as_view(), name='admin-login'),
    path('add-question/', views.AddExamQuestionView.as_view(), name='add-question'),
    path('add-schedule/', views.AddExamScheduleView.as_view(), name='add-schedule'),

    path('start-exam/', views.StartExamView.as_view(), name='start-exam'),
    path('submit-score/<str:session_id>/', views.SubmitScoreView.as_view(), name='submit-score'),

    path('exam-questions/', views.ExamQuestionListView.as_view(), name='exam-questions'),
    path('exam-schedules/', views.ExamScheduleListView.as_view(), name='exam-schedules'),
    path('admins/', views.AdminListView.as_view(), name='admins-list'),
    path('users/', views.UserListView.as_view(), name='users-list'),
    path('delete-user/<str:id>/', views.delete_user_view, name='delete-user'),

    path('edit-question/<str:id>/', views.edit_exam_question, name='edit-question'),
    path('delete-question/<str:id>/', views.delete_exam_question, name='delete-question'),
    path('edit-schedule/<str:id>/', views.edit_exam_schedule, name='edit-schedule'),
    path('delete-schedule/<str:id>/', views.delete_exam_schedule, name='delete-schedule'),

    # API routes
    path('', include(router.urls)),
]
