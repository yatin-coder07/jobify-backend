import hashlib
import traceback
import requests
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from django.core.cache import cache
from .serializers import ResumeSerializer
from ai.services.resume_ingestion_service import ResumeIngestionService
from ai.models import Resume 

def report_debug(data):
    print(f"DEBUG LOG TRIGGERED: {data.get('event')}", flush=True)
    try:
        requests.post("http://127.0.0.1:7777/event", json=data, timeout=1)
    except:
        pass


class ResumeUploadView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            report_debug({
                "event": "resume_upload_start",
                "user": str(request.user)
            })

            if 'original_file' not in request.FILES:
                return Response({"error": "No file uploaded"}, status=status.HTTP_400_BAD_REQUEST)

            uploaded_file = request.FILES['original_file']

            # ==================================================================
            # ⚡ STEP 1: IMMEDIATE CACHE CHECK (THE SHIELD)
            # ==================================================================
            # Read the incoming file stream bytes to calculate its unique fingerprint
            file_content = uploaded_file.read()
            file_hash = hashlib.md5(file_content).hexdigest()
            
            # CRITICAL: Always rewind the stream pointer so downstream parsers can read it!
            uploaded_file.seek(0)  

            # Build a dynamic composite key tied to this specific user profile
            cache_key = f"user_resume_hash:{request.user.id}:{file_hash}"
            print(f"🔍 [CACHE INSPECTION] Checking key: {cache_key}")

            # Look up the fingerprint inside Redis memory
            cached_resume_id = cache.get(cache_key)

            if cached_resume_id:
                # Double-check that the row wasn't manually purged from PostgreSQL
                if Resume.objects.filter(id=cached_resume_id).exists():
                    report_debug({
                        "event": "global_cache_hit_intercept",
                        "resume_id": str(cached_resume_id),
                        "file_hash": file_hash
                    })
                    print(f"⚡ [REDIS HIT] Found signature match! Short-circuiting pipeline for ID: {cached_resume_id}")
                    return Response(
                        {
                            "message": "Resume retrieved from cache successfully",
                            "resume_id": str(cached_resume_id),
                            "cached": True
                        },
                        status=status.HTTP_201_CREATED
                    )

            # ==================================================================
            # ❄️ STEP 2: CACHE MISS PIPELINE (RUNS ONLY ON NEW FILES)
            # ==================================================================
            print("❄️ [CACHE MISS] Processing new file footprint. Initiating parsing engine...")
            
            serializer = ResumeSerializer(data=request.data)
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            # Persist data footprint to PostgreSQL database tables
            resume = serializer.save(user=request.user)

            report_debug({
                "event": "ingestion_start",
                "resume_id": str(resume.id)
            })

            # Call your pipeline to extract text blocks and process Gemini embeddings
            ResumeIngestionService.process_resume(resume)

            report_debug({
                "event": "ingestion_success",
                "resume_id": str(resume.id)
            })

            # Save the successful file hash signature into Redis for 7 days
            try:
                cache.set(cache_key, str(resume.id), timeout=86400 * 7)
                print(f"💾 [CACHE SAVE] Cached file fingerprint under key: {cache_key}")
            except Exception as cache_err:
                print(f"⚠️ Warning: Failed to populate cache storage matrix: {str(cache_err)}")

            return Response(
                {
                    "message": "Resume uploaded successfully",
                    "resume_id": str(resume.id),
                    "cached": False
                },
                status=status.HTTP_201_CREATED
            )

        except Exception as e:
            error_trace = traceback.format_exc()
            report_debug({
                "event": "resume_upload_exception",
                "error": str(e),
                "traceback": error_trace
            })
            print(error_trace, flush=True)
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)