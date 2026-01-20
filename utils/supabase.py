import os
import uuid

def upload_resume(file, filename):
    try:
       
        from supabase import create_client

        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_SERVICE_KEY")

      
        if not supabase_url or not supabase_key:
            raise Exception("Supabase env vars missing")

        supabase = create_client(supabase_url, supabase_key)

        unique_name = f"{uuid.uuid4()}-{filename}"

        supabase.storage.from_("resumes").upload(
            unique_name,
            file.read(),
            {"content-type": file.content_type},
        )

        return f"{supabase_url}storage/v1/object/public/resumes/{unique_name}"

    except Exception as e:
        
        print("SUPABASE UPLOAD FAILED:", str(e))
        return None
