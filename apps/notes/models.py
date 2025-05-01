from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
from django.core.exceptions import ValidationError
from django.utils.html import strip_tags
from django.utils.text import Truncator
import json
from .validators import (
    validate_note_title, validate_note_content,
    validate_category_name, validate_tag_name,
    validate_content_quota
)


class Category(models.Model):
    name = models.CharField(max_length=100, validators=[validate_category_name])
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='categories')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name_plural = 'Categories'
        ordering = ['name']
        unique_together = ['name', 'user']
    
    def __str__(self):
        return self.name
    
    def get_absolute_url(self):
        return reverse('notes:category_detail', kwargs={'pk': self.pk})
    
    def clean(self):
        """Validate the category."""
        super().clean()
        
        # Check if name is unique for this user
        # Skip this validation if user is not set yet (will be set by the view)
        if self.name and hasattr(self, 'user_id') and self.user_id is not None:
            existing = Category.objects.filter(name__iexact=self.name, user=self.user)
            if self.pk:  # If updating existing category
                existing = existing.exclude(pk=self.pk)
            
            if existing.exists():
                raise ValidationError({'name': 'A category with this name already exists.'})


class Tag(models.Model):
    name = models.CharField(max_length=50, validators=[validate_tag_name])
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tags')
    
    class Meta:
        ordering = ['name']
        unique_together = ['name', 'user']
    
    def __str__(self):
        return self.name
    
    def clean(self):
        """Validate the tag."""
        super().clean()
        
        # Check if name is unique for this user
        # Skip this validation if user is not set yet (will be set by the view)
        if self.name and hasattr(self, 'user_id') and self.user_id is not None:
            existing = Tag.objects.filter(name__iexact=self.name, user=self.user)
            if self.pk:  # If updating existing tag
                existing = existing.exclude(pk=self.pk)
            
            if existing.exists():
                raise ValidationError({'name': 'A tag with this name already exists.'})


class NoteSharing(models.Model):
    """Model to represent sharing permissions for a note."""
    PERMISSION_CHOICES = [
        ('read', 'Read Only'),
        ('edit', 'Edit'),
        ('admin', 'Admin'),
    ]
    
    note = models.ForeignKey('Note', on_delete=models.CASCADE, related_name='sharing_permissions')
    shared_with = models.ForeignKey(User, on_delete=models.CASCADE, related_name='shared_with_me')
    permission = models.CharField(max_length=10, choices=PERMISSION_CHOICES, default='read')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['note', 'shared_with']
        ordering = ['created_at']
    
    def __str__(self):
        return f"{self.note.title} shared with {self.shared_with.username} ({self.permission})"


class Note(models.Model):
    title = models.CharField(max_length=200, validators=[validate_note_title])
    content = models.TextField(validators=[validate_note_content])
    category = models.ForeignKey(
        Category, 
        on_delete=models.SET_NULL, 
        related_name='notes',
        null=True,
        blank=True
    )
    tags = models.ManyToManyField(Tag, related_name='notes', blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notes')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # New fields for enhanced functionality
    is_pinned = models.BooleanField(default=False, help_text="Pin this note to the top")
    shared_with = models.ManyToManyField(User, through=NoteSharing, related_name='shared_notes')
    is_archived = models.BooleanField(default=False, help_text="Archive this note")
    
    class Meta:
        ordering = ['-is_pinned', '-updated_at']
    
    def __str__(self):
        return self.title
    
    def get_absolute_url(self):
        return reverse('notes:detail', kwargs={'pk': self.pk})
    
    def get_tags_display(self):
        return ', '.join(tag.name for tag in self.tags.all())
    
    def clean(self):
        """Validate the note."""
        super().clean()
        
        # Check if category belongs to the same user
        if self.category and self.user and self.category.user != self.user:
            raise ValidationError({'category': 'You do not have permission to use this category.'})
        
        # Check maximum number of tags
        MAX_TAGS = 10  # Maximum number of tags per note
        if hasattr(self, '_tags') and len(self._tags) > MAX_TAGS:
            raise ValidationError({'tags': f'You cannot add more than {MAX_TAGS} tags to a note.'})
        
        # Check content quota
        if self.content:
            try:
                # Calculate content size difference for existing notes
                if self.pk:
                    old_note = Note.objects.get(pk=self.pk)
                    old_size = len(old_note.content.encode('utf-8'))
                    new_size = len(self.content.encode('utf-8'))
                    content_diff = new_size - old_size
                else:
                    content_diff = len(self.content.encode('utf-8'))
                
                # User's content quota is 10MB (can be adjusted)
                validate_content_quota(self.user, content_diff)
            except Exception as e:
                raise ValidationError({'content': str(e)})
    
    def sanitize_content(self):
        """Sanitize note content to remove potentially harmful HTML."""
        self.content = strip_tags(self.content)
    
    def save(self, *args, **kwargs):
        """Save the note and validate it."""
        # Sanitize content
        self.sanitize_content()
        
        # Validate the note
        self.full_clean()
        
        super().save(*args, **kwargs)
    
    def get_excerpt(self, length=100):
        """Get a truncated version of the content."""
        return Truncator(self.content).chars(length)
    
    def is_shared_with_user(self, user):
        """Check if note is shared with specified user."""
        return user in self.shared_with.all()
    
    def get_user_permission(self, user):
        """Get the permission level for specified user."""
        if self.user == user:
            return 'owner'
        
        try:
            sharing = NoteSharing.objects.get(note=self, shared_with=user)
            return sharing.permission
        except NoteSharing.DoesNotExist:
            return None
    
    def can_user_edit(self, user):
        """Check if user can edit the note."""
        if self.user == user:
            return True
        
        permission = self.get_user_permission(user)
        return permission in ['edit', 'admin']
    
    def can_user_view(self, user):
        """Check if user can view the note."""
        if self.user == user:
            return True
        
        return self.is_shared_with_user(user)


class NoteAttachment(models.Model):
    """Model for storing file attachments for notes."""
    note = models.ForeignKey(Note, on_delete=models.CASCADE, related_name='attachments')
    file = models.FileField(upload_to='note_attachments/%Y/%m/%d/')
    file_name = models.CharField(max_length=255)
    file_size = models.PositiveIntegerField(help_text="File size in bytes")
    file_type = models.CharField(max_length=100)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-uploaded_at']
    
    def __str__(self):
        return self.file_name
    
    def clean(self):
        """Validate the attachment."""
        super().clean()
        
        # Check file size limit (5MB)
        if self.file_size > 5 * 1024 * 1024:  # 5MB in bytes
            raise ValidationError({'file': 'File size cannot exceed 5MB.'})
        
        # Check user's attachment quota
        user = self.note.user
        total_attachments = NoteAttachment.objects.filter(note__user=user).count()
        if total_attachments >= 100:  # Limit to 100 attachments per user
            raise ValidationError({'file': 'You have reached the maximum number of attachments allowed.'})
        
        # Check total attachment size per user
        total_size = NoteAttachment.objects.filter(note__user=user).exclude(pk=self.pk).aggregate(
            total=models.Sum('file_size')
        )['total'] or 0
        
        MAX_ATTACHMENT_SIZE = 100 * 1024 * 1024  # 100MB per user
        if total_size + self.file_size > MAX_ATTACHMENT_SIZE:
            raise ValidationError({'file': 'You have reached your attachment quota limit.'})
    
    def save(self, *args, **kwargs):
        """Save the attachment and validate it."""
        if not self.file_size and self.file:
            self.file_size = self.file.size
        
        self.full_clean()
        super().save(*args, **kwargs)
