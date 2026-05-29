import logging
import threading
from django.shortcuts import get_object_or_404
from django.db.models import Q
from django.core.cache import cache
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, generics, permissions
from rest_framework.permissions import IsAuthenticated
from ai.services.matching_service import SemanticMatchingService

from .models import Job
from .serializers import JobSerializer
from .permissions import IsEmployer
from ai.services.job_ingestion_service import JobIngestionService

# Standardize logger naming for your application monitoring setups
logger = logging.getLogger("jobify.jobs.views")

# Global Cache Key Definitions
CACHE_TTL_JOBS = 60 * 15  # 15 Minutes cache window for list queries
CACHE_KEY_PREFIX_DETAIL = "job_detail:"

def _clear_global_job_caches(job_id=None):
    """ Helper to flush query keys whenever data mutations occur """
    try:
        # Clear specific lists and the modified detail instance cache
        cache.delete_pattern("job_list:*")
        if job_id:
            cache.delete(f"{CACHE_KEY_PREFIX_DETAIL}{job_id}")
        logger.info(f"[Cache Flush] Successfully cleared job cache layers for mutation.")
    except AttributeError:
        # Falling back gracefully if the cache backend doesn't support pattern matching
        cache.delete("job_list_default")
        if job_id:
            cache.delete(f"{CACHE_KEY_PREFIX_DETAIL}{job_id}")


def _async_pipeline_wrapper(job):
    """
    Handles background execution context cleanly, catching exceptions 
    and generating precise system logs.
    """
    logger.info(f"[Background Pipeline] Starting async job ingestion for Job ID: {job.id}")
    try:
        success = JobIngestionService.process_job(job)
        if success:
            logger.info(f"[Background Pipeline] Ingestion completed successfully for Job ID: {job.id}")
        else:
            logger.error(f"[Background Pipeline] Ingestion pipeline failed or returned false for Job ID: {job.id}")
    except Exception as e:
        logger.critical(f"[Background Pipeline] CRITICAL ERROR during ingestion for Job ID {job.id}: {str(e)}", exc_info=True)


class JobCreateView(APIView):
    permission_classes = [IsAuthenticated, IsEmployer]

    def post(self, request):
        logger.info(f"[Job Creation Started] User {request.user.id} attempting to post a job.")
        serializer = JobSerializer(data=request.data)

        if serializer.is_valid():
            # 1. Save data record transactionally
            job = serializer.save(employer=request.user)
            logger.info(f"[Job Database Saved] Created Base Job Record ID: {job.id}")

            # 2. Invalidate older cached lists now that new content exists
            _clear_global_job_caches()

            # 3. Offload text parsing + clean operations + Gemini vectorizations safely
            threading.Thread(
                target=_async_pipeline_wrapper,
                args=(job,),
                daemon=True
            ).start()

            # 4. Return success response instantly, detailing background processing state
            response_data = serializer.data
            response_data["ingestion_status"] = "processing"
            
            return Response(
                response_data,
                status=status.HTTP_201_CREATED
            )

        logger.warning(f"[Job Creation Validation Error] User {request.user.id} provided faulty data: {serializer.errors}")
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )


class JobListView(APIView):
    def get(self, request):
        search = request.query_params.get("search", "").strip()
        
        # Build deterministic caching key matching search mutations
        cache_key = f"job_list:query_{search if search else 'all'}"
        cached_data = cache.get(cache_key)
        
        if cached_data is not None:
            logger.info(f"[Cache Hit] Serving job listings query matching '{search}' directly from Redis.")
            return Response(cached_data)

        logger.info(f"[Cache Miss] Fetching fresh job list records matching query '{search}' from database.")
        jobs = Job.objects.all().order_by("-created_at")

        if search:
            jobs = jobs.filter(
                Q(title__icontains=search) |
                Q(location__icontains=search)
            )

        serializer = JobSerializer(jobs, many=True)
        serialized_data = serializer.data
        
        # Cache results back down to your Redis cluster instance
        cache.set(cache_key, serialized_data, timeout=CACHE_TTL_JOBS)
        
        return Response(serialized_data)


class EmployerJobListView(APIView):
    permission_classes = [IsAuthenticated, IsEmployer]

    def get(self, request):
        # We generally do not cache this or use highly short TTLs since it's a dynamic dashboard route
        logger.info(f"[Recruiter Request] Fetching workspace listings for employer user {request.user.id}")
        jobs = Job.objects.filter(employer=request.user).order_by("-created_at")
        serializer = JobSerializer(jobs, many=True)
        return Response(serializer.data)


class JobDetailView(generics.RetrieveUpdateAPIView):
    queryset = Job.objects.all()
    serializer_class = JobSerializer
    permission_classes = [permissions.IsAuthenticated]

    def retrieve(self, request, *args, **kwargs):
        job_id = kwargs.get("pk")
        cache_key = f"{CACHE_KEY_PREFIX_DETAIL}{job_id}"
        
        cached_job = cache.get(cache_key)
        if cached_job is not None:
            logger.info(f"[Cache Hit] Serving Job Detail ID: {job_id} from Redis.")
            return Response(cached_job)
            
        logger.info(f"[Cache Miss] Querying detail context parameters for Job ID: {job_id} from database.")
        response = super().retrieve(request, *args, **kwargs)
        
        # Commit back to state manager
        cache.set(cache_key, response.data, timeout=CACHE_TTL_JOBS)
        return response

    def perform_update(self, serializer):
        job = serializer.save()
        logger.info(f"[Job Update Occurred] Recruiter modified attributes on Job ID: {job.id}")
        
        # Flush outdated instances across list caches and direct details entries
        _clear_global_job_caches(job_id=job.id)

        # Trigger indexing engine loop routines asynchronously to re-align vector values
        threading.Thread(
            target=_async_pipeline_wrapper,
            args=(job,),
            daemon=True
        ).start()


class JobDeleteView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, job_id):
        logger.info(f"[Job Deletion Requested] Attempting removal of Job ID: {job_id} by User: {request.user.id}")
        job = get_object_or_404(
            Job,
            id=job_id,
            employer=request.user 
        )

        job.delete()
        logger.info(f"[Job Deletion Complete] Dropped Job ID: {job_id} successfully.")
        
        # Flush all references out of cache memory to prevent ghost responses
        _clear_global_job_caches(job_id=job_id)
        
        return Response(
            {"message": "Job deleted successfully"},
            status=status.HTTP_204_NO_CONTENT
        )
    
class ResumeMatchJobAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, resume_id):
        """
        GET endpoint returning a sorted list of jobs contextually 
        closest to the scanned resume structure.
        """
        try:
            # Pull the top 5 closest matching job posts
            matched_jobs = SemanticMatchingService.get_jobs_for_resume(resume_id=resume_id, limit=5)
            
            # Format JSON payload response structure
            results = []
            for job in matched_jobs:
                results.append({
                    "id": job.id,
                    "title": job.title,
                    "location": job.location,
                    "salary": job.salary,
                    "experience_level": job.experience_level,
                    "work_mode": job.work_mode,
                    "match_score": getattr(job, "match_score", 0.0) # Pulled out of instance memory annotation
                })
                
            return Response({"matches": results}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {"error": "Failed to calculate semantic matches.", "details": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )