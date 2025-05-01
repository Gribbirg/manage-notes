from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .api import NoteViewSet, CategoryViewSet, TagViewSet

# Create a router for the API endpoints
router = DefaultRouter()
router.register(r'notes', NoteViewSet, basename='api-note')
router.register(r'categories', CategoryViewSet, basename='api-category')
router.register(r'tags', TagViewSet, basename='api-tag')

# API URL patterns
urlpatterns = [
    path('', include(router.urls)),
] 