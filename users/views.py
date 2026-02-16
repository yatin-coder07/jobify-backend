from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.contrib.auth.models import User
from .serializers import RegisterSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from rest_framework.permissions import IsAuthenticated
from .models import CandidateProfile,EmployerProfile,Experience,Education
from .serializers import CandidateProfileSerializer,EmployerProfileSerializer,ExperienceSerializer,EducationSerializer


# views triggered during user registration and other user-related actions and they trigger the serializers to process data


class RegisterView(APIView):
    def post(self , request): #request is the HTTP request data sent from the frontend
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        print(serializer.errors)    
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate

class LoginView(APIView):
    def post(self, request):
        username = request.data.get("username")
        password = request.data.get("password")

        user = authenticate(username=username, password=password)

        if user is None:
            return Response(
                {"error": "Invalid credentials"},
                status=status.HTTP_401_UNAUTHORIZED
            )

        refresh = RefreshToken.for_user(user)

        return Response({
            "access": str(refresh.access_token),
            "role": user.profile.role
        })


class UserRoleView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(
            {"username": request.user.username,
                "role": request.user.profile.role},
            status=status.HTTP_200_OK
        )

class CandidateProfileView(APIView):
     permission_classes = [IsAuthenticated]

     def get(self, request, id=None):
        if id:
            candidate = CandidateProfile.objects.get(id=id)
        else:
            candidate = CandidateProfile.objects.get(user=request.user)

        serializer = CandidateProfileSerializer(candidate)
        return Response(serializer.data)
     def post(self, request):
         """Create profile"""
         serializer = CandidateProfileSerializer(data = request.data, context={'request':request})

         if serializer.is_valid():
             serializer.save()
             return Response(
                 serializer.data,
                status=status.HTTP_201_CREATED
             )
         return Response(
           serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )
     def put(self, request):
        """
        Update candidate profile
        """
        try:
            profile = CandidateProfile.objects.get(user=request.user)
        except CandidateProfile.DoesNotExist:
            return Response(
                {"detail": "Candidate profile not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = CandidateProfileSerializer(
            profile,
            data=request.data,
            partial=True,
            context={"request": request}
        )

        if serializer.is_valid():
            serializer.save()
            return Response(
                serializer.data,
                status=status.HTTP_200_OK
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )
     
class ExperienceView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        profile = CandidateProfile.objects.get(user=request.user)
        serializer = ExperienceSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(candidate=profile)
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)

    def delete(self, request, pk):
        experience = Experience.objects.get(
            pk=pk, candidate__user=request.user
        )
        experience.delete()
        return Response(status=204)
    def get(self, request):
        try:
            profile = CandidateProfile.objects.get(user=request.user)
        except CandidateProfile.DoesNotExist:
            return Response(
                {"detail": "Candidate profile not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        experiences = Experience.objects.filter(candidate=profile)
        serializer = ExperienceSerializer(experiences, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    
    
class EducationView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        profile = CandidateProfile.objects.get(user=request.user)
        serializer = EducationSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(candidate=profile)
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)
    def get(self, request):
        profile = CandidateProfile.objects.get(user=request.user)
        education = Education.objects.filter(candidate=profile)
        serializer = EducationSerializer(education, many=True)
        return Response(serializer.data, status=200)


class EmployerProfileView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        """
        Get employer company profile
        """
        try:
            profile = EmployerProfile.objects.get(user=request.user)
        except EmployerProfile.DoesNotExist:
            return Response(
                {"detail": "Employer profile not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = EmployerProfileSerializer(profile)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        """
        Create employer company profile
        """
        serializer = EmployerProfileSerializer(
            data=request.data,
            context={"request": request}
        )

        if serializer.is_valid():
            serializer.save()
            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )

    def put(self, request):
        """
        Update employer company profile
        """
        try:
            profile = EmployerProfile.objects.get(user=request.user)
        except EmployerProfile.DoesNotExist:
            return Response(
                {"detail": "Employer profile not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = EmployerProfileSerializer(
            profile,
            data=request.data,
            partial=True,
            context={"request": request}
        )

        if serializer.is_valid():
            serializer.save()
            return Response(
                serializer.data,
                status=status.HTTP_200_OK
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )
class CandidateProfileCheckView(APIView):
    def get(self, request):
        user = request.user

        if CandidateProfile.objects.filter(user=user).exists():
            return Response(
                {"detail": "Profile already exists"},
                status=status.HTTP_404_NOT_FOUND
            )

        return Response(
            {"detail": "Profile does not exist"},
            status=status.HTTP_200_OK
        )
class EmployerProfileCheckView(APIView):
    def get(self, request):
        user = request.user

        if EmployerProfile.objects.filter(user=user).exists():
            return Response(
                {"detail": "Profile already exists"},
                status=status.HTTP_404_NOT_FOUND
            )

        return Response(
            {"detail": "Profile does not exist"},
            status=status.HTTP_200_OK
        )