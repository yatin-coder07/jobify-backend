from django.conf import settings
from google import genai
import requests

from ai.cache.embedding_cache import EmbeddingCache


def report_debug(data):
    try:
        requests.post(
            "http://127.0.0.1:7777/event",
            json=data,
            timeout=1
        )
    except:
        pass


class GeminiEmbeddingService:

    # create ONE client (important optimization)
    client = genai.Client(api_key=settings.GEMINI_API_KEY)

    @staticmethod
    def generate_embedding(text: str):

        # 1. cache check
        cached_embedding = EmbeddingCache.get(text)
        if cached_embedding:
            return cached_embedding

        try:
            report_debug({
                "event": "gemini_api_call_start",
                "text_len": len(text)
            })

            # 2. call new embedding API
            response = GeminiEmbeddingService.client.models.embed_content(
                model="models/gemini-embedding-001",
                contents=text
            )

            # 3. extract embedding vector
            embedding = response.embeddings[0].values

            report_debug({
                "event": "gemini_api_call_success"
            })

            # 4. cache it
            EmbeddingCache.set(text, embedding)

            return embedding

        except Exception as e:

            report_debug({
                "event": "gemini_api_call_error",
                "error": str(e)
            })

            raise e