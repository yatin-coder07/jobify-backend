from django.urls import path

from .views import ApplyJobView, CandidateApplicationsView, DeleteApplicationView, EmployerApplicationsView

urlpatterns = [
    path('apply/<int:job_id>/', ApplyJobView.as_view(), ),
    path("employer/", EmployerApplicationsView.as_view(), ),
    path("candidate/", CandidateApplicationsView.as_view(), ),
    path("delete/<int:application_id>/", DeleteApplicationView.as_view(), ),
]