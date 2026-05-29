from ai.models import ResumeChunk
from ai.embeddings.gemini_embedding_service import (
    GeminiEmbeddingService
)


class VectorSearchService:

    @classmethod
    def search_resume(
        cls,
        resume,
        query,
        limit=5
    ):

        query_embedding = (
            GeminiEmbeddingService.generate_embedding(
                query
            )
        )

        chunks = (
            ResumeChunk.objects
            .filter(resume=resume)
            .order_by(
                "embedding__cosine_distance"
            )[:limit]
        )

        return chunks