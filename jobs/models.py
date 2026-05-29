from pgvector.django import VectorField
from django.db import models
from django.contrib.auth.models import User

class Job(models.Model):
    EXPERIENCE_CHOICES = [
        ("intern", "Intern"),
        ("entry", "Entry Level"),
        ("senior", "Senior Level"),
    ]
    employer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="jobs"
    )
    title = models.CharField(max_length=200)
    description = models.TextField()
    location = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    experience_level = models.CharField(max_length=30, choices=EXPERIENCE_CHOICES, null=True)
    work_mode = models.CharField(max_length=20, null=True)
    job_type = models.CharField(max_length=20, null=True)
    salary = models.CharField(max_length=50, null=True)

    def __str__(self):
        return self.title


class JobChunk(models.Model):
    job = models.ForeignKey(
        "Job",
        on_delete=models.CASCADE,
        related_name="chunks"
    )
    section = models.CharField(max_length=100, default="general")
    chunk_text = models.TextField()
    
    # Matches your ResumeChunk field layout completely
    embedding = VectorField(dimensions=3072, null=True) 
    metadata = models.JSONField(default=dict)

    def __str__(self):
        return f"Chunk for {self.job.title} - {self.section}"
    
    