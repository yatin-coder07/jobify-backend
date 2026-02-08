from rest_framework import serializers
from .models import JobApplication

class JobApplicationSerializer(serializers.ModelSerializer):
    job_title = serializers.CharField(source="job.title", read_only=True)
    job_location = serializers.CharField(source="job.location", read_only=True)
    candidate_name = serializers.CharField(
        source="candidate.candidateprofile.full_name",
        read_only=True
    )
    

    candidate_profile_image = serializers.URLField(
        source="candidate.candidateprofile.profile_image",
        read_only=True
    )
    candidate_profile_id = serializers.IntegerField(
        source="candidate.candidateprofile.id",
        read_only=True
    )

    class Meta:
        model = JobApplication
        fields = "__all__"
        
        read_only_fields = ["applied_at"]
