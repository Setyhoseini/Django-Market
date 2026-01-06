# core/views.py
from rest_framework import viewsets, status, serializers as drf_serializers
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.decorators import action
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from rest_framework.exceptions import PermissionDenied, ValidationError

from .models import Announcement, ContractorRequest, Comment, Ticket, TicketMessage
from .serializers import (
    UserRegisterSerializer,
    AnnouncementSerializer,
    ContractorRequestSerializer,
    CommentSerializer,
    TicketSerializer,
    TicketMessageSerializer,
)
from .permissions import IsCustomer, IsContractor, IsSupport, IsOwnerOrAdmin
from drf_spectacular.utils import extend_schema, OpenApiExample

User = get_user_model()


class RegisterViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserRegisterSerializer
    permission_classes = [AllowAny]


class AnnouncementViewSet(viewsets.ModelViewSet):
    queryset = Announcement.objects.all().select_related("creator", "assigned_to")
    serializer_class = AnnouncementSerializer

    def get_permissions(self):
        # create -> only customers
        if self.action == 'create':
            return [IsCustomer()]
        # update/partial_update/destroy -> owner or admin
        if self.action in ['update', 'partial_update', 'destroy']:
            return [IsOwnerOrAdmin()]
        # other actions: allow any for list/retrieve, action-level permissions enforced below
        return [AllowAny()]

    def perform_create(self, serializer):
        serializer.save(creator=self.request.user)

    # Contractor -> create a request for this announcement (does NOT assign yet)
    @extend_schema(
        description="Contractor requests the job. Request body: {\"message\": \"...\"}. Creates a ContractorRequest.",
        request=drf_serializers.DictField(child=drf_serializers.CharField(), required=False),
        responses={201: ContractorRequestSerializer},
        examples=[
            OpenApiExample(
                "Request example",
                value={"message": "I can do it tomorrow morning"},
                request_only=True,
                media_type="application/json",
            ),
            OpenApiExample(
                "Response example",
                value={
                    "id": 1,
                    "announcement": 10,
                    "contractor": {"id": 3, "username": "contr"},
                    "message": "I can do it tomorrow morning",
                    "created_at": "2026-01-06T12:00:00Z",
                    "cancelled": False
                },
                response_only=True,
                media_type="application/json",
                status_codes=["201"]
            ),
        ],
    )
    @action(detail=True, methods=['post'], permission_classes=[IsContractor])
    def request_job(self, request, pk=None):
        ann = self.get_object()
        if ann.status != Announcement.STATUS_OPEN:
            return Response({'error': 'Announcement not open for requests'}, status=400)
        # prevent duplicate requests
        if ContractorRequest.objects.filter(announcement=ann, contractor=request.user, cancelled=False).exists():
            return Response({'error': 'You already requested this job'}, status=400)
        req = ContractorRequest.objects.create(announcement=ann, contractor=request.user, message=request.data.get("message",""))
        return Response(ContractorRequestSerializer(req).data, status=201)

    # Owner assigns contractor (must be an existing request)
    @extend_schema(
        description="Owner assigns a previously-requesting contractor. Body: {\"contractor_id\": <id>}.",
        request=drf_serializers.DictField(child=drf_serializers.IntegerField()),
        responses={200: AnnouncementSerializer},
        examples=[
            OpenApiExample(
                "Request example",
                value={"contractor_id": 3},
                request_only=True,
                media_type="application/json",
            ),
            OpenApiExample(
                "Response example",
                value={
                    "id": 10,
                    "title": "Fix sink",
                    "description": "kitchen sink leaking",
                    "creator": {"id": 2, "username": "cust"},
                    "assigned_to": {"id": 3, "username": "contr"},
                    "status": "assigned",
                    "created_at": "2026-01-06T09:00:00Z",
                    "updated_at": "2026-01-06T09:05:00Z"
                },
                response_only=True,
                media_type="application/json",
                status_codes=["200"]
            ),
        ],
    )
    @action(detail=True, methods=['post'], permission_classes=[IsCustomer])
    def assign(self, request, pk=None):
        ann = self.get_object()
        if ann.creator != request.user:
            return Response({'error': 'Only the announcement owner can assign'}, status=403)
        if ann.status != Announcement.STATUS_OPEN:
            return Response({'error': 'Announcement not in open state'}, status=400)
        contractor_id = request.data.get('contractor_id')
        if not contractor_id:
            return Response({'error': 'contractor_id required'}, status=400)
        # check valid contractor and existing request
        try:
            contractor = User.objects.get(pk=contractor_id, groups__name="contractor")
        except User.DoesNotExist:
            return Response({'error': 'Invalid contractor'}, status=400)
        exists = ContractorRequest.objects.filter(announcement=ann, contractor=contractor, cancelled=False).exists()
        if not exists:
            return Response({'error': 'That contractor did not request this job'}, status=400)
        ann.assigned_to = contractor
        ann.status = Announcement.STATUS_ASSIGNED
        ann.save()
        return Response(AnnouncementSerializer(ann).data)

    # Assigned contractor marks as done (requests confirmation)
    @extend_schema(
        description="Assigned contractor marks the job done (moves to done_requested). No body.",
        request=None,
        responses={200: AnnouncementSerializer},
        examples=[
            OpenApiExample(
                "Response example",
                value={
                    "id": 10,
                    "status": "done_requested",
                    "assigned_to": {"id": 3, "username": "contr"},
                },
                response_only=True,
                media_type="application/json",
                status_codes=["200"]
            ),
        ],
    )
    @action(detail=True, methods=['post'], permission_classes=[IsContractor])
    def mark_done(self, request, pk=None):
        ann = self.get_object()
        if ann.assigned_to != request.user:
            return Response({'error': 'You are not assigned to this announcement'}, status=403)
        if ann.status != Announcement.STATUS_ASSIGNED:
            return Response({'error': 'Invalid state to mark done'}, status=400)
        ann.status = Announcement.STATUS_DONE_REQUESTED
        ann.save()
        return Response(AnnouncementSerializer(ann).data)

    # Owner confirms the work done
    @extend_schema(
        description="Owner confirms completion (moves to done_confirmed). No body.",
        request=None,
        responses={200: AnnouncementSerializer},
        examples=[
            OpenApiExample(
                "Response example",
                value={
                    "id": 10,
                    "status": "done_confirmed",
                },
                response_only=True,
                media_type="application/json",
                status_codes=["200"]
            ),
        ],
    )
    @action(detail=True, methods=['post'], permission_classes=[IsCustomer])
    def confirm_done(self, request, pk=None):
        ann = self.get_object()
        if ann.creator != request.user:
            return Response({'error': 'Only the owner can confirm completion'}, status=403)
        if ann.status != Announcement.STATUS_DONE_REQUESTED:
            return Response({'error': 'No completion requested'}, status=400)
        ann.status = Announcement.STATUS_DONE_CONFIRMED
        ann.save()
        return Response(AnnouncementSerializer(ann).data)

    # Owner/admin/support can cancel
    @extend_schema(
        description="Owner, support, or admin can cancel the announcement. No body.",
        request=None,
        responses={200: AnnouncementSerializer},
    )
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        ann = self.get_object()
        if not (request.user == ann.creator or request.user.is_superuser or request.user.groups.filter(name="support").exists()):
            return Response({'error': 'Not permitted to cancel'}, status=403)
        ann.status = Announcement.STATUS_CANCELLED
        ann.save()
        return Response(AnnouncementSerializer(ann).data)

    # Optional: list contractor requests for owner (only owner or admin/support can view)
    @extend_schema(
        description="List contractor requests for this announcement (owner or support/admin).",
        responses={200: ContractorRequestSerializer(many=True)},
    )
    @action(detail=True, methods=['get'], permission_classes=[IsCustomer])
    def requests(self, request, pk=None):
        ann = self.get_object()
        if ann.creator != request.user and not (request.user.is_superuser or request.user.groups.filter(name="support").exists()):
            return Response({'error': 'Not permitted'}, status=403)
        qs = ann.contractor_requests.filter(cancelled=False).select_related('contractor')
        return Response(ContractorRequestSerializer(qs, many=True).data)


class CommentViewSet(viewsets.ModelViewSet):
    queryset = Comment.objects.all().select_related("author", "announcement")
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated]

    @extend_schema(
        description="Create a comment/rating for an announcement. Allowed only after announcement status is done_confirmed.",
        request=CommentSerializer,
        responses={201: CommentSerializer},
        examples=[
            OpenApiExample(
                "Request example",
                value={"announcement": 10, "rating": 5, "text": "Great work!"},
                request_only=True,
                media_type="application/json",
            ),
            OpenApiExample(
                "Response example",
                value={"id": 1, "announcement": 10, "author": {"id":2,"username":"cust"}, "rating": 5, "text": "Great work!", "created_at": "2026-01-06T12:45:00Z"},
                response_only=True,
                media_type="application/json",
                status_codes=["201"]
            ),
        ],
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        ann = serializer.validated_data.get('announcement')
        # allow comment only if announcement completed and confirmed
        if ann.status != Announcement.STATUS_DONE_CONFIRMED:
            raise ValidationError("Comments are allowed only after the owner confirms the job is done.")
        serializer.save(author=self.request.user)


class TicketViewSet(viewsets.ModelViewSet):
    queryset = Ticket.objects.all().prefetch_related("messages")
    serializer_class = TicketSerializer

    def get_permissions(self):
        # Any authenticated user can create a ticket
        if self.action == 'create':
            return [IsAuthenticated()]
        return [IsAuthenticated()]

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return Ticket.objects.none()
        if user.is_superuser or user.groups.filter(name="support").exists():
            return Ticket.objects.all().order_by("-created_at")
        return Ticket.objects.filter(creator=user).order_by("-created_at")

    def perform_create(self, serializer):
        serializer.save(creator=self.request.user)

    # Add message to a ticket. Support/admin can post messages to any ticket;
    # ticket owner can also post messages on their ticket.
    @extend_schema(
        description="Post a message to a ticket. Body: {\"text\": \"...\"}.",
        request=drf_serializers.DictField(child=drf_serializers.CharField()),
        responses={201: TicketMessageSerializer},
        examples=[
            OpenApiExample(
                "Request example",
                value={"text": "I have more details: the location is upstairs."},
                request_only=True,
                media_type="application/json",
            ),
            OpenApiExample(
                "Response example",
                value={
                    "id": 5,
                    "ticket": 2,
                    "sender": {"id": 2, "username": "cust"},
                    "text": "I have more details: the location is upstairs.",
                    "created_at": "2026-01-06T12:30:00Z"
                },
                response_only=True,
                media_type="application/json",
                status_codes=["201"]
            ),
        ],
    )
    @action(detail=True, methods=['post'])
    def post_message(self, request, pk=None):
        ticket = self.get_object()
        user = request.user
        if not user.is_authenticated:
            raise PermissionDenied("Authentication required")
        # only owner or support/admin may post
        if not (user == ticket.creator or user.is_superuser or user.groups.filter(name="support").exists()):
            raise PermissionDenied("Only ticket owner or support can post messages")
        text = request.data.get('text')
        if not text:
            return Response({'error': 'text required'}, status=400)
        msg = TicketMessage.objects.create(ticket=ticket, sender=user, text=text)
        return Response(TicketMessageSerializer(msg).data, status=201)

    # Allow support/admin to close a ticket
    @extend_schema(
        description="Close a ticket (support or admin only). No body.",
        request=None,
        responses={200: TicketSerializer},
    )
    @action(detail=True, methods=['post'])
    def close(self, request, pk=None):
        ticket = self.get_object()
        user = request.user
        if not (user.is_superuser or user.groups.filter(name="support").exists()):
            return Response({'error': 'Only support/admin can close tickets'}, status=403)
        ticket.status = Ticket.STATUS_CLOSED
        ticket.save()
        return Response(TicketSerializer(ticket).data)
