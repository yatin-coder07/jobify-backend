from ai.parsers.pdf_parser import PDFParser
from ai.services.text_cleaner import TextCleaner
from ai.chunking.resume_chunker import ResumeChunker
from ai.models import ResumeChunk

from ai.embeddings.gemini_embedding_service import (
    GeminiEmbeddingService
)

from ai.cache.resume_cache import (
    ResumeCache
)

import requests


def report_debug(data):
    try:
        requests.post(
            "http://127.0.0.1:7777/event",
            json=data,
            timeout=1
        )
    except:
        pass


class ResumeIngestionService:

    @classmethod
    def process_resume(cls, resume):

        report_debug({
            "event":
            "process_resume_method_start",

            "resume_id":
            str(resume.id)
        })

        cached_text = (
            ResumeCache.get_resume_text(
                resume.id
            )
        )

        if cached_text:

            report_debug({
                "event":
                "cache_hit",

                "resume_id":
                str(resume.id)
            })

            cleaned_text = (
                cached_text
            )

        else:

            report_debug({
                "event":
                "cache_miss",

                "resume_id":
                str(resume.id)
            })

            try:

                report_debug({
                    "event":
                    "pdf_extraction_start",

                    "path":
                    resume.original_file.path
                })

                raw_text = (
                    PDFParser.extract_text(
                        resume.original_file.path
                    )
                )

                report_debug({
                    "event":
                    "pdf_extraction_success",

                    "text_len":
                    len(raw_text)
                    if raw_text else 0
                })

            except Exception as e:

                report_debug({
                    "event":
                    "pdf_extraction_error",

                    "error":
                    str(e)
                })

                raise e

            try:

                cleaned_text = (
                    TextCleaner.clean(
                        raw_text
                    )
                )

                report_debug({
                    "event":
                    "text_clean_success",

                    "text_len":
                    len(cleaned_text)
                })

            except Exception as e:

                report_debug({
                    "event":
                    "text_clean_error",

                    "error":
                    str(e)
                })

                raise e

            try:

                ResumeCache.set_resume_text(
                    resume.id,
                    cleaned_text
                )

                report_debug({
                    "event":
                    "resume_cache_saved",

                    "resume_id":
                    str(resume.id)
                })

            except Exception as e:

                report_debug({
                    "event":
                    "resume_cache_error",

                    "error":
                    str(e)
                })

        try:

            resume.extracted_text = (
                cleaned_text
            )

            resume.save(
                update_fields=[
                    "extracted_text"
                ]
            )

            report_debug({
                "event":
                "resume_text_saved"
            })

        except Exception as e:

            report_debug({
                "event":
                "resume_text_save_error",

                "error":
                str(e)
            })

            raise e

        ResumeChunk.objects.filter(
            resume=resume
        ).delete()

        report_debug({
            "event":
            "old_chunks_deleted"
        })

        try:

            chunks = (
                ResumeChunker.chunk_resume(
                    cleaned_text
                )
            )

            report_debug({
                "event":
                "chunking_complete",

                "num_chunks":
                len(chunks)
            })

        except Exception as e:

            report_debug({
                "event":
                "chunking_error",

                "error":
                str(e)
            })

            raise e

        for i, chunk in enumerate(
            chunks
        ):

            try:

                report_debug({
                    "event":
                    "embedding_start",

                    "chunk_index":
                    i,

                    "section":
                    chunk["section"],

                    "text_len":
                    len(chunk["text"])
                })

                embedding = (
                    GeminiEmbeddingService
                    .generate_embedding(
                        chunk["text"]
                    )
                )

                report_debug({
                    "event":
                    "embedding_success",

                    "chunk_index":
                    i,

                    "dimensions":
                    len(embedding)
                })

            except Exception as e:

                report_debug({
                    "event":
                    "embedding_error",

                    "chunk_index":
                    i,

                    "error":
                    str(e)
                })

                raise e

            try:

                ResumeChunk.objects.create(
                    resume=resume,

                    section=
                    chunk["section"],

                    chunk_text=
                    chunk["text"],

                    embedding=
                    embedding,

                    metadata={}
                )

                report_debug({
                    "event":
                    "chunk_saved",

                    "chunk_index":
                    i
                })

            except Exception as e:

                report_debug({
                    "event":
                    "chunk_save_error",

                    "chunk_index":
                    i,

                    "error":
                    str(e)
                })

                raise e

        report_debug({
            "event":
            "process_resume_method_complete",

            "resume_id":
            str(resume.id)
        })