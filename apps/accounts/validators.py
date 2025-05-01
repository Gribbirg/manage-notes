"""
Role-based validators for Notes Manager application.
This module contains validators for user roles and permissions.
"""
from django.core.exceptions import ValidationError, PermissionDenied
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.password_validation import validate_password as django_validate_password
from django.contrib.auth.models import User, Group
from django.core.validators import validate_email as django_validate_email
from functools import wraps
import re


def validate_admin_role(user):
    """
    Validate if the user has admin role.
    
    Args:
        user: User object to validate
    
    Raises:
        ValidationError: If the user does not have admin role
    """
    if not hasattr(user, 'profile') or not user.profile.is_admin:
        raise ValidationError(
            _("User does not have admin privileges."),
            code='not_admin'
        )


def validate_object_owner(user, obj):
    """
    Validate if the user is the owner of the object.
    
    Args:
        user: User object
        obj: Object to validate ownership
    
    Raises:
        ValidationError: If the user is not the owner of the object
    """
    if not hasattr(obj, 'user') or obj.user != user:
        raise ValidationError(
            _("You don't have permission to access this object."),
            code='not_owner'
        )


def validate_object_permission(user, obj, permission_types=None):
    """
    Validate if the user has permission to access the object.
    
    Args:
        user: User object
        obj: Object to validate access
        permission_types: List of permission types ('read', 'write', 'delete')
    
    Raises:
        ValidationError: If the user doesn't have permission to access the object
    """
    if not permission_types:
        permission_types = ['read']
    
    # Check if user is admin (admins have all permissions)
    if hasattr(user, 'profile') and user.profile.is_admin:
        return
    
    # Check if user is the owner
    if hasattr(obj, 'user') and obj.user == user:
        return
    
    # Check for shared access (if applicable)
    if hasattr(obj, 'shared_with') and user in obj.shared_with.all():
        # Check if the sharing includes the requested permission types
        if hasattr(obj, 'sharing_permissions'):
            # This assumes a field storing JSON or a ManyToMany with permission types
            for permission_type in permission_types:
                if permission_type not in obj.sharing_permissions.get(str(user.id), []):
                    raise ValidationError(
                        _("You don't have %(permission)s permission for this object."),
                        params={'permission': permission_type},
                        code=f'no_{permission_type}_permission'
                    )
        return
    
    # If we get here, the user doesn't have permission
    raise ValidationError(
        _("You don't have permission to access this object."),
        code='no_permission'
    )


def require_role(role):
    """
    Decorator to require specific user role.
    
    Args:
        role: Required role ('admin', 'user')
    
    Returns:
        Decorated function
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            user = request.user
            
            if not user.is_authenticated:
                raise PermissionDenied("Authentication required")
            
            if role == 'admin' and (not hasattr(user, 'profile') or not user.profile.is_admin):
                raise PermissionDenied("Admin privileges required")
            
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator


def require_permission(permission):
    """
    Decorator to require specific permission.
    
    Args:
        permission: Required permission (e.g., 'notes.add_note')
    
    Returns:
        Decorated function
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            user = request.user
            
            if not user.is_authenticated:
                raise PermissionDenied("Authentication required")
            
            if not user.has_perm(permission):
                raise PermissionDenied(f"Permission '{permission}' required")
            
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator


class RolePermissionMixin:
    """
    Mixin to add role-based permissions to class-based views.
    """
    required_role = None  # 'admin' or 'user'
    required_permission = None  # e.g., 'notes.add_note'
    
    def dispatch(self, request, *args, **kwargs):
        user = request.user
        
        if not user.is_authenticated:
            raise PermissionDenied("Authentication required")
        
        if self.required_role == 'admin' and (not hasattr(user, 'profile') or not user.profile.is_admin):
            raise PermissionDenied("Admin privileges required")
        
        if self.required_permission and not user.has_perm(self.required_permission):
            raise PermissionDenied(f"Permission '{self.required_permission}' required")
        
        return super().dispatch(request, *args, **kwargs)


class ObjectOwnerPermissionMixin:
    """
    Mixin to add object ownership validation to class-based views.
    """
    owner_field = 'user'  # Default field name for owner
    
    def get_object(self, *args, **kwargs):
        obj = super().get_object(*args, **kwargs)
        
        # Check if user is admin
        user = self.request.user
        if hasattr(user, 'profile') and user.profile.is_admin:
            return obj
        
        # Check ownership
        owner = getattr(obj, self.owner_field, None)
        if owner != user:
            raise PermissionDenied("You don't have permission to access this object")
        
        return obj


def validate_unique_username(username):
    """
    Validate if the username is unique.
    
    Args:
        username: Username to validate
    
    Raises:
        ValidationError: If the username already exists
    """
    if User.objects.filter(username__iexact=username).exists():
        raise ValidationError(
            _("This username is already taken."),
            code='username_taken'
        )


def validate_username_format(username):
    """
    Validate username format.
    
    Args:
        username: Username to validate
    
    Raises:
        ValidationError: If the username doesn't meet requirements
    """
    # Check length
    if len(username) < 3:
        raise ValidationError(
            _("Username must be at least 3 characters long."),
            code='username_too_short'
        )
    
    if len(username) > 30:
        raise ValidationError(
            _("Username cannot be more than 30 characters long."),
            code='username_too_long'
        )
    
    # Check characters
    if not re.match(r'^[a-zA-Z0-9_.-]+$', username):
        raise ValidationError(
            _("Username can only contain letters, numbers, and the characters: . _ -"),
            code='invalid_username_chars'
        )
    
    # Check if username starts with a letter
    if not username[0].isalpha():
        raise ValidationError(
            _("Username must start with a letter."),
            code='username_start_with_letter'
        )
    
    # Check for prohibited usernames
    prohibited_usernames = ['admin', 'administrator', 'root', 'superuser', 'system', 
                           'moderator', 'support', 'help', 'info', 'guest']
    if username.lower() in prohibited_usernames:
        raise ValidationError(
            _("This username is reserved and cannot be used."),
            code='reserved_username'
        )


def validate_email(email):
    """
    Validate email format and uniqueness.
    
    Args:
        email: Email to validate
    
    Raises:
        ValidationError: If the email is invalid or already exists
    """
    # Use Django's built-in email validator
    try:
        django_validate_email(email)
    except ValidationError:
        raise ValidationError(
            _("Please enter a valid email address."),
            code='invalid_email'
        )
    
    # Check if email is already taken
    if User.objects.filter(email__iexact=email).exists():
        raise ValidationError(
            _("This email is already registered."),
            code='email_taken'
        )
    
    # Check for disposable email domains
    disposable_domains = ['mailinator.com', 'tempmail.com', 'throwawaymail.com']
    domain = email.split('@')[-1].lower()
    if domain in disposable_domains:
        raise ValidationError(
            _("Disposable email addresses are not allowed."),
            code='disposable_email'
        )


def validate_password_strength(password):
    """
    Validate password strength.
    
    Args:
        password: Password to validate
    
    Raises:
        ValidationError: If the password does not meet the requirements
    """
    # First use Django's built-in password validators
    try:
        django_validate_password(password)
    except ValidationError as e:
        raise ValidationError(e)
    
    # Password must be at least 8 characters long
    if len(password) < 8:
        raise ValidationError(
            _("Password must be at least 8 characters long."),
            code='password_too_short'
        )
    
    # Password must contain at least one digit
    if not any(char.isdigit() for char in password):
        raise ValidationError(
            _("Password must contain at least one digit."),
            code='password_no_digit'
        )
    
    # Password must contain at least one uppercase letter
    if not any(char.isupper() for char in password):
        raise ValidationError(
            _("Password must contain at least one uppercase letter."),
            code='password_no_uppercase'
        )
    
    # Password must contain at least one lowercase letter
    if not any(char.islower() for char in password):
        raise ValidationError(
            _("Password must contain at least one lowercase letter."),
            code='password_no_lowercase'
        )
    
    # Password must contain at least one special character
    if not any(not char.isalnum() for char in password):
        raise ValidationError(
            _("Password must contain at least one special character."),
            code='password_no_special'
        )
    
    # Check for common patterns
    common_patterns = ['123456', 'password', 'qwerty', 'abc123', 'admin']
    password_lower = password.lower()
    for pattern in common_patterns:
        if pattern in password_lower:
            raise ValidationError(
                _("Password contains a common pattern that is easily guessable."),
                code='common_password_pattern'
            )
    
    # Check for repeating characters
    if re.search(r'(.)\1{2,}', password):  # Check for 3 or more repeating characters
        raise ValidationError(
            _("Password contains too many repeating characters."),
            code='repeating_characters'
        )


def validate_password_not_similar_to_user_info(password, user):
    """
    Validate password is not similar to user information.
    
    Args:
        password: Password to validate
        user: User object or user data dict
    
    Raises:
        ValidationError: If the password is too similar to user information
    """
    password_lower = password.lower()
    
    # Get user information
    if isinstance(user, User):
        user_data = {
            'username': user.username,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'email': user.email.split('@')[0]  # Only check the local part of the email
        }
    else:
        user_data = user
    
    # Check if password contains user information
    for field, value in user_data.items():
        if value and len(value) > 2 and value.lower() in password_lower:
            raise ValidationError(
                _("Password is too similar to your %(field_name)s."),
                params={'field_name': field.replace('_', ' ')},
                code='password_similar_to_user_info'
            ) 