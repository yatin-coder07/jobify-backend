from supabase import create_client
import os
import uuid

supabase = create_client(
    os.environ.get("SUPABASE_URL"),
    os.environ.get("SUPABASE_SERVICE_KEY"),
)

def upload_resume(file, filename):
    try:
        unique_name = f"{uuid.uuid4()}-{filename}"

        file_bytes = file.read()  # ✅ convert to bytes

        response = supabase.storage.from_("resumes").upload(
            unique_name,
            file_bytes,
            {
                "content-type": file.content_type
            },
        )

        if response.get("error"):
            raise Exception(response["error"])

        return (
            f"{os.environ.get('SUPABASE_URL')}"
            f"storage/v1/object/public/resumes/{unique_name}"
        )

    except Exception as e:
        print("SUPABASE UPLOAD ERROR:", str(e))
        raise
