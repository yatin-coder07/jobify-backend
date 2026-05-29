from django.urls import path

from .views import (
    ApplyJobView, 
    CandidateApplicationsView, 
    DeleteApplicationView, 
    EmployerApplicationsView,
    ConfirmAgentSubmissionView  # Added the approval view
)

urlpatterns = [
    # 🚀 Phase 1: Apply and generate AI Cover letter draft
    path('apply/<int:job_id>/', ApplyJobView.as_view(), ),
    
    # 🚀 Phase 2: Give explicit permission to the Agent to submit
    path("agent-confirm/<int:application_id>/", ConfirmAgentSubmissionView.as_view(), ),
    
    # Management Routes
    path("employer/", EmployerApplicationsView.as_view(), ),
    path("employer/<int:application_id>/", EmployerApplicationsView.as_view(), ),
    path("candidate/", CandidateApplicationsView.as_view(), ),
    path("delete/<int:application_id>/", DeleteApplicationView.as_view(), ),
]