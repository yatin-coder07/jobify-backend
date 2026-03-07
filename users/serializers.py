from rest_framework import serializers
from django.contrib.auth.models import User
from django.core.files.uploadedfile import UploadedFile
import logging

from .models import (
    CandidateProfile,
    EmployerProfile,
    Profile,
    Education,
    Experience,
    Skill,
)

from utils.supabase import upload_file

logger = logging.getLogger(__name__)


class RegisterSerializer(serializers.ModelSerializer):
    role = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ["username", "email", "password", "role"]
        extra_kwargs = {
            "password": {"write_only": True}
        }

    def create(self, validated_data):
        logger.debug("RegisterSerializer.create called")

        try:
            role = validated_data.pop("role")

            user = User.objects.create_user(**validated_data)
            user.profile.role = role
            user.profile.save()

            logger.debug(f"User {user.username} created with role {role}")
            return user

        except Exception as e:
            logger.exception("Error creating user")
            raise


class SkillSerializer(serializers.ModelSerializer):
    class Meta:
        model = Skill
        fields = ["id", "name"]


class EducationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Education
        fields = "__all__"
        read_only_fields = ["candidate"]

    def create(self, validated_data):
        logger.debug("EducationSerializer.create called")

        try:
            user = self.context["request"].user
            logger.debug(f"Education creation for user: {user}")

            candidate = CandidateProfile.objects.filter(user=user).first()

            if not candidate:
                logger.error("Candidate profile not found for user")
                raise serializers.ValidationError("Candidate profile not found")

            education = Education.objects.create(
                candidate=candidate,
                **validated_data
            )

            logger.debug(f"Education created: {education}")
            return education

        except Exception as e:
            logger.exception("Error creating education")
            raise


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

    user = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = CandidateProfile
        fields = "__all__"

    def validate(self, attrs):
        logger.debug("CandidateProfileSerializer.validate called")

        user = self.context["request"].user

        try:
            profile = Profile.objects.get(user=user)
        except Profile.DoesNotExist:
            logger.error("User profile not found")
            raise serializers.ValidationError("User profile not found")

        if profile.role != "candidate":
            logger.error("User is not a candidate")
            raise serializers.ValidationError(
                "Only candidates can create or update candidate profiles"
            )

        logger.debug("Validation successful")
        return attrs

    def create(self, validated_data):
        logger.debug("CandidateProfileSerializer.create called")

        request = self.context["request"]
        user = request.user

        try:
            skills_data = request.data.getlist("skills")
            profile_image = validated_data.pop("profile_image", None)
            resume = validated_data.pop("resume", None)

            logger.debug(f"Creating profile for user: {user}")
            logger.debug(f"Validated data: {validated_data}")

            candidate_profile = CandidateProfile.objects.create(
                user=user,
                **validated_data
            )

            logger.debug("CandidateProfile created successfully")

            for skill_name in skills_data:
                skill, _ = Skill.objects.get_or_create(name=skill_name.strip())
                candidate_profile.skills.add(skill)

            logger.debug(f"Skills added: {skills_data}")

            if isinstance(profile_image, UploadedFile):
                try:
                    logger.debug("Uploading profile image")
                    candidate_profile.profile_image = upload_file(
                        profile_image, "profile_image"
                    )
                except Exception as exc:
                    logger.exception("Profile image upload failed")
                    raise serializers.ValidationError(
                        {"profile_image": str(exc)}
                    )

            if isinstance(resume, UploadedFile):
                try:
                    logger.debug("Uploading resume")
                    candidate_profile.resume = upload_file(
                        resume, "resumes"
                    )
                except Exception as exc:
                    logger.exception("Resume upload failed")
                    raise serializers.ValidationError(
                        {"resume": str(exc)}
                    )

            candidate_profile.save()
            logger.debug("Candidate profile saved successfully")

            return candidate_profile

        except Exception as e:
            logger.exception("Error creating candidate profile")
            raise

    def update(self, instance, validated_data):
        logger.debug("CandidateProfileSerializer.update called")

        request = self.context["request"]

        try:
            skills_data = request.data.getlist("skills")
            profile_image = validated_data.pop("profile_image", None)
            resume = validated_data.pop("resume", None)

            if skills_data:
                instance.skills.clear()

                for skill_name in skills_data:
                    skill, _ = Skill.objects.get_or_create(name=skill_name.strip())
                    instance.skills.add(skill)

                logger.debug(f"Updated skills: {skills_data}")

            if isinstance(profile_image, UploadedFile):
                try:
                    logger.debug("Uploading new profile image")
                    instance.profile_image = upload_file(
                        profile_image, "profile_image"
                    )
                except Exception as exc:
                    logger.exception("Profile image upload failed")
                    raise serializers.ValidationError(
                        {"profile_image": str(exc)}
                    )

            if isinstance(resume, UploadedFile):
                try:
                    logger.debug("Uploading new resume")
                    instance.resume = upload_file(
                        resume, "resumes"
                    )
                except Exception as exc:
                    logger.exception("Resume upload failed")
                    raise serializers.ValidationError(
                        {"resume": str(exc)}
                    )

            for attr, value in validated_data.items():
                setattr(instance, attr, value)

            instance.save()
            logger.debug("Candidate profile updated successfully")

            return instance

        except Exception:
            logger.exception("Error updating candidate profile")
            raise


class UserMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "first_name", "last_name"]


class EmployerProfileSerializer(serializers.ModelSerializer):
    logo = serializers.ImageField(write_only=True, required=False)
    user = UserMiniSerializer(read_only=True)

    class Meta:
        model = EmployerProfile
        fields = "__all__"

    def validate(self, attrs):
        logger.debug("EmployerProfileSerializer.validate called")

        user = self.context["request"].user

        try:
            profile = Profile.objects.get(user=user)
        except Profile.DoesNotExist:
            logger.error("User profile not found")
            raise serializers.ValidationError("User profile not found")

        if profile.role != "employer":
            logger.error("User is not an employer")
            raise serializers.ValidationError(
                "Only employers can create or update company profiles"
            )

        return attrs

    def create(self, validated_data):
        logger.debug("EmployerProfileSerializer.create called")

        try:
            user = self.context["request"].user
            logo_file = validated_data.pop("logo", None)

            employer_profile = EmployerProfile.objects.create(
                user=user,
                **validated_data
            )

            if isinstance(logo_file, UploadedFile):
                try:
                    logger.debug("Uploading company logo")
                    employer_profile.logo = upload_file(
                        logo_file,
                        "logo"
                    )
                    employer_profile.save()

                except Exception as exc:
                    logger.exception("Logo upload failed")
                    raise serializers.ValidationError({"logo": str(exc)})

            logger.debug("Employer profile created successfully")
            return employer_profile

        except Exception:
            logger.exception("Error creating employer profile")
            raise

    def update(self, instance, validated_data):
        logger.debug("EmployerProfileSerializer.update called")

        try:
            logo_file = validated_data.pop("logo", None)

            if isinstance(logo_file, UploadedFile):
                try:
                    logger.debug("Uploading new logo")
                    instance.logo = upload_file(
                        logo_file,
                        "logo"
                    )
                except Exception as exc:
                    logger.exception("Logo upload failed")
                    raise serializers.ValidationError({"logo": str(exc)})

            for attr, value in validated_data.items():
                setattr(instance, attr, value)

            instance.save()

            logger.debug("Employer profile updated successfully")
            return instance

        except Exception:
            logger.exception("Error updating employer profile")
            raise