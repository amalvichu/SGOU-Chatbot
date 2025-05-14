from django.shortcuts import render
from django.http import JsonResponse
from Chat.models import Program, ProgramCategory


def program_query(request):
    programs = Program.objects.all()
    data = [
        {
            'name': program.name,
            'category': program.category.name,
            'duration': program.duration,
            'description': program.description
        }
        for program in programs
    ]
    return JsonResponse(data, safe=False)

# Create your views here.