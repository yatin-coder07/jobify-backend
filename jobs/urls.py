from django.urls import path
from .views import JobCreateView, JobDeleteView, JobDetailView, JobListView, EmployerJobListView

urlpatterns = [
    path('', JobListView.as_view()),
    path("create/", JobCreateView.as_view()),
    path("my-jobs/", EmployerJobListView.as_view()),
      path("<int:pk>/", JobDetailView.as_view()),
    path("delete/<int:job_id>/", JobDeleteView.as_view()),
]