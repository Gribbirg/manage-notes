"""
Validators for Notes Manager application.
This module contains custom validators for notes, categories, and tags.
"""
import re
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.core.validators import FileExtensionValidator
from django.db import models


class BlacklistValidator:
    """
    Validator for checking if text contains blacklisted words.
    """
    def __init__(self, blacklist=None, message=None):
        self.blacklist = blacklist or []
        self.message = message or _("This text contains prohibited word: %(word)s")

    def __call__(self, value):
        if not value:
            return
        
        value_lower = value.lower()
        for word in self.blacklist:
            if word.lower() in value_lower:
                raise ValidationError(
                    self.message,
                    params={'word': word},
                    code='blacklisted_word'
                )


class SpecialCharValidator:
    """
    Validator for checking if text contains allowed special characters.
    """
    def __init__(self, allowed_chars=None, message=None):
        self.allowed_chars = allowed_chars or r'a-zA-Z0-9\s.,;:!?()-_@#$%&*+='
        self.message = message or _("This text contains invalid characters. Only %(allowed)s are allowed.")
        self.pattern = re.compile(f'^[{self.allowed_chars}]+$')

    def __call__(self, value):
        if not value:
            return
        
        if not self.pattern.match(value):
            raise ValidationError(
                self.message,
                params={'allowed': self.allowed_chars},
                code='invalid_characters'
            )


class LengthValidator:
    """
    Validator for checking text length.
    """
    def __init__(self, min_length=None, max_length=None, message_min=None, message_max=None):
        self.min_length = min_length
        self.max_length = max_length
        self.message_min = message_min or _("This text is too short. Minimum length is %(min)d characters.")
        self.message_max = message_max or _("This text is too long. Maximum length is %(max)d characters.")

    def __call__(self, value):
        if not value:
            return
        
        value_length = len(value)
        
        if self.min_length is not None and value_length < self.min_length:
            raise ValidationError(
                self.message_min,
                params={'min': self.min_length, 'current': value_length},
                code='text_too_short'
            )
        
        if self.max_length is not None and value_length > self.max_length:
            raise ValidationError(
                self.message_max,
                params={'max': self.max_length, 'current': value_length},
                code='text_too_long'
            )


class ProfanityValidator:
    """
    Validator for checking if text contains profanity.
    Uses a more comprehensive list than BlacklistValidator.
    """
    def __init__(self, profanity_list=None, message=None):
        self.profanity_list = profanity_list or [
            'profanity', 'obscene', 'vulgar', 'explicit',
            # Add more profanity words here
        ]
        self.message = message or _("This text contains profanity.")

    def __call__(self, value):
        if not value:
            return
        
        value_lower = value.lower()
        found_profanity = []
        
        for word in self.profanity_list:
            if re.search(r'\b' + re.escape(word) + r'\b', value_lower):
                found_profanity.append(word)
        
        if found_profanity:
            raise ValidationError(
                self.message,
                code='contains_profanity'
            )


class HTMLContentValidator:
    """
    Validator for checking if text contains HTML tags.
    Can be configured to allow certain tags.
    """
    def __init__(self, allowed_tags=None, message=None):
        self.allowed_tags = allowed_tags or []
        self.message = message or _("This text contains HTML tags, which are not allowed.")
        
        # Create regex pattern for allowed tags
        if allowed_tags:
            allowed_pattern = '|'.join(re.escape(tag) for tag in allowed_tags)
            self.pattern = re.compile(f'<(?!/?(({allowed_pattern})( [^>]*)?>|!--|/?>))', re.IGNORECASE)
        else:
            self.pattern = re.compile(r'<[^>]*>')

    def __call__(self, value):
        if not value:
            return
        
        if self.allowed_tags:
            # Check for any tags not in the allowed list
            if self.pattern.search(value):
                raise ValidationError(
                    self.message,
                    code='html_not_allowed'
                )
        else:
            # No tags allowed
            if re.search(r'<[^>]*>', value):
                raise ValidationError(
                    self.message,
                    code='html_not_allowed'
                )


# Common validators for notes
def validate_note_title(value):
    """
    Validate note title.
    - Must not be empty
    - Must be between 3 and 200 characters
    - Must not contain prohibited words
    """
    # Check for prohibited words
    prohibited_words = ['spam', 'junk', 'inappropriate', 'offensive']
    BlacklistValidator(blacklist=prohibited_words)(value)
    
    # Check length
    LengthValidator(min_length=3, max_length=200)(value)
    
    # Check for HTML tags (simple check)
    HTMLContentValidator()(value)
    
    # Check for profanity
    ProfanityValidator()(value)


def validate_note_content(value):
    """
    Validate note content.
    - Must not be empty
    - Must not be too short
    - Must not contain prohibited words
    """
    # Check for prohibited words
    prohibited_words = ['spam', 'scam', 'offensive', 'inappropriate']
    BlacklistValidator(blacklist=prohibited_words)(value)
    
    # Check length
    LengthValidator(min_length=5)(value)
    
    # Check for suspicious patterns (e.g., excessive URLs)
    url_count = len(re.findall(r'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+', value))
    if url_count > 10:
        raise ValidationError(
            _("Content contains too many URLs (%(count)d). Maximum allowed is 10."),
            params={'count': url_count},
            code='too_many_urls'
        )
    
    # Check for profanity
    ProfanityValidator()(value)
    
    # Check for excessive capitalization (shouting)
    if len(value) > 20:  # Only check longer content
        uppercase_ratio = sum(1 for c in value if c.isupper()) / len([c for c in value if c.isalpha()])
        if uppercase_ratio > 0.7:  # If more than 70% of alphabetic chars are uppercase
            raise ValidationError(
                _("Content contains excessive capitalization."),
                code='excessive_caps'
            )


# Category validators
def validate_category_name(value):
    """
    Validate category name.
    - Must not be empty
    - Must be between 2 and 100 characters
    - Must not contain prohibited words
    - Must contain only allowed characters
    """
    # Check for prohibited words
    prohibited_words = ['spam', 'junk', 'test', 'undefined', 'none']
    BlacklistValidator(blacklist=prohibited_words)(value)
    
    # Check length
    LengthValidator(min_length=2, max_length=100)(value)
    
    # Check characters
    allowed_chars = r'a-zA-Z0-9\s_-'
    SpecialCharValidator(allowed_chars=allowed_chars)(value)
    
    # Check for profanity
    ProfanityValidator()(value)


# Tag validators
def validate_tag_name(value):
    """
    Validate tag name.
    - Must not be empty
    - Must be between 2 and 50 characters
    - Must not contain prohibited words
    - Must contain only allowed characters
    """
    # Check for prohibited words
    prohibited_words = ['spam', 'junk', 'test', 'undefined', 'none']
    BlacklistValidator(blacklist=prohibited_words)(value)
    
    # Check length
    LengthValidator(min_length=2, max_length=50)(value)
    
    # Check characters - tags should be more restrictive
    allowed_chars = r'a-zA-Z0-9_-'
    SpecialCharValidator(allowed_chars=allowed_chars)(value)
    
    # Tags should not start with numbers
    if re.match(r'^\d', value):
        raise ValidationError(
            _("Tag name cannot start with a number."),
            code='tag_starts_with_number'
        )
    
    # Check for profanity
    ProfanityValidator()(value)


# File validators
def validate_file_upload(file):
    """
    Validate uploaded files.
    - Check size
    - Check file type
    """
    # Check file size (max 5MB)
    max_size = 5 * 1024 * 1024  # 5MB in bytes
    if file.size > max_size:
        raise ValidationError(
            _("File size cannot exceed 5MB."),
            code='file_too_large'
        )


# Validate file extensions
validate_document_file_extension = FileExtensionValidator(
    allowed_extensions=['pdf', 'doc', 'docx', 'txt', 'rtf', 'odt'],
    message=_("Only PDF, DOC, DOCX, TXT, RTF, and ODT files are allowed.")
)


validate_image_file_extension = FileExtensionValidator(
    allowed_extensions=['jpg', 'jpeg', 'png', 'gif', 'bmp', 'svg'],
    message=_("Only JPG, JPEG, PNG, GIF, BMP, and SVG files are allowed.")
)


# System validators
def validate_user_quota(user, model_class, max_count, message=None):
    """
    Validate user quota for models (notes, categories, tags).
    
    Args:
        user: User object
        model_class: Model class to check count
        max_count: Maximum allowed count
        message: Custom error message
    """
    current_count = model_class.objects.filter(user=user).count()
    
    if current_count >= max_count:
        model_name = model_class._meta.verbose_name_plural.lower()
        default_message = _(f"You have reached the maximum number of {model_name} allowed (%(max)d).")
        message = message or default_message
        
        raise ValidationError(
            message,
            params={'max': max_count, 'current': current_count},
            code='quota_exceeded'
        )


def validate_content_quota(user, current_size=0, max_size=None):
    """
    Validate total content size quota for a user.
    
    Args:
        user: User object
        current_size: Size of current content being added (in bytes)
        max_size: Maximum allowed total size (in bytes)
    """
    if max_size is None:
        max_size = 10 * 1024 * 1024  # Default 10MB
    
    # Calculate total size of all user's notes
    from django.db.models import Sum
    from django.db.models.functions import Length
    from .models import Note
    
    total_size = Note.objects.filter(user=user).aggregate(
        total=Sum(Length('content'))
    )['total'] or 0
    
    new_total = total_size + current_size
    
    if new_total > max_size:
        raise ValidationError(
            _("You have reached your content quota limit of %(max)s MB."),
            params={'max': max_size / (1024 * 1024)},  # Convert to MB for display
            code='content_quota_exceeded'
        ) 