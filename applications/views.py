from django.shortcuts import render

# Create your views here.
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

from .models import JobApplication
from .serializers import JobApplicationSerializer
from jobs.models import Job

class ApplyJobView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self,request,job_id):
        try:
          job = Job.objects.get(id=job_id)
        except Job.DoesNotExist:
            return Response({"error": "Job not found"}, status=404)
        if JobApplication.objects.filter(
            job=job, candidate=request.user
        ).exists():
              return Response(
                {"error": "Already applied"},
                status=status.HTTP_400_BAD_REQUEST)
        serializer = JobApplicationSerializer(data = request.data)
        if serializer.is_valid():
            serializer.save(job=job, candidate=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

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