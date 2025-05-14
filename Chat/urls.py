from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('programs/', views.get_programs, name='get_programs'),
]