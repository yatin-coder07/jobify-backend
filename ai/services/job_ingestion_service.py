import logging
from django.db import transaction
from jobs.models import JobChunk
from ai.chunking.job_chunker import JobChunker
from ai.embeddings.gemini_embedding_service import GeminiEmbeddingService

logger = logging.getLogger(__name__)

class JobIngestionService:

    @classmethod
    def process_job(cls, job):
        """
        Cleans text, resolves embeddings, and processes insertions atomically 
        using optimized bulk operations.
        """
        # 1. Structural multi-section chunk generation
        chunks = JobChunker.chunk_job(job)
        if not chunks:
            logger.warning(f"No text content found to process for Job ID {job.id}")
            return False

        chunks_to_create = []

        try:
            # Wrap database mutations inside an atomic transaction block
            with transaction.atomic():
                
                # 2. Flush previously existing chunks to prevent orphan constraints on updates
                JobChunk.objects.filter(job=job).delete()

                # 3. Process structural nodes
                for chunk in chunks:
                    raw_text = chunk.get("text", "")
                    
                    # Basic inline cleaning: strip leading/trailing whitespace & empty lines
                    cleaned_text = "\n".join([
                        line.strip() for line in raw_text.splitlines() if line.strip()
                    ])
                    
                    # Guard rail: Skip empty strings so we don't waste API tokens
                    if not cleaned_text:
                        continue

                    # 4. Fetch the embedding (relying on your internal EmbeddingCache layer)
                    embedding = GeminiEmbeddingService.generate_embedding(cleaned_text)
                    
                    if embedding is None:
                        logger.error(f"Failed to generate embedding for Job {job.id}, section '{chunk['section']}'")
                        continue

                    # 5. Stage instance memory references for bulk injection
                    chunks_to_create.append(
                        JobChunk(
                            job=job,
                            section=chunk["section"],
                            chunk_text=cleaned_text,
                            embedding=embedding,
                            metadata={
                                "character_count": len(cleaned_text)
                            }
                        )
                    )

                # 6. Perform a single batch SQL operation
                if chunks_to_create:
                    JobChunk.objects.bulk_create(chunks_to_create)
                    logger.info(f"Successfully chunked and bulk-inserted {len(chunks_to_create)} sections for Job ID {job.id}")
                    return True
                
        except Exception as e:
            logger.error(f"Critical error executing Job Ingestion Pipeline for ID {job.id}: {str(e)}")
            # The transaction.atomic block automatically rolls back the `.delete()` if anything failed here
            raise e

        return False