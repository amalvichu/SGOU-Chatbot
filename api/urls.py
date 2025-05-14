from django.urls import path
from .views import (
    ProgramCategoryList, ProgramList, AdmissionList, 
    ExamList, LearningSupportCenterList, RegionalCenterList, 
    FaqList, NewsUpdateList, FeedbackList
)

urlpatterns = [
    path('program-categories/', ProgramCategoryList.as_view(), name='prorgam-category-list'),
    path('programs/', ProgramList.as_view(), name='program-list'),
    path('admissions/', AdmissionList.as_view(), name='admission-list'),
    path('exams/', ExamList.as_view(), name='exam-list'),
    path('learning-support-centers/', LearningSupportCenterList.as_view(), name='learning-support-center-list'),
    path('regional-centers/', RegionalCenterList.as_view(), name='regional-center-list'),
    path('faqs/', FaqList.as_view(), name='faq-list'),
    path('news-updates/', NewsUpdateList.as_view(), name='news-update-list'),
    path('feedbacks/', FeedbackList.as_view(), name='feedback-list'),
]