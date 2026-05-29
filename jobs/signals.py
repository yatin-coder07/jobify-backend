from django.db.models.signals import post_save
from django.dispatch import receiver

from jobs.models import Job
from ai.services.job_ingestion_service import (
    JobIngestionService
)


@receiver(post_save, sender=Job)
def create_job_embeddings(
    sender,
    instance,
    created,
    **kwargs
):

    JobIngestionService.process_job(
        instance
    )