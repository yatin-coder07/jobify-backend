from rest_framework import serializers
from .models import Job

class JobSerializer(serializers.ModelSerializer):
    company_name = serializers.CharField(
        source="employer.employerprofile.company_name",
        read_only=True
    )
    company_logo = serializers.URLField(
        source="employer.employerprofile.logo",
        read_only=True
    )
    company_location = serializers.CharField(
        source="employer.employerprofile.location",
        read_only=True
    )
    company_website = serializers.URLField(
        source="employer.employerprofile.website_link",
        read_only=True
    )

    class Meta:
        model = Job
        fields = [
            "id",
            "title",
            "description",
            "location",
            "experience_level",
            "work_mode",
            "job_type",
            "salary",
            "company_name",
            "company_logo",
            "company_location",
            "company_website",
            "created_at",
        ]