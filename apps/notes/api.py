from rest_framework import viewsets, permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Count

from .models import Note, Category, Tag
from .serializers import NoteSerializer, CategorySerializer, TagSerializer


class IsOwner(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to access it.
    """
    def has_object_permission(self, request, view, obj):
        # Check if the requesting user is the owner of the object
        return obj.user == request.user


class NoteViewSet(viewsets.ModelViewSet):
    """
    API endpoint for notes.
    """
    serializer_class = NoteSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwner]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'content']
    ordering_fields = ['title', 'created_at', 'updated_at']
    ordering = ['-updated_at']
    
    def get_queryset(self):
        user = self.request.user
        queryset = Note.objects.filter(user=user)
        
        # Filter by category if provided
        category_id = self.request.query_params.get('category', None)
        if category_id:
            queryset = queryset.filter(category_id=category_id)
        
        # Filter by tag if provided
        tag_id = self.request.query_params.get('tag', None)
        if tag_id:
            queryset = queryset.filter(tags__id=tag_id)
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """
        Return statistics about user's notes.
        """
        user = request.user
        total_notes = Note.objects.filter(user=user).count()
        notes_by_category = Category.objects.filter(user=user).annotate(
            notes_count=Count('notes')
        ).values('id', 'name', 'notes_count')
        
        return Response({
            'total_notes': total_notes,
            'notes_by_category': notes_by_category
        })


class CategoryViewSet(viewsets.ModelViewSet):
    """
    API endpoint for categories.
    """
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticated, IsOwner]
    
    def get_queryset(self):
        return Category.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class TagViewSet(viewsets.ModelViewSet):
    """
    API endpoint for tags.
    """
    serializer_class = TagSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwner]
    
    def get_queryset(self):
        return Tag.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user) 