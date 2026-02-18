from rest_framework import serializers
from django.contrib.auth.models import User
from django.core.files.uploadedfile import UploadedFile

from .models import (
    CandidateProfile,
    EmployerProfile,
    Profile,
    Education,
    Experience,
    Skill,
)

from utils.supabase import upload_file


class RegisterSerializer(serializers.ModelSerializer):
    role = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ["username", "email", "password", "role"]
        extra_kwargs = {
            "password": {"write_only": True}
        }

    def create(self, validated_data):
        role = validated_data.pop("role")

        user = User.objects.create_user(**validated_data)
        user.profile.role = role
        user.profile.save()

        return user
class SkillSerializer(serializers.ModelSerializer):
    class Meta:
        model = Skill
        fields = ["id", "name"]
class EducationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Education
        fields = "__all__"
       


class ExperienceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Experience
        fields = "__all__"

class CandidateProfileSerializer(serializers.ModelSerializer):
    skills = SkillSerializer(many=True, read_only=True)
    experiences = ExperienceSerializer(many=True, read_only=True)
    educations = EducationSerializer(many=True, read_only=True)

 
    profile_image = serializers.FileField(write_only=True, required=False)
    resume = serializers.FileField(write_only=True, required=False)

    
    profile_image_url = serializers.CharField(
        source="profile_image", read_only=True
    )
    
    resume_url = serializers.CharField(
        source="resume", read_only=True
    )

    class Meta:
     model = CandidateProfile
     exclude = ["user"]


    def validate(self, attrs):
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

        skills_data = request.data.getlist("skills")
        profile_image = validated_data.pop("profile_image", None)
        resume = validated_data.pop("resume", None)

        candidate_profile = CandidateProfile.objects.create(
            user=user,
            **validated_data
        )

        for skill_name in skills_data:
            skill, _ = Skill.objects.get_or_create(name=skill_name.strip())
            candidate_profile.skills.add(skill)

        if isinstance(profile_image, UploadedFile):
            candidate_profile.profile_image = upload_file(
                profile_image, "profile_image"
            )

        if isinstance(resume, UploadedFile):
            candidate_profile.resume = upload_file(
                resume, "resumes"
            )

        candidate_profile.save()
        return candidate_profile

    def update(self, instance, validated_data):
        request = self.context["request"]

        skills_data = request.data.getlist("skills")
        profile_image = validated_data.pop("profile_image", None)
        resume = validated_data.pop("resume", None)

        if skills_data:
            instance.skills.clear()
            for skill_name in skills_data:
                skill, _ = Skill.objects.get_or_create(name=skill_name.strip())
                instance.skills.add(skill)

        if isinstance(profile_image, UploadedFile):
            instance.profile_image = upload_file(
                profile_image, "profile_image"
            )

        if isinstance(resume, UploadedFile):
            instance.resume = upload_file(
                resume, "resumes"
            )

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        return instance



        

class UserMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "first_name", "last_name"]
class EmployerProfileSerializer(serializers.ModelSerializer):
    logo = serializers.ImageField(write_only=True, required=False)
    user = UserMiniSerializer(read_only=True)
    class Meta:
        model = EmployerProfile
        fields ="__all__"
        

    def validate(self, attrs):
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
        user = self.context["request"].user
        logo_file = validated_data.pop("logo", None)

        employer_profile = EmployerProfile.objects.create(
            user=user,
            **validated_data
        )

        if isinstance(logo_file, UploadedFile):
            employer_profile.logo = upload_file(
                logo_file,
                "logo"
            )
            employer_profile.save()

        return employer_profile

    def update(self, instance, validated_data):
        logo_file = validated_data.pop("logo", None)

        if isinstance(logo_file, UploadedFile):
            instance.logo = upload_file(
                logo_file,
                "logo"
            )

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        return instance
