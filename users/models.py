from django.db import models
from django.contrib.auth.models import User

class Profile(models.Model):
    ROLE_CHOICES = (
        ('employer', 'Employer'),
        ('candidate', 'Candidate'),
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)

    def __str__(self):
        return f"{self.user.username} - {self.role}"

class CandidateProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    full_name=models.CharField(max_length=20)
    profile_image=models.URLField(blank=True, null=True)
    bio=models.TextField(blank=True)
    skills = models.ManyToManyField("Skill", blank=True)
    resume = models.URLField( blank=True, null=True)

    def __str__(self):
        return self.full_name
    
class EmployerProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    company_name = models.CharField(max_length=150)
    description = models.TextField()
    website = models.URLField(blank=True)
    industry = models.CharField(max_length=100)
    location = models.CharField(max_length=100)
    logo = models.URLField(blank=True, null=True)

    def __str__(self):
        return self.company_name
    
class Skill(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name
