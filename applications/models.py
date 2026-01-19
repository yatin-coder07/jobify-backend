from django.conf import settings
from django.db import models
from jobs.models import Job

User = settings.AUTH_USER_MODEL

class JobApplication(models.Model):
    # Fields for the JobApplication model
   job=models.ForeignKey(
      Job,
      on_delete=models.CASCADE,
        related_name="applications"
   )
   candidate=models.ForeignKey(
      User,
      on_delete=models.CASCADE,
        related_name="applications"
   )
   resume_url = models.URLField()
   cover_letter=models.TextField(blank=True)
   applied_at=models.DateTimeField(auto_now_add=True)