import logging
from django.shortcuts import render
from django.db.models import Q
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

from .models import JobApplication
from .serializers import JobApplicationSerializer
from jobs.models import Job
from utils.supabase import upload_file

# Import the clean agent handler from the AI workspace application layer
from ai.services.agent_service import AIApplicationAgent
from ai.models import Resume

logger = logging.getLogger(__name__)

class ApplyJobView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, job_id):
        if not request.FILES:
            return Response(
                {"error": "Request must be multipart/form-data"},
                status=status.HTTP_400_BAD_REQUEST
            )

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
            resume_url = upload_file(resume_file, "resumes")
            print("RESUME URL:", resume_url)
        except Exception as e:
            print("UPLOAD FAILED:", str(e))
            return Response(
                {"error": "Resume upload failed"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        # ⚡ OPTIONAL STEP: Grab the most recent processed active Resume instance 
        # or fallback to None if it hasn't been parsed inside the `ai` engine yet.
        active_resume = Resume.objects.filter(user=request.user).order_by('-created_at').first()

        # 🚀 Step 1: Initialize the Application Row with a 'pending_approval' status floor
        application = JobApplication.objects.create(
            job=job,
            candidate=request.user,
            resume=active_resume,
            resume_url=resume_url,
            cover_letter="Drafting in progress...",
            status="pending_approval"
        )

        try:
            # 🚀 Step 2: Trigger the agent workflow (user_has_approved=False).
            # The agent creates the cover letter, calls tool 1 to overwrite "Drafting in progress...", and stops.
            AIApplicationAgent.run_workflow(application_id=application.id, user_has_approved=False)
            
            # Refresh from database memory block to return the freshly synthesized cover letter to frontend
            application.refresh_from_db()
        except Exception as agent_err:
            logger.error(f"Agent failed to draft letter initially: {str(agent_err)}")
            application.status = "failed"
            application.save()

        return Response(
            JobApplicationSerializer(application).data,
            status=status.HTTP_201_CREATED
        )


class ConfirmAgentSubmissionView(APIView):
    """
    Endpoint for Human-In-The-Loop explicit approval confirmation.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, application_id):
        action = request.data.get("action")  # Expected options: "APPROVE" or "REJECT"
        user_edited_letter = request.data.get("cover_letter", None)

        try:
            application = JobApplication.objects.get(id=application_id, candidate=request.user)
        except JobApplication.DoesNotExist:
            return Response({"error": "Application context row not found"}, status=status.HTTP_404_NOT_FOUND)

        if action == "REJECT":
            application.status = "rejected"
            application.save()
            return Response({"message": "Application rejected and closed by user."}, status=status.HTTP_200_OK)

        if action == "APPROVE":
            # If user sent over modifications, save it right before submitting
            if user_edited_letter:
                application.cover_letter = user_edited_letter
                application.save()

            # Set the approval flag to True. The agent skips the drafting block,
            # triggers Tool 2 (automation tool), and flips state to 'applied'.
            try:
                application.status = "approved"
                application.save()

                AIApplicationAgent.run_workflow(
                    application_id=application.id,
                    user_has_approved=True,
                    final_letter_text=application.cover_letter
                )

                application.refresh_from_db()
                return Response({
                    "message": "Agent execution approved. Automated submission successful.",
                    "application": JobApplicationSerializer(application).data
                }, status=status.HTTP_200_OK)

            except Exception as e:
                application.status = "failed"
                application.save()
                return Response({"error": f"Automation pipeline failed: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({"error": "Invalid action value passed"}, status=status.HTTP_400_BAD_REQUEST)


class EmployerApplicationsView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, job_id):
        try:
            job = Job.objects.get(id=job_id, employer=request.user)
        except Job.DoesNotExist:
            return Response({"error": "Job not found"}, status=status.HTTP_404_NOT_FOUND)
        applications = JobApplication.objects.filter(job=job)
        serializer = JobApplicationSerializer(applications, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def get(self, request):
        search = request.query_params.get("search", "")
        applications = JobApplication.objects.filter(
            job__employer=request.user
        )
        if search:
            applications = applications.filter(
                Q(candidate__first_name__icontains=search) |
                Q(job__title__icontains=search)
            )
        serializer = JobApplicationSerializer(applications, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request, application_id):
        try:
            application = JobApplication.objects.get(
                id=application_id,
                job__employer=request.user
            )
        except JobApplication.DoesNotExist:
            return Response({"error": "Application not found"}, status=404)

        serializer = JobApplicationSerializer(
            application,
            data=request.data,
            partial=True
        )

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=200)

        return Response(serializer.errors, status=400)

    def delete(self, request, application_id):
        try:
            application = JobApplication.objects.get(id=application_id, job__employer=request.user)
        except JobApplication.DoesNotExist:
            return Response({"error": "Application not found"}, status=status.HTTP_404_NOT_FOUND)
        application.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class CandidateApplicationsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        applications = JobApplication.objects.filter(candidate=request.user)
        serializer = JobApplicationSerializer(applications, many=True)
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