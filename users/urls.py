from django.urls import path
from .views import RegisterView, LoginView, UserRoleView,CandidateProfileView,EmployerProfileView , ExperienceView,EducationView
from django.conf import settings
from django.conf.urls.static import static




urlpatterns = [
    path('register/', RegisterView.as_view()),
    path('login/', LoginView.as_view()),
    path('role/',UserRoleView.as_view()),
     path("candidate/profile/", CandidateProfileView.as_view()),
     # Experience
    path("candidate/experience/", ExperienceView.as_view()),
    path("candidate/experience/<int:pk>/", ExperienceView.as_view()),
     # Education
    path("candidate/education/", EducationView.as_view()),
    path("candidate/education/<int:pk>/", EducationView.as_view()),
    
    path("employer/profile/", EmployerProfileView.as_view()),
]

