from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.decorators import action
from rest_framework.response import Response
from django.contrib.auth import get_user_model

from .models import Announcement, Comment, Ticket
from .serializers import (
    UserRegisterSerializer,
    AnnouncementSerializer,
    CommentSerializer,
    TicketSerializer
)
from .permissions import IsCustomer, IsContractor, IsSupport, IsOwnerOrAdmin

User = get_user_model()


class RegisterViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserRegisterSerializer
    permission_classes = [AllowAny]


class AnnouncementViewSet(viewsets.ModelViewSet):
    queryset = Announcement.objects.all()
    serializer_class = AnnouncementSerializer

    def get_permissions(self):
        if self.action == 'create':
            return [IsCustomer()]
        if self.action in ['update', 'partial_update', 'destroy']:
            return [IsOwnerOrAdmin()]
        return [AllowAny()]

    def perform_create(self, serializer):
        serializer.save(creator=self.request.user)

    @action(detail=True, methods=['post'], permission_classes=[IsContractor])
    def request_job(self, request, pk=None):
        ann = self.get_object()
        if ann.status != 'open':
            return Response({'error': 'Not available'}, status=400)
        ann.assigned_to = request.user
        ann.status = 'assigned'
        ann.save()
        return Response({'status': 'assigned'})


class CommentViewSet(viewsets.ModelViewSet):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


class TicketViewSet(viewsets.ModelViewSet):
    queryset = Ticket.objects.all()
    serializer_class = TicketSerializer

    def get_permissions(self):
        if self.action == 'create':
            return [IsAuthenticated()]
        return [IsSupport()]

    def perform_create(self, serializer):
        serializer.save(creator=self.request.user)
