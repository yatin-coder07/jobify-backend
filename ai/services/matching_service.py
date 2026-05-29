import logging
from django.db.models import F
from pgvector.django import CosineDistance
from ai.models import Resume
from jobs.models import Job, JobChunk

logger = logging.getLogger(__name__)

class SemanticMatchingService:

    @classmethod
    def get_jobs_for_resume(cls, resume_id: str, limit: int = 5):
        """
        Queries JobChunks against ALL vector chunks of a resume, aggregates scores,
        and applies a strict keyword/title hybrid boost to filter out irrelevant roles.
        """
        try:
            # 1. Fetch the requested clean resume database object
            try:
                resume = Resume.objects.get(id=resume_id)
            except Resume.DoesNotExist:
                logger.warning(f"Resume {resume_id} not found")
                return []

            # 2. Extract valid vector blocks belonging to this specific resume instance
            resume_chunks = resume.chunks.filter(embedding__isnull=False)
            if not resume_chunks.exists():
                logger.warning(f"No embeddings found for Resume {resume_id}")
                return []

            # Multi-vector extraction map
            resume_vectors = [chunk.embedding for chunk in resume_chunks]

            # Matrix dictionary holding aggregated matching lists per unique Job model row
            job_scores = {}

            # High-priority technical keyword validation set
            tech_keywords = {"ai", "engineer", "developer", "stack", "software", "backend", "frontend", "python"}

            # 3. Comprehensive Multi-Chunk Loop Search
            for vector in resume_vectors:
                # Query nearest neighbor vectors with a tightened structural distance radius boundary
                matched_chunks = JobChunk.objects.filter(embedding__isnull=False).annotate(
                    distance=CosineDistance('embedding', vector)
                ).filter(distance__lt=0.42).select_related('job')

                for chunk in matched_chunks:
                    job = chunk.job
                    # Convert raw geometric distance score into intuitive percentage accuracy
                    similarity_score = round((1 - chunk.distance) * 100, 2)
                    
                    if job not in job_scores:
                        job_scores[job] = []
                    job_scores[job].append(similarity_score)

            if not job_scores:
                return []

            # 4. Hybrid Context Boosting & Scoring Aggregations
            final_ranked_jobs = []
            for job, scores in job_scores.items():
                # Pin base metric on the highest-matching document sub-block 
                base_score = max(scores)
                title_lower = job.title.lower()
                
                # Check cross-relevance match counts against tech keyword matrix
                keyword_matches = sum(1 for word in tech_keywords if word in title_lower)
                
                if keyword_matches >= 2:
                    # Provide an immediate score boost for core engineering titles
                    final_score = min(base_score + 15.0, 100.0)
                elif any(bad_word in title_lower for bad_word in ["assistant", "manager", "operations"]) and not any(tech in title_lower for tech in ["ai", "engineer"]):
                    # Penalize non-technical operations positions to suppress them
                    final_score = base_score - 25.0
                else:
                    final_score = base_score

                job.match_score = round(final_score, 2)
                
                # 🚀 ELITE FILTRATION GATEWAY: Drop everything falling below the 70.0% bar
                if job.match_score >= 70.0:
                    final_ranked_jobs.append(job)

            # 5. Descending High-Score Priority Sorting Order
            final_ranked_jobs.sort(key=lambda x: x.match_score, reverse=True)

            return final_ranked_jobs[:limit]

        except Exception as e:
            logger.error(f"Failed to execute semantic search: {str(e)}")
            raise e