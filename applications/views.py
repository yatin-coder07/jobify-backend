from django.shortcuts import render

# Create your views here.
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

from .models import JobApplication
from .serializers import JobApplicationSerializer
from jobs.models import Job

from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from .models import JobApplication
from .serializers import JobApplicationSerializer
from jobs.models import Job
from utils.supabase import upload_file

class ApplyJobView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, job_id):
        print("=== APPLY JOB HIT ===")

        try:
            job = Job.objects.get(id=job_id)
        except Job.DoesNotExist:
            print("JOB NOT FOUND")
            return Response({"error": "Job not found"}, status=404)

        if JobApplication.objects.filter(
            job=job, candidate=request.user
        ).exists():
            print("ALREADY APPLIED")
            return Response(
                {"error": "Already applied"},
                status=status.HTTP_400_BAD_REQUEST
            )

        resume_file = request.FILES.get("resume")
        print("RESUME FILE:", resume_file)

        if not resume_file:
            return Response(
                {"error": "Resume missing"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            resume_url = upload_file(resume_file, resume_file.name)
            print("RESUME URL:", resume_url)
        except Exception as e:
            print("UPLOAD FAILED:", str(e))
            return Response(
                {"error": "Resume upload failed"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        application = JobApplication.objects.create(
            job=job,
            candidate=request.user,
            cover_letter=request.data.get("cover_letter", ""),
            resume_url=resume_url,
        )

        return Response(
            JobApplicationSerializer(application).data,
            status=status.HTTP_201_CREATED
        )



class EmployerApplicationsView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        applications = JobApplication.objects.filter(
            job__employer=request.user
        )
        serializer = JobApplicationSerializer(applications, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class CandidateApplicationsView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self , request):
        applications = JobApplication.objects.filter(candidate=request.user)
        serializer=JobApplicationSerializer(applications, many = True)
        return Response(serializer.data, status=status.HTTP_200_OK)
class DeleteApplicationView(APIView):
    permission_classes = [IsAuthenticated]
    def delete(self, request, application_id):
        try:
            application = JobApplication.objects.get(id=application_id, candidate=request.user)
        except JobApplication.DoesNotExist:
            return Response({"error": "Application not found"}, status=status.HTTP_404_NOT_FOUND)
        application.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)