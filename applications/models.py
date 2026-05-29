from django.conf import settings
from django.db import models
from jobs.models import Job
from ai.models import Resume  # Link to your clean AI resume model

User = settings.AUTH_USER_MODEL

class JobApplication(models.Model):

    STATUS_CHOICES = [
        ("new", "New"),
        ("reviewed", "Reviewed"),
        ("accepted", "Accepted"),
        ("rejected", "Rejected"),
        
        # 🚀 New Agentic Workflow States
        ("pending_approval", "Pending Cover Letter Review"),
        ("approved", "Approved - Ready to Submit"),
        ("applied", "Applied via Automation"),
        ("failed", "Automation Error"),
    ]
  
    job = models.ForeignKey(
        Job,
        on_delete=models.CASCADE,
        related_name="applications"
    )
    candidate = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="applications"
    )
    
    # Link the application directly to the structured resume instance used
    resume = models.ForeignKey(
        Resume, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name="applications"
    )
    
    resume_url = models.URLField()
    cover_letter = models.TextField(blank=True)
    applied_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(null=True, choices=STATUS_CHOICES, default="new", max_length=20)

    def __str__(self):
        return f"{self.candidate.username} - {self.job.title} ({self.status})"