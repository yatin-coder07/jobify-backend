from supabase import create_client
import os

supabase = create_client(
    os.environ.get("SUPABASE_URL"),
    os.environ.get("SUPABASE_SERVICE_KEY"),
)

def upload_resume(file, filename):
    res = supabase.storage.from_("resumes").upload(
        filename,
        file,
        {"content-type": file.content_type},
    )

    if res.get("error"):
        raise Exception("Upload failed")

    return f"{os.environ.get('SUPABASE_URL')}/storage/v1/object/public/resumes/{filename}"
