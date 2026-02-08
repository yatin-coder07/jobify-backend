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
    portfolio_link=models.URLField(blank=True,null=True)
    linkedin_link=models.URLField(blank=True,null=True)

    def __str__(self):
        return self.full_name
    

class Experience(models.Model):
    candidate = models.ForeignKey(
        CandidateProfile,
        on_delete=models.CASCADE,
        related_name="experiences"
    )
    company_name = models.CharField(max_length=150)
    role = models.CharField(max_length=150)
    role_description=models.TextField(null=True)
    start_date = models.DateField()
    end_date = models.DateField(blank=True, null=True)
    is_current = models.BooleanField(default=False)
   

    def __str__(self):
        return f"{self.role} at {self.company_name}"

class Education(models.Model):
    candidate = models.ForeignKey(
        CandidateProfile,
        on_delete=models.CASCADE,
        related_name="educations"
    )
    institution = models.CharField(max_length=150)
    degree = models.CharField(max_length=150)
    start_year = models.IntegerField()
    end_year = models.IntegerField(blank=True, null=True)
    is_current=models.BooleanField(default=False)

    def __str__(self):
        return f"{self.degree} - {self.institution}"


class EmployerProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    company_name = models.CharField(max_length=150)
    description = models.TextField(null=True)
    linkedin_link=models.URLField(blank=True, null=True)  
    website_link = models.URLField(blank=True)
    about_company= models.TextField(null=True)
    location = models.CharField(max_length=100)
    logo = models.URLField(blank=True, null=True)

    def __str__(self):
        return self.company_name
    
class Skill(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name
