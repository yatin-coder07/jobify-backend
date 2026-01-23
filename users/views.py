from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.contrib.auth.models import User
from .serializers import RegisterSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from rest_framework.permissions import IsAuthenticated
from .models import CandidateProfile,EmployerProfile
from .serializers import CandidateProfileSerializer,EmployerProfileSerializer


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

     def get(self, request):
        """
        Get candidate profile (dashboard)
        """
        try:
            profile = CandidateProfile.objects.get(user=request.user)
        except CandidateProfile.DoesNotExist:
            return Response(
                {"detail": "Candidate profile not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        serializer = CandidateProfileSerializer(profile)
        return Response(serializer.data , status=status.HTTP_200_OK)
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
