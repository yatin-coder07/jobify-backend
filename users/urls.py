from django.urls import path
from .views import CandidateProfileCheckView, EmployerProfileCheckView, RegisterView, LoginView, UserRoleView,CandidateProfileView,EmployerProfileView , ExperienceView,EducationView
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path('register/', RegisterView.as_view()),
    path('login/', LoginView.as_view()),
    path('role/', UserRoleView.as_view()),

    # Candidate
    path("candidate/profile/", CandidateProfileView.as_view()),            # self profile
    path("candidate/profile/<int:id>/", CandidateProfileView.as_view()),   # by ID

    path("candidate/experience/", ExperienceView.as_view()),
    path("candidate/experience/<int:id>/", ExperienceView.as_view()),

    path("candidate/education/", EducationView.as_view()),
    path("candidate/education/<int:id>/", EducationView.as_view()),

    # Employer
    path("employer/profile/", EmployerProfileView.as_view()),              # self profile
    path("employer/profile/<int:id>/", EmployerProfileView.as_view()),     # by ID

    path("employer/profile/check/",EmployerProfileCheckView.as_view()),
    path("candidate/profile/check/",CandidateProfileCheckView.as_view()),
]