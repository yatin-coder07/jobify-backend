from django.urls import path
from .views import (
    ResumeUploadView
)

urlpatterns = [
    path(
        "resume/upload/",
        ResumeUploadView.as_view()
    ),
]