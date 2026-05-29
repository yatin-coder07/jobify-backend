import hashlib
from django.core.cache import cache


class EmbeddingCache:

    TTL = 86400 * 7

    @staticmethod
    def make_key(text):

        digest = hashlib.md5(
            text.encode()
        ).hexdigest()

        return f"embedding:{digest}"

    @classmethod
    def get(cls, text):

        return cache.get(
            cls.make_key(text)
        )

    @classmethod
    def set(
        cls,
        text,
        embedding
    ):

        cache.set(
            cls.make_key(text),
            embedding,
            timeout=cls.TTL
        )