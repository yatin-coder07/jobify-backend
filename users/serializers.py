#serializer is saving to the database what the user sent from the frontend
from rest_framework import serializers
from django.contrib.auth.models import User

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