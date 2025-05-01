from django import forms
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from .models import Note, Category, Tag, NoteSharing, NoteAttachment
from .validators import (
    validate_note_title, validate_note_content,
    validate_category_name, validate_tag_name,
    validate_user_quota, validate_file_upload,
    validate_image_file_extension, validate_document_file_extension
)
from django.db.models import Q


class CategoryForm(forms.ModelForm):
    """Form for creating and editing categories."""
    name = forms.CharField(
        widget=forms.TextInput(
            attrs={'class': 'form-control', 'placeholder': 'Category Name'}
        ),
        validators=[validate_category_name]
    )
    
    class Meta:
        model = Category
        fields = ['name']
    
    def __init__(self, *args, **kwargs):
        """Initialize the form."""
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
    
    def clean_name(self):
        """Validate that the category name is unique for this user."""
        name = self.cleaned_data.get('name')
        
        if name and self.user:
            # Check if category with this name already exists for this user
            existing = Category.objects.filter(name__iexact=name, user=self.user)
            
            # If we're editing an existing category, exclude it from the check
            if self.instance and self.instance.pk:
                existing = existing.exclude(pk=self.instance.pk)
            
            if existing.exists():
                raise ValidationError('A category with this name already exists.')
        
        return name
    
    def clean(self):
        """Validate the form."""
        cleaned_data = super().clean()
        
        # Check if user has reached the maximum number of categories
        if not self.instance.pk and self.user:  # Only for new categories
            try:
                MAX_CATEGORIES = 50  # Maximum number of categories per user
                validate_user_quota(self.user, Category, MAX_CATEGORIES)
            except ValidationError as e:
                raise ValidationError(e.message)
        
        return cleaned_data
    
    def save(self, commit=True):
        """Save the category and ensure user is assigned."""
        category = super().save(commit=False)
        
        # Assign the user if available
        if self.user and not category.user_id:
            category.user = self.user
            
        if commit:
            category.save()
            
        return category


class TagForm(forms.ModelForm):
    """Form for creating tags."""
    name = forms.CharField(
        widget=forms.TextInput(
            attrs={'class': 'form-control', 'placeholder': 'Tag Name'}
        ),
        validators=[validate_tag_name]
    )
    
    class Meta:
        model = Tag
        fields = ['name']
    
    def __init__(self, *args, **kwargs):
        """Initialize the form."""
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
    
    def clean_name(self):
        """Validate that the tag name is unique for this user."""
        name = self.cleaned_data.get('name')
        
        if name and self.user:
            # Check if tag with this name already exists for this user
            existing = Tag.objects.filter(name__iexact=name, user=self.user)
            
            # If we're editing an existing tag, exclude it from the check
            if self.instance and self.instance.pk:
                existing = existing.exclude(pk=self.instance.pk)
            
            if existing.exists():
                raise ValidationError('A tag with this name already exists.')
        
        return name
    
    def clean(self):
        """Validate the form."""
        cleaned_data = super().clean()
        
        # Check if user has reached the maximum number of tags
        if not self.instance.pk and self.user:  # Only for new tags
            try:
                MAX_TAGS = 100  # Maximum number of tags per user
                validate_user_quota(self.user, Tag, MAX_TAGS)
            except ValidationError as e:
                raise ValidationError(e.message)
        
        return cleaned_data
    
    def save(self, commit=True):
        """Save the tag and ensure user is assigned."""
        tag = super().save(commit=False)
        
        # Assign the user if available
        if self.user and not tag.user_id:
            tag.user = self.user
            
        if commit:
            tag.save()
            
        return tag


class NoteForm(forms.ModelForm):
    """Form for creating and editing notes."""
    title = forms.CharField(
        widget=forms.TextInput(
            attrs={'class': 'form-control', 'placeholder': 'Заголовок заметки'}
        ),
        validators=[validate_note_title]
    )
    content = forms.CharField(
        widget=forms.Textarea(
            attrs={'class': 'form-control', 'placeholder': 'Содержание заметки', 'rows': 8}
        ),
        validators=[validate_note_content]
    )
    category = forms.ModelChoiceField(
        queryset=Category.objects.none(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    # Field for displaying existing tags
    tags = forms.ModelMultipleChoiceField(
        queryset=Tag.objects.none(),
        required=False,
        widget=forms.SelectMultiple(attrs={'class': 'form-select', 'size': 5})
    )
    
    # Field for adding new tags
    new_tags = forms.CharField(
        required=False,
        widget=forms.TextInput(
            attrs={'class': 'form-control', 'placeholder': 'Добавьте теги (через запятую)'}
        ),
        help_text='Введите новые теги, разделенные запятыми'
    )
    
    # New fields for enhanced functionality
    is_pinned = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text='Закрепить эту заметку вверху'
    )
    
    is_archived = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text='Архивировать эту заметку'
    )
    
    class Meta:
        model = Note
        fields = ['title', 'content', 'category', 'tags', 'is_pinned', 'is_archived']
    
    def __init__(self, *args, **kwargs):
        """Initialize the form with user-specific categories and tags."""
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if self.user:
            # Filter categories by user
            self.fields['category'].queryset = Category.objects.filter(user=self.user)
            # Filter tags by user
            self.fields['tags'].queryset = Tag.objects.filter(user=self.user)
    
    def clean_title(self):
        """Extra validation for title field."""
        title = self.cleaned_data.get('title')
        
        # Check for duplicate titles
        if title and self.user:
            existing = Note.objects.filter(title__iexact=title, user=self.user)
            
            # If we're editing an existing note, exclude it from the check
            if self.instance and self.instance.pk:
                existing = existing.exclude(pk=self.instance.pk)
            
            if existing.exists():
                # Duplicate titles are allowed but warn the user
                self.add_warning('title', 'You already have a note with this title.')
        
        return title
    
    def add_warning(self, field, message):
        """Add a warning message to a field without raising an error."""
        if not hasattr(self, '_warnings'):
            self._warnings = {}
        if field not in self._warnings:
            self._warnings[field] = []
        self._warnings[field].append(message)
    
    def get_warnings(self):
        """Get all warning messages."""
        return getattr(self, '_warnings', {})
    
    def clean_category(self):
        """Validate that the category belongs to the user."""
        category = self.cleaned_data.get('category')
        
        if category and self.user and category.user != self.user:
            raise ValidationError('You do not have permission to use this category.')
        
        return category
    
    def clean_new_tags(self):
        """Validate new tags."""
        new_tags_text = self.cleaned_data.get('new_tags', '').strip()
        
        if new_tags_text:
            # Split by comma and strip whitespace
            tag_names = [t.strip() for t in new_tags_text.split(',') if t.strip()]
            
            # Validate each tag name
            for tag_name in tag_names:
                try:
                    validate_tag_name(tag_name)
                except ValidationError as e:
                    raise ValidationError(f'Invalid tag "{tag_name}": {e.message}')
            
            # Check if too many new tags
            MAX_NEW_TAGS = 10
            if len(tag_names) > MAX_NEW_TAGS:
                raise ValidationError(f'You cannot add more than {MAX_NEW_TAGS} new tags at once.')
            
            # Store validated tag names for later use
            self._new_tag_names = tag_names
        else:
            self._new_tag_names = []
        
        return new_tags_text
    
    def clean_content(self):
        """Validate content and check for potential issues."""
        content = self.cleaned_data.get('content')
        
        if content:
            # Check content size
            content_size = len(content.encode('utf-8'))
            if content_size > 1048576:  # 1MB
                self.add_warning('content', 'Your note is quite large. Consider breaking it into smaller notes for better organization.')
            
            # Check for potential code snippets
            code_patterns = ['def ', 'class ', 'function', 'var ', 'let ', 'const ', '<script', '<div', '<style']
            for pattern in code_patterns:
                if pattern in content:
                    self.add_warning('content', 'Your note appears to contain code. Make sure to format it properly.')
                    break
        
        return content
    
    def clean(self):
        """Validate the form."""
        cleaned_data = super().clean()
        
        # Check if user has reached the maximum number of notes
        if not self.instance.pk and self.user:  # Only for new notes
            try:
                MAX_NOTES = 1000  # Maximum number of notes per user
                validate_user_quota(self.user, Note, MAX_NOTES)
            except ValidationError as e:
                raise ValidationError(e)
        
        # Check total number of tags (existing + new)
        tags = cleaned_data.get('tags', [])
        new_tag_count = len(getattr(self, '_new_tag_names', []))
        total_tag_count = len(tags) + new_tag_count
        
        MAX_TAGS_PER_NOTE = 10
        if total_tag_count > MAX_TAGS_PER_NOTE:
            raise ValidationError(f'A note cannot have more than {MAX_TAGS_PER_NOTE} tags.')
        
        # Check if archive and pin are both set
        is_archived = cleaned_data.get('is_archived')
        is_pinned = cleaned_data.get('is_pinned')
        
        if is_archived and is_pinned:
            self.add_warning('is_pinned', 'A note cannot be both archived and pinned. The pin setting will be ignored for archived notes.')
        
        return cleaned_data
    
    def save(self, commit=True):
        """Save the note and process any new tags."""
        note = super().save(commit=False)
        
        # Debug print
        print(f"User in form: {self.user}")
        print(f"Note user before assignment: {getattr(note, 'user', None)}")
        
        if self.user:
            note.user = self.user
            print(f"Note user after assignment: {note.user}")
        
        # Logic for handling the case when a note is both archived and pinned
        if note.is_archived and note.is_pinned:
            note.is_pinned = False
        
        if commit:
            try:
                note.save()
                print(f"Note saved successfully with ID: {note.pk}")
                
                # Process existing tags
                self.save_m2m()
                
                # Process new tags
                new_tag_names = getattr(self, '_new_tag_names', [])
                
                for tag_name in new_tag_names:
                    # Check if tag already exists for this user
                    tag, created = Tag.objects.get_or_create(
                        name=tag_name,
                        user=self.user
                    )
                    # Add tag to note
                    note.tags.add(tag)
            except Exception as e:
                print(f"Error saving note: {str(e)}")
                raise e
        
        return note


class NoteAttachmentForm(forms.ModelForm):
    """Form for uploading attachments to notes."""
    file = forms.FileField(
        widget=forms.ClearableFileInput(attrs={'class': 'form-control'}),
        help_text='Maximum file size: 5MB'
    )
    
    class Meta:
        model = NoteAttachment
        fields = ['file']
    
    def __init__(self, *args, **kwargs):
        """Initialize the form."""
        self.note = kwargs.pop('note', None)
        super().__init__(*args, **kwargs)
    
    def clean_file(self):
        """Validate the uploaded file."""
        file = self.cleaned_data.get('file')
        
        if file:
            # Validate file size and type
            validate_file_upload(file)
            
            # Set additional attributes for the model
            self.file_name = file.name
            self.file_size = file.size
            self.file_type = file.content_type
        
        return file
    
    def save(self, commit=True):
        """Save the attachment."""
        attachment = super().save(commit=False)
        
        # Set attachment properties
        attachment.note = self.note
        attachment.file_name = getattr(self, 'file_name', self.cleaned_data['file'].name)
        attachment.file_size = getattr(self, 'file_size', self.cleaned_data['file'].size)
        attachment.file_type = getattr(self, 'file_type', self.cleaned_data['file'].content_type)
        
        if commit:
            attachment.save()
        
        return attachment


class NoteSharingForm(forms.ModelForm):
    """Form for sharing notes with other users."""
    shared_with = forms.ModelChoiceField(
        queryset=User.objects.all(),
        widget=forms.Select(attrs={'class': 'form-select'}),
        help_text='Select a user to share this note with'
    )
    permission = forms.ChoiceField(
        choices=NoteSharing.PERMISSION_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'}),
        initial='read',
        help_text='Select permission level for this user'
    )
    
    class Meta:
        model = NoteSharing
        fields = ['shared_with', 'permission']
    
    def __init__(self, *args, **kwargs):
        """Initialize the form."""
        self.note = kwargs.pop('note', None)
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if self.user:
            # Exclude the current user from the queryset
            self.fields['shared_with'].queryset = User.objects.exclude(id=self.user.id)
    
    def clean_shared_with(self):
        """Validate that the note isn't already shared with this user."""
        shared_with = self.cleaned_data.get('shared_with')
        
        if shared_with and self.note:
            # Check if note is already shared with this user
            existing = NoteSharing.objects.filter(note=self.note, shared_with=shared_with)
            
            # If we're editing an existing sharing, exclude it from the check
            if self.instance and self.instance.pk:
                existing = existing.exclude(pk=self.instance.pk)
            
            if existing.exists():
                raise ValidationError('This note is already shared with this user.')
        
        return shared_with
    
    def clean(self):
        """Validate the form."""
        cleaned_data = super().clean()
        
        # Check maximum number of shared users per note
        if self.note and not self.instance.pk:  # Only for new sharing
            current_shared_count = NoteSharing.objects.filter(note=self.note).count()
            MAX_SHARED_USERS = 20  # Maximum number of users to share a note with
            
            if current_shared_count >= MAX_SHARED_USERS:
                raise ValidationError(f'You cannot share this note with more than {MAX_SHARED_USERS} users.')
        
        return cleaned_data
    
    def save(self, commit=True):
        """Save the note sharing."""
        sharing = super().save(commit=False)
        
        if self.note:
            sharing.note = self.note
        
        if commit:
            sharing.save()
        
        return sharing


class NoteSearchForm(forms.Form):
    """Form for searching notes."""
    query = forms.CharField(
        required=False,
        widget=forms.TextInput(
            attrs={'class': 'form-control', 'placeholder': 'Search notes...'}
        )
    )
    category = forms.ModelChoiceField(
        queryset=Category.objects.none(),
        required=False,
        empty_label="All Categories",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    tags = forms.ModelMultipleChoiceField(
        queryset=Tag.objects.none(),
        required=False,
        widget=forms.SelectMultiple(attrs={'class': 'form-select', 'size': 5})
    )
    
    # Add filter for archived notes
    include_archived = forms.BooleanField(
        required=False,
        initial=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label='Include archived notes'
    )
    
    # Add date range filters
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        label='From date'
    )
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        label='To date'
    )
    
    # Add option to include shared notes
    include_shared = forms.BooleanField(
        required=False,
        initial=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label='Include shared notes'
    )
    
    # Add sort options
    SORT_CHOICES = [
        ('updated_desc', 'Recently Updated'),
        ('updated_asc', 'Oldest Updated'),
        ('created_desc', 'Recently Created'),
        ('created_asc', 'Oldest Created'),
        ('title_asc', 'Title A-Z'),
        ('title_desc', 'Title Z-A'),
    ]
    
    sort_by = forms.ChoiceField(
        choices=SORT_CHOICES,
        required=False,
        initial='updated_desc',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    # Add search location options (title only, content only, or both)
    SEARCH_IN_CHOICES = [
        ('both', 'Title & Content'),
        ('title', 'Title Only'),
        ('content', 'Content Only')
    ]
    
    search_in = forms.ChoiceField(
        choices=SEARCH_IN_CHOICES,
        required=False,
        initial='both',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    # Add checkbox for exact phrase matching
    exact_match = forms.BooleanField(
        required=False,
        initial=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label='Match exact phrase'
    )
    
    def __init__(self, *args, **kwargs):
        """Initialize the form with user-specific categories and tags."""
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if self.user:
            # Filter categories by user
            self.fields['category'].queryset = Category.objects.filter(user=self.user)
            # Filter tags by user
            self.fields['tags'].queryset = Tag.objects.filter(user=self.user)
    
    def clean(self):
        """Validate the form."""
        cleaned_data = super().clean()
        
        # Validate date range
        date_from = cleaned_data.get('date_from')
        date_to = cleaned_data.get('date_to')
        
        if date_from and date_to and date_from > date_to:
            self.add_error('date_to', 'End date must be after start date.')
        
        return cleaned_data
    
    def get_search_queryset(self, user):
        """
        Apply all search and filter criteria to create a queryset.
        This method centralizes all filtering logic to make it reusable.
        """
        # Start with user's notes
        queryset = Note.objects.filter(user=user)
        
        # Get form data
        cleaned_data = self.cleaned_data
        
        # Apply text search filter
        query = cleaned_data.get('query')
        if query:
            search_in = cleaned_data.get('search_in', 'both')
            exact_match = cleaned_data.get('exact_match', False)
            
            if exact_match:
                # Exact phrase matching
                if search_in == 'title':
                    queryset = queryset.filter(title__icontains=query)
                elif search_in == 'content':
                    queryset = queryset.filter(content__icontains=query)
                else:  # both
                    queryset = queryset.filter(
                        Q(title__icontains=query) | Q(content__icontains=query)
                    )
            else:
                # Word-by-word matching
                terms = query.split()
                q_objects = Q()
                
                for term in terms:
                    if search_in == 'title':
                        q_objects |= Q(title__icontains=term)
                    elif search_in == 'content':
                        q_objects |= Q(content__icontains=term)
                    else:  # both
                        q_objects |= Q(title__icontains=term) | Q(content__icontains=term)
                
                queryset = queryset.filter(q_objects)
        
        # Apply category filter
        category = cleaned_data.get('category')
        if category:
            queryset = queryset.filter(category=category)
        
        # Apply tags filter
        tags = cleaned_data.get('tags')
        if tags:
            queryset = queryset.filter(tags__in=tags).distinct()
        
        # Apply archive filter
        include_archived = cleaned_data.get('include_archived', False)
        if not include_archived:
            queryset = queryset.filter(is_archived=False)
        
        # Apply date filters
        date_from = cleaned_data.get('date_from')
        if date_from:
            queryset = queryset.filter(updated_at__gte=date_from)
        
        date_to = cleaned_data.get('date_to')
        if date_to:
            queryset = queryset.filter(updated_at__lte=date_to)
        
        # Include shared notes
        include_shared = cleaned_data.get('include_shared', False)
        if include_shared:
            shared_notes = Note.objects.filter(shared_with=user)
            queryset = (queryset | shared_notes).distinct()
        
        # Apply sorting
        sort_by = cleaned_data.get('sort_by', 'updated_desc')
        
        if sort_by == 'updated_desc':
            queryset = queryset.order_by('-updated_at')
        elif sort_by == 'updated_asc':
            queryset = queryset.order_by('updated_at')
        elif sort_by == 'created_desc':
            queryset = queryset.order_by('-created_at')
        elif sort_by == 'created_asc':
            queryset = queryset.order_by('created_at')
        elif sort_by == 'title_asc':
            queryset = queryset.order_by('title')
        elif sort_by == 'title_desc':
            queryset = queryset.order_by('-title')
        else:
            # Default sort by pinned first, then updated
            queryset = queryset.order_by('-is_pinned', '-updated_at')
        
        return queryset 