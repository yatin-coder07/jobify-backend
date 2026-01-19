from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from urllib3 import request

from .models import Job
from .serializers import JobSerializer
from .permissions import IsEmployer
from rest_framework import generics, permissions
from .models import Job


# Create your views here.
class JobCreateView(APIView):
    permission_classes = [IsAuthenticated, IsEmployer]

    def post(self, request):
        serializer = JobSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save(employer=request.user)
            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )
class JobListView(APIView):
    def get(self, request):
        search = request.query_params.get("search")
        jobs = Job.objects.all().order_by("-created_at")

        if search:
            jobs = jobs.filter(
                Q(title__icontains=search) |
                Q(location__icontains=search)
            )

        serializer = JobSerializer(jobs, many=True)
        return Response(serializer.data)


class EmployerJobListView(APIView):
    permission_classes = [IsAuthenticated, IsEmployer]

    def get(self, request):
        jobs = Job.objects.filter(employer=request.user)
        serializer = JobSerializer(jobs, many=True)
        return Response(serializer.data)


class JobDetailView(generics.RetrieveUpdateAPIView):
    queryset = Job.objects.all()
    serializer_class = JobSerializer
    permission_classes = [permissions.IsAuthenticated]

class JobDeleteView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, job_id):
        job = get_object_or_404(
            Job,
            id=job_id,
            employer=request.user 
        )

        job.delete()
        return Response(
            {"message": "Job deleted successfully"},
            status=status.HTTP_204_NO_CONTENT
        )