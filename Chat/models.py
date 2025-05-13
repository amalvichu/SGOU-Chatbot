from django.db import models

# Create your models here.

# PROGRAM CATEGORY
class ProgramCategory(models.Model):
    name = models.CharField(max_length=100)
    duration = models.CharField(max_length=50)

    def __str__(self):
        return self.name

# PROGRAM DETAILS
class Program(models.Model):
    name = models.CharField(max_length=100)
    category = models.ForeignKey(ProgramCategory, on_delete=models.CASCADE, related_name='programs')
    duration = models.CharField(max_length=50)
    mode = models.CharField(max_length=100)
    description = models.TextField()
    fee_structure = models.TextField()
    eligibility = models.TextField()

    def __str__(self):
        return self.name
    
# ADMISSION INFORMATION
class Admission(models.Model):
    program = models.ForeignKey(Program, on_delete=models.CASCADE)
    application_start_date = models.DateField()
    application_end_date = models.DateField()
    application_procedure = models.TextField()

    def __str__(self):
        return f"Admission for {self.program.name}"
    
# EXAM DETAILS
class Exam(models.Model):
    exam_name = models.CharField(max_length=100)
    date = models.DateField()
    details = models.TextField()

    def __str__(self):
        return self.exam_name
    
# LEARNING SUPPORT CENTERS(lSC's)
class LearningSupportCenter(models.Model):
    name = models.CharField(max_length=100)
    address = models.CharField(max_length=200)
    contact_number = models.CharField(max_length=20)

    def __str__(self):
        return self.name

# REGIONAL CENTERS
class RegionalCenter(models.Model):
    name = models.CharField(max_length=100)
    address = models.CharField(max_length=200)
    contact_number = models.CharField(max_length=20)

    def __str__(self):
        return self.name
    
# FAQ
class Faq(models.Model):
    question = models.CharField(max_length=100)
    answer = models.TextField()

    def __str__(self):
        return self.question

# NEWS UPDATE
class NewsUpdate(models.Model):
    title = models.CharField(max_length=100)
    content = models.TextField()
    date = models.DateField()

    def __str__(self):
        return self.title
    
# FEEDBACK
class Feedback(models.Model):
    name = models.CharField(max_length=15)
    email = models.EmailField()
    message = models.TextField()

    def __str__(self):
        return self.name