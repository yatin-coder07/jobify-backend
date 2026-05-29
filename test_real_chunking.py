import os
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from ai.models import Resume
from ai.chunking.resume_chunker import ResumeChunker

resume = Resume.objects.first()

if resume:
    print(f"Testing chunking for resume ID: {resume.id}")
    print(f"Extracted text preview (first 1000 chars):\n{resume.extracted_text[:1000]}")
    print("\n" + "="*50 + "\n")
    
    chunks = ResumeChunker.chunk_resume(resume.extracted_text)
    print(f"Number of chunks found: {len(chunks)}")
    
    for i, chunk in enumerate(chunks):
        print(f"Chunk {i+1}:")
        print(f"Section: {chunk['section']}")
        print(f"Text Preview: {chunk['text'][:200]}...")
        print("-" * 30)
else:
    print("No resumes found in the database.")
