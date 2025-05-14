from django.shortcuts import render
from rest_framework import generics
from Chat.models import ProgramCategory, Program, Admission, Exam, LearningSupportCenter, RegionalCenter, Faq, NewsUpdate, Feedback
from .serializers import (
    ProgramCategorySerializer, ProgramSerializer, AdmissionSerializer, 
    ExamSerializer, LearningSupportCenterSerializer, RegionalCenterSerializer, 
    FaqSerializer, NewsUpdateSerializer, FeedbackSerializer
)

# Create your views here.

class ProgramCategoryList(generics.ListCreateAPIView):
    queryset = ProgramCategory.objects.all()
    serializer_class = ProgramCategorySerializer

class ProgramList(generics.ListCreateAPIView):
    queryset = Program.objects.select_related('category').all()
    serializer_class = ProgramSerializer

class AdmissionList(generics.ListCreateAPIView):
    queryset = Admission.objects.all()
    serializer_class = AdmissionSerializer  

class ExamList(generics.ListCreateAPIView):
    queryset = Exam.objects.all()
    serializer_class = ExamSerializer

class LearningSupportCenterList(generics.ListCreateAPIView):
    queryset = LearningSupportCenter.objects.all()
    serializer_class = LearningSupportCenterSerializer

class RegionalCenterList(generics.ListCreateAPIView):
    queryset = RegionalCenter.objects.all()
    serializer_class = RegionalCenterSerializer

class FaqList(generics.ListCreateAPIView):
    queryset = Faq.objects.all()
    serializer_class = FaqSerializer

class NewsUpdateList(generics.ListCreateAPIView):
    queryset = NewsUpdate.objects.all()
    serializer_class = NewsUpdateSerializer

class FeedbackList(generics.ListCreateAPIView):
    queryset = Feedback.objects.all()
    serializer_class = FeedbackSerializer