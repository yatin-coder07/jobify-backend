from supabase import create_client
import os
import uuid

def upload_resume(file, filename):
    supabase = create_client(
        os.environ["SUPABASE_URL"],
        os.environ["SUPABASE_SERVICE_KEY"],
    )

    unique_name = f"{uuid.uuid4()}-{filename}"

    supabase.storage.from_("resumes").upload(
        unique_name,
        file.read(),
        {"content-type": file.content_type},
    )

    return (
        f"{os.environ['SUPABASE_URL']}"
        f"storage/v1/object/public/resumes/{unique_name}"
    )
