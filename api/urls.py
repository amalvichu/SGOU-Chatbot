from django.urls import path
from .views import *

urlpatterns = [
    path('program-categories/', ProgramCategoryList.as_view(), name='program-list'),
    path('programs/<int:pk>/', ProgramList.as_view(), name='program-detail'),
    path('admissions/', AdmissionList.as_view(), name='admission-list'),
    path('exams/', ExamList.as_view(), name='exam-list'),
    path('learning-centers/', LearningSupportCenterList.as_view(), name='learning-center-list'),
    path('regional-centers/', RegionalCenterList.as_view(), name='regional-center-list'),
    path('faqs/', FaqList.as_view(), name='faq-list'),
    path('news/', NewsUpdateList.as_view(), name='news-list'),
    path('feedback/', FeedbackList.as_view(), name='feedback-list'),
]