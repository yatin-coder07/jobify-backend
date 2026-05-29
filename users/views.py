import logging
from django.shortcuts import render, get_object_or_404
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.db.models import Q

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions, generics
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken

from .models import CandidateProfile, EmployerProfile, Experience, Education
from .serializers import (
    RegisterSerializer, 
    CandidateProfileSerializer, 
    EmployerProfileSerializer, 
    ExperienceSerializer, 
    EducationSerializer
)

logger = logging.getLogger("jobify.auth.views")

class RegisterView(APIView):
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        logger.warning(f"Registration validation failure: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


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

        # Defensive fallback check in case profile properties haven't been configured yet
        user_role = getattr(getattr(user, 'profile', None), 'role', 'unknown')

        return Response({
            "access": str(refresh.access_token),
            "role": user_role
        })


class UserRoleView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user_role = getattr(getattr(request.user, 'profile', None), 'role', 'unknown')
        return Response(
            {
                "username": request.user.username,
                "role": user_role
            },
            status=status.HTTP_200_OK
        )


class CandidateProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, id=None):
        try:
            if id:
                candidate = CandidateProfile.objects.get(id=id)
            else:
                candidate = CandidateProfile.objects.get(user=request.user)
            serializer = CandidateProfileSerializer(candidate)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except CandidateProfile.DoesNotExist:
            return Response(
                {"detail": "Candidate profile not found"},
                status=status.HTTP_404_NOT_FOUND
            )

    def post(self, request):
        # Explicit check to stop duplicate submissions
        if CandidateProfile.objects.filter(user=request.user).exists():
            return Response(
                {"detail": "Profile already exists for this authenticated user workspace."},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = CandidateProfileSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            # Force the authenticated user into the save operations context
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request):
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
            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ExperienceView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        profile = get_object_or_404(CandidateProfile, user=request.user)
        serializer = ExperienceSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(candidate=profile)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request):
        profile = get_object_or_404(CandidateProfile, user=request.user)
        experiences = Experience.objects.filter(candidate=profile)
        serializer = ExperienceSerializer(experiences, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def delete(self, request, pk):
        experience = get_object_or_404(Experience, pk=pk, candidate__user=request.user)
        experience.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class EducationView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        profile = get_object_or_404(CandidateProfile, user=request.user)
        serializer = EducationSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(candidate=profile)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request):
        profile = get_object_or_404(CandidateProfile, user=request.user)
        education = Education.objects.filter(candidate=profile)
        serializer = EducationSerializer(education, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class EmployerProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            profile = EmployerProfile.objects.get(user=request.user)
            serializer = EmployerProfileSerializer(profile)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except EmployerProfile.DoesNotExist:
            return Response(
                {"detail": "Employer profile not found"},
                status=status.HTTP_404_NOT_FOUND
            )

    # Ensure this is named exactly 'post' in lowercase
    def post(self, request):
        if EmployerProfile.objects.filter(user=request.user).exists():
            return Response(
                {"detail": "Employer profile already exists for this account context."},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = EmployerProfileSerializer(data=request.data, context={"request": request})

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    def put(self, request):
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
            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CandidateProfileCheckView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        exists = CandidateProfile.objects.filter(user=request.user).exists()
        return Response(
            {
                "exists": exists,
                "detail": "Profile already exists" if exists else "Profile does not exist"
            },
            status=status.HTTP_200_OK  # Return 200 OK so frontend applications process the boolean cleanly
        )


class EmployerProfileCheckView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        exists = EmployerProfile.objects.filter(user=request.user).exists()
        return Response(
            {
                "exists": exists,
                "detail": "Profile already exists" if exists else "Profile does not exist"
            },
            status=status.HTTP_200_OK  # Return 200 OK so frontend applications process the boolean cleanly
        )