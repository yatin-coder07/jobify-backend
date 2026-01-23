#serializer is saving to the database what the user sent from the frontend
from rest_framework import serializers
from django.contrib.auth.models import User
from .models import CandidateProfile
from utils.supabase import upload_file
from .models import EmployerProfile, Profile

class RegisterSerializer(serializers.ModelSerializer):
    role = serializers.CharField(write_only=True) #because role is not a field in User model
    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'role']
        extra_kwargs = {
            'password': {'write_only': True}
        }
    def create(self, validated_data):
        role = validated_data.pop('role')

        user = User.objects.create_user(**validated_data)
        user.profile.role = role
        user.profile.save()

        return user

class CandidateProfileSerializer(serializers.ModelSerializer):
    profile_image = serializers.ImageField(write_only=True, required=False)
    resume = serializers.FileField(write_only=True, required=False)

    class Meta:
        model = CandidateProfile
        fields = [
            "id",
            "full_name",
            "bio",
            "skills",
            "profile_image",
            "resume",
        ]

    def validate(self, attrs):
        """
        Ensure only candidates can create/update candidate profiles
        """
        user = self.context["request"].user

        try:
            profile = Profile.objects.get(user=user)
        except Profile.DoesNotExist:
            raise serializers.ValidationError("User profile not found")

        if profile.role != "candidate":
            raise serializers.ValidationError(
                "Only candidates can create or update candidate profiles"
            )

        return attrs

    def create(self, validated_data):
        request = self.context["request"]
        user = request.user

        profile_image = validated_data.pop("profile_image", None)
        resume = validated_data.pop("resume", None)

        if CandidateProfile.objects.filter(user=user).exists():
            raise serializers.ValidationError(
                "Candidate profile already exists"
            )

        candidate_profile = CandidateProfile.objects.create(
            user=user,
            **validated_data
        )

        if profile_image:
            candidate_profile.profile_image = upload_file(
                profile_image,
                "profile-images"
            )

        if resume:
            candidate_profile.resume = upload_file(
                resume,
                "resumes"
            )

        candidate_profile.save()
        return candidate_profile

    def update(self, instance, validated_data):
        profile_image = validated_data.pop("profile_image", None)
        resume = validated_data.pop("resume", None)

        if profile_image:
            instance.profile_image = upload_file(
                profile_image,
                "profile-images"
            )

        if resume:
            instance.resume = upload_file(
                resume,
                "resumes"
            )

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        return instance


class EmployerProfileSerializer(serializers.ModelSerializer):
    logo = serializers.ImageField(write_only=True, required=False)

    class Meta:
        model = EmployerProfile
        fields = [
            "id",
            "company_name",
            "description",
            "website",
            "industry",
            "location",
            "logo",
        ]

    def validate(self, attrs):
        """
        Ensure only employers can create/update employer profiles
        """
        user = self.context["request"].user

        try:
            profile = Profile.objects.get(user=user)
        except Profile.DoesNotExist:
            raise serializers.ValidationError("User profile not found")

        if profile.role != "employer":
            raise serializers.ValidationError(
                "Only employers can create or update company profiles"
            )

        return attrs

    def create(self, validated_data):
        request = self.context["request"]
        user = request.user

        logo_file = validated_data.pop("logo", None)

        employer_profile = EmployerProfile.objects.create(
            user=user,
            **validated_data
        )

        if logo_file:
            employer_profile.logo = upload_file(
                logo_file,
                bucket_name="logo"
            )
            employer_profile.save()

        return employer_profile

    def update(self, instance, validated_data):
        logo_file = validated_data.pop("logo", None)

        if logo_file:
            instance.logo = upload_file(
                logo_file,
                bucket_name="logo"
            )

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        return instance
