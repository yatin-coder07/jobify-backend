import os
import uuid
from supabase import create_client


def get_supabase_client():
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_KEY")

    if not supabase_url or not supabase_key:
        raise Exception("Supabase env vars missing")

    # the underlying client expects the base URL to end with a slash
    # (error: "Storage endpoint URL should have a trailing slash.").
    # normalise here so callers don't have to remember it.
    if not supabase_url.endswith("/"):
        supabase_url = supabase_url + "/"

    return create_client(supabase_url, supabase_key)


def upload_file(file, bucket_name):
    supabase = get_supabase_client()

    unique_name = f"{uuid.uuid4()}.{file.name.split('.')[-1]}"

    supabase.storage.from_(bucket_name).upload(
        unique_name,
        file.read(),
        {"content-type": file.content_type},
    )

    # we can rstrip here so the returned URL doesn't have a double slash
    base = os.getenv("SUPABASE_URL", "").rstrip("/")
    return f"{base}/storage/v1/object/public/{bucket_name}/{unique_name}"
