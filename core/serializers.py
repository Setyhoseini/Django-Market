# core/serializers.py
from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from .models import Announcement, ContractorRequest, Comment, Ticket, TicketMessage

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "username", "email", "first_name", "last_name")


class UserRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6)
    role = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ("id", "username", "email", "password", "role")

    def create(self, validated_data):
        role = validated_data.pop("role")
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(password)
        user.save()

        # assign group as role
        group, _ = Group.objects.get_or_create(name=role)
        user.groups.add(group)

        return user


class AnnouncementSerializer(serializers.ModelSerializer):
    creator = UserSerializer(read_only=True)
    assigned_to = UserSerializer(read_only=True)

    class Meta:
        model = Announcement
        fields = "__all__"
        read_only_fields = ("creator", "assigned_to", "status", "created_at", "updated_at")


class ContractorRequestSerializer(serializers.ModelSerializer):
    contractor = UserSerializer(read_only=True)

    class Meta:
        model = ContractorRequest
        fields = "__all__"
        read_only_fields = ("contractor", "created_at")


class CommentSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)

    class Meta:
        model = Comment
        fields = "__all__"
        read_only_fields = ("author", "created_at")

    def validate_rating(self, value):
        if not (1 <= value <= 5):
            raise serializers.ValidationError("rating must be 1–5")
        return value


class TicketMessageSerializer(serializers.ModelSerializer):
    sender = UserSerializer(read_only=True)

    class Meta:
        model = TicketMessage
        fields = "__all__"
        read_only_fields = ("sender", "created_at")


class TicketSerializer(serializers.ModelSerializer):
    creator = UserSerializer(read_only=True)
    messages = TicketMessageSerializer(many=True, read_only=True)

    class Meta:
        model = Ticket
        fields = "__all__"
        read_only_fields = ("creator", "created_at", "messages")
