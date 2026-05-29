import json
from django.core.cache import cache


class ResumeCache:

    TTL = 60 * 60 * 24

    @classmethod
    def get_resume_text(
        cls,
        resume_id
    ):

        return cache.get(
            f"resume:text:{resume_id}"
        )

    @classmethod
    def set_resume_text(
        cls,
        resume_id,
        text
    ):

        cache.set(
            f"resume:text:{resume_id}",
            text,
            timeout=cls.TTL
        )

    @classmethod
    def get_resume_profile(
        cls,
        user_id
    ):

        return cache.get(
            f"resume:profile:{user_id}"
        )

    @classmethod
    def set_resume_profile(
        cls,
        user_id,
        profile
    ):

        cache.set(
            f"resume:profile:{user_id}",
            profile,
            timeout=cls.TTL
        )