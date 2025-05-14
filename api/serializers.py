from rest_framework import serializers
from Chat.models import ProgramCategory, Program, Admission, Exam, LearningSupportCenter, RegionalCenter, Faq, NewsUpdate, Feedback


class ProgramCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ProgramCategory
        fields = '__all__'

class ProgramSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    
    class Meta:
        model = Program
        fields = ['id', 'name', 'category', 'category_name', 'duration', 'mode', 'description', 'fee_structure', 'eligibility']

class AdmissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Admission
        fields = '__all__'

class ExamSerializer(serializers.ModelSerializer):
    class Meta:
        model = Exam
        fields = '__all__'

class LearningSupportCenterSerializer(serializers.ModelSerializer):
    class Meta:
        model = LearningSupportCenter
        fields = '__all__'

class RegionalCenterSerializer(serializers.ModelSerializer):
    class Meta:
        model = RegionalCenter
        fields = '__all__'

class FaqSerializer(serializers.ModelSerializer):
    class Meta:
        model = Faq
        fields = '__all__'

class NewsUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = NewsUpdate
        fields = '__all__'

class FeedbackSerializer(serializers.ModelSerializer):
    class Meta:
        model = Feedback
        fields = '__all__'