# core/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework.authtoken.views import obtain_auth_token
from .views import RegisterViewSet, AnnouncementViewSet, CommentViewSet, TicketViewSet

router = DefaultRouter()
router.register('register', RegisterViewSet, basename='register')
router.register('announcements', AnnouncementViewSet)
router.register('comments', CommentViewSet)
router.register('tickets', TicketViewSet)

urlpatterns = [
    path('login/', obtain_auth_token),
    path('', include(router.urls)),
]
