class JobChunker:

    @staticmethod
    def chunk_job(job):
        chunks = []

        # 1. Section: Title
        chunks.append({
            "section": "title",
            "text": job.title
        })

        # 2. Section: Description
        chunks.append({
            "section": "description",
            "text": job.description
        })

        # 3. Section: Hard Requirements Metadata
        chunks.append({
            "section": "requirements",
            "text": f"""
            Experience Level: {job.experience_level}
            Work Mode: {job.work_mode}
            Job Type: {job.job_type}
            Salary: {job.salary}
            Location: {job.location}
            """
        })

        return chunks