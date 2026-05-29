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
            
            # Sync role metadata to profile tracking model
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
            candidate = CandidateProfile.objects.filter(user=user).first()

            if not candidate:
                logger.error("Candidate profile not found for user")
                raise serializers.ValidationError("Candidate profile not found")

            education = Education.objects.create(
                candidate=candidate,
                **validated_data
            )
            return education
        except Exception as e:
            logger.exception("Error creating education")
            raise


class ExperienceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Experience
        fields = "__all__"
        read_only_fields = ["candidate"]


class CandidateProfileSerializer(serializers.ModelSerializer):
    skills = SkillSerializer(many=True, read_only=True)
    experiences = ExperienceSerializer(many=True, read_only=True)
    educations = EducationSerializer(many=True, read_only=True)

    # Use FileField for incoming form-data flexibilities
    profile_image = serializers.FileField(write_only=True, required=False, allow_null=True)
    resume = serializers.FileField(write_only=True, required=False, allow_null=True)

    profile_image_url = serializers.CharField(source="profile_image", read_only=True)
    resume_url = serializers.CharField(source="resume", read_only=True)

    class Meta:
        model = CandidateProfile
        fields = "__all__"
        read_only_fields = ["user"]

    def to_internal_value(self, data):
        """
        Defensive cleaning: strips out empty strings sent by frontends 
        for file fields so strict DRF field validation doesn't throw a 400.
        """
        mutable_data = data.copy() if hasattr(data, 'copy') else data
        for field in ["profile_image", "resume"]:
            if field in mutable_data and (mutable_data[field] == "" or isinstance(mutable_data[field], str) or mutable_data[field] is None):
                if hasattr(mutable_data, 'pop'):
                    mutable_data.pop(field)
                else:
                    del mutable_data[field]
        return super().to_internal_value(mutable_data)

    def validate(self, attrs):
        logger.debug("CandidateProfileSerializer.validate called")
        user = self.context["request"].user

        try:
            profile = Profile.objects.get(user=user)
        except Profile.DoesNotExist:
            raise serializers.ValidationError("User account routing profile missing.")

        if str(profile.role).strip().lower() != "candidate":
            raise serializers.ValidationError("Only candidates can manage candidate profiles.")

        return attrs

    def create(self, validated_data):
        logger.debug("CandidateProfileSerializer.create called")
        request = self.context["request"]
        user = request.user

        try:
            # Handle standard list extraction across Form-Data interfaces
            skills_data = request.data.getlist("skills") or request.data.get("skills", [])
            if isinstance(skills_data, str):
                skills_data = [s.strip() for s in skills_data.split(",") if s.strip()]

            profile_image = validated_data.pop("profile_image", None)
            resume = validated_data.pop("resume", None)

            candidate_profile = CandidateProfile.objects.create(user=user, **validated_data)

            # Process Skills Assignment
            for skill_name in skills_data:
                if isinstance(skill_name, dict):
                    skill_name = skill_name.get("name", "")
                if skill_name:
                    skill, _ = Skill.objects.get_or_create(name=str(skill_name).strip())
                    candidate_profile.skills.add(skill)

            # Handle Supabase storage pipes
            if profile_image and isinstance(profile_image, UploadedFile):
                try:
                    candidate_profile.profile_image = upload_file(profile_image, "profile_image")
                except Exception as exc:
                    raise serializers.ValidationError({"profile_image": f"Storage upload failed: {str(exc)}"})

            if resume and isinstance(resume, UploadedFile):
                try:
                    candidate_profile.resume = upload_file(resume, "resumes")
                except Exception as exc:
                    raise serializers.ValidationError({"resume": f"Resume upload failed: {str(exc)}"})

            candidate_profile.save()
            return candidate_profile
        except Exception as e:
            logger.exception("Error creating candidate profile")
            raise

    def update(self, instance, validated_data):
        logger.debug("CandidateProfileSerializer.update called")
        request = self.context["request"]

        try:
            skills_data = request.data.getlist("skills") or request.data.get("skills", None)
            profile_image = validated_data.pop("profile_image", None)
            resume = validated_data.pop("resume", None)

            if skills_data is not None:
                instance.skills.clear()
                if isinstance(skills_data, str):
                    skills_data = [s.strip() for s in skills_data.split(",") if s.strip()]
                
                for skill_name in skills_data:
                    if isinstance(skill_name, dict):
                        skill_name = skill_name.get("name", "")
                    if skill_name:
                        skill, _ = Skill.objects.get_or_create(name=str(skill_name).strip())
                        instance.skills.add(skill)

            if profile_image and isinstance(profile_image, UploadedFile):
                try:
                    instance.profile_image = upload_file(profile_image, "profile_image")
                except Exception as exc:
                    raise serializers.ValidationError({"profile_image": str(exc)})

            if resume and isinstance(resume, UploadedFile):
                try:
                    instance.resume = upload_file(resume, "resumes")
                except Exception as exc:
                    raise serializers.ValidationError({"resume": str(exc)})

            for attr, value in validated_data.items():
                setattr(instance, attr, value)

            instance.save()
            return instance
        except Exception:
            logger.exception("Error updating candidate profile")
            raise


class UserMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "first_name", "last_name"]


class EmployerProfileSerializer(serializers.ModelSerializer):
    logo = serializers.FileField(write_only=True, required=False, allow_null=True)
    user = UserMiniSerializer(read_only=True)

    class Meta:
        model = EmployerProfile
        fields = "__all__"
        read_only_fields = ["user"]

    # Add this method right here to catch and print the real validation error:
    def is_valid(self, raise_exception=False):
        valid = super().is_valid(raise_exception=False)
        if not valid:
            print("\n❌ !!! DRF SERIALIZER VALIDATION ERRORS !!! ❌")
            print(self.errors)
            print("❌ !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! ❌\n")
            
            # This forces your python terminal logs to show the error as well
            logger.error(f"Validation failed: {self.errors}")
            
        if not valid and raise_exception:
            raise serializers.ValidationError(self.errors)
        return valid

    def to_internal_value(self, data):
        mutable_data = data.copy() if hasattr(data, 'copy') else data
        if "logo" in mutable_data:
            logo_val = mutable_data["logo"]
            if logo_val == "" or isinstance(logo_val, str) or logo_val is None:
                if hasattr(mutable_data, 'pop'):
                    mutable_data.pop("logo")
                else:
                    del mutable_data["logo"]
        return super().to_internal_value(mutable_data)

    def validate(self, attrs):
        user = self.context["request"].user
        try:
            profile = Profile.objects.get(user=user)
        except Profile.DoesNotExist:
            raise serializers.ValidationError("Base user tracking configuration missing.")

        if str(profile.role).strip().lower() != "employer":
            raise serializers.ValidationError("Only users with an employer role can manage company records.")
        return attrs

    def create(self, validated_data):
        try:
            user = self.context["request"].user
            logo_file = validated_data.pop("logo", None)
            employer_profile = EmployerProfile.objects.create(user=user, **validated_data)

            if logo_file and isinstance(logo_file, UploadedFile):
                try:
                    employer_profile.logo = upload_file(logo_file, "logo")
                    employer_profile.save()
                except Exception as exc:
                    raise serializers.ValidationError({"logo": f"Cloud storage upload error: {str(exc)}"})
            return employer_profile
        except Exception:
            raise