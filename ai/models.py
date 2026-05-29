from django.db import models
import uuid
from django.contrib.auth.models import User
from pgvector.django import VectorField



class Resume(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="resumes"
    )

    original_file = models.FileField(upload_to="resumes/")

    extracted_text = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.email} Resume"
    


class ResumeChunk(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    resume = models.ForeignKey(
        Resume,
        on_delete=models.CASCADE,
        related_name="chunks"
    )

    section = models.CharField(max_length=100)

    chunk_text = models.TextField()

    embedding = VectorField(
        dimensions=3072,
        null=True
    )

    metadata = models.JSONField(default=dict)

    created_at = models.DateTimeField(auto_now_add=True)