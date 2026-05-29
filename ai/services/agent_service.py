import google.generativeai as genai
from django.conf import settings
from applications.models import JobApplication

# 🧰 TOOL 1: Caches the draft to the database application row
def save_drafted_cover_letter_to_application(application_id: int, draft_text: str) -> str:
    """
    Saves the generated cover letter draft into the application row state.
    Args:
        application_id: The database ID integer of the application.
        draft_text: The complete generated text content of the cover letter.
    """
    try:
        app = JobApplication.objects.get(id=int(application_id))
        app.cover_letter = draft_text
        app.status = "pending_approval"
        app.save()
        return "Success: Cover letter draft saved. System state paused for user confirmation."
    except Exception as e:
        return f"Error saving draft: {str(e)}"


# 🧰 TOOL 2: The actual automation execution function
def trigger_external_submission_automation(application_id: int) -> str:
    """
    Executes background automation scripts to submit the application data externally.
    Args:
        application_id: The database ID integer of the application.
    """
    try:
        app = JobApplication.objects.get(id=int(application_id))
        
        print(f"🤖 Tool executing background application submission for {app.job.title}...")
        # Your automation engine hooks (Playwright/Selenium/Requests) launch here.
        
        app.status = "applied"
        app.save()
        return "Success: The application has been fully processed and submitted."
    except Exception as e:
        return f"Error executing automation: {str(e)}"


class AIApplicationAgent:

    @classmethod
    def run_workflow(cls, application_id: int, user_has_approved: bool = False, final_letter_text: str = None):
        """
        Orchestrates the tool-calling loop using the verified Gemini model workspace.
        """
        app = JobApplication.objects.get(id=int(application_id))
        
        # Pull text from chunks using your verified model attribute: chunk_text
        if app.resume and app.resume.chunks.exists():
            resume_context = " ".join([str(chunk.chunk_text) for chunk in app.resume.chunks.all()])
        else:
            resume_context = "No detailed text resume chunks found. Use background profile metrics."

        # Configure Gemini settings
        genai.configure(api_key=settings.GEMINI_API_KEY)
        available_tools = [save_drafted_cover_letter_to_application, trigger_external_submission_automation]
        
        # 🚀 TARGETING YOUR VERIFIED WORKING GENERATION ENGINE
        model = genai.GenerativeModel(
            model_name='gemini-2.5-flash',
            tools=available_tools
        )

        system_instruction = f"""
        You are an autonomous job application agent runner. You have access to tools that alter an application status.
        
        CRITICAL OPERATING RULES:
        1. If user_approved is False: Write a professional, personalized cover letter for the candidate matching their skills to the job description. IMMEDIATELY call the `save_drafted_cover_letter_to_application` tool with the draft_text and application_id. Do NOT call any other tool.
        2. If user_approved is True: Do NOT write a cover letter. IMMEDIATELY call the `trigger_external_submission_automation` tool using the application_id.
        
        CURRENT EXECUTION STATE:
        - user_approved: {user_has_approved}
        """

        input_payload = f"""
        Job Title: {app.job.title}
        Job Description: {app.job.description}
        Candidate Resume Context: {resume_context}
        User Final Approved Letter Text: {final_letter_text if final_letter_text else "None provided yet"}
        Application Database ID: {app.id}
        """

        # Start automatic function calling chat session
        chat = model.start_chat(enable_automatic_function_calling=True)
        response = chat.send_message(f"{system_instruction}\n\n{input_payload}")
        
        return response.text