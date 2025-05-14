from django.urls import path
from . import views

urlpatterns = [
    path('education/', views.education_query, name='education'),
    path('certification/', views.certification_query, name='certification'),
    path('learning-center/', views.learning_center_query, name='learning_center'),
    path('programs/', views.program_query, name='programs'),
]