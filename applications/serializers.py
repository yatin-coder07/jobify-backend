from rest_framework import serializers
from .models import JobApplication

class JobApplicationSerializer(serializers.ModelSerializer):
    job_title = serializers.CharField(source="job.title", read_only=True)
    job_location = serializers.CharField(source="job.location", read_only=True)

    class Meta:
        model = JobApplication
        fields = [
            "id",
            "job_title",
            "job_location",
            "cover_letter",
            "resume",
            "applied_at",
        ]
        read_only_fields = ["applied_at"]