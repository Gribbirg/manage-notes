from django.shortcuts import redirect
from django.contrib import messages
from django.urls import reverse
from django.http import HttpResponseForbidden, JsonResponse
from django.core.cache import cache
import re
import time
import logging

# Configure logger
logger = logging.getLogger(__name__)


class RoleMiddleware:
    """Middleware to check user roles and restrict access accordingly."""
    
    def __init__(self, get_response):
        self.get_response = get_response
        
        # Admin-only paths
        self.admin_only_paths = [
            '/admin/',  # Django admin site
            '/api/admin/',  # Admin API endpoints
            '/notes/admin/',  # Admin note management
        ]
    
    def __call__(self, request):
        # Skip middleware for anonymous users
        if not request.user.is_authenticated:
            return self.get_response(request)
        
        path = request.path
        
        # Check if the path is admin-only and user is not admin
        if any(path.startswith(admin_path) for admin_path in self.admin_only_paths):
            # Allow superusers and staff
            if request.user.is_superuser or request.user.is_staff:
                return self.get_response(request)
            
            # Allow users with admin profile
            try:
                if request.user.profile.is_admin:
                    return self.get_response(request)
            except:
                pass
            
            # Redirect non-admin users
            messages.error(request, "You don't have permission to access this area.")
            return redirect('notes:list')
        
        # Proceed with the request for non-restricted paths
        return self.get_response(request)


class RequestValidationMiddleware:
    """Middleware to validate incoming requests and prevent malicious activity."""
    
    def __init__(self, get_response):
        self.get_response = get_response
        
        # Patterns that could indicate malicious requests
        self.suspicious_patterns = [
            r'<script.*?>',  # Potential XSS
            r'SELECT.*FROM',  # Potential SQL injection
            r'DELETE.*FROM',  # Potential SQL injection
            r'UPDATE.*SET',   # Potential SQL injection
            r'\.\./',         # Path traversal
            r'etc/passwd',    # Path traversal targeting system files
        ]
    
    def __call__(self, request):
        # Skip validation for static files and media
        if any(path in request.path for path in ['/static/', '/media/']):
            return self.get_response(request)
        
        # Check if request contains suspicious patterns
        if self._is_suspicious_request(request):
            logger.warning(f"Suspicious request blocked: {request.path} from {request.META.get('REMOTE_ADDR')}")
            return HttpResponseForbidden("Request blocked for security reasons")
        
        # Proceed with valid request
        return self.get_response(request)
    
    def _is_suspicious_request(self, request):
        """Check if request contains suspicious patterns."""
        # Combine all request parameters for checking
        request_data = []
        
        # Check GET parameters
        for key, value in request.GET.items():
            request_data.append(f"{key}={value}")
        
        # Check POST parameters if it's not a file upload
        if not request.META.get('CONTENT_TYPE', '').startswith('multipart/form-data'):
            for key, value in request.POST.items():
                request_data.append(f"{key}={value}")
        
        # Check query string
        if request.META.get('QUERY_STRING'):
            request_data.append(request.META.get('QUERY_STRING'))
        
        # Check path
        request_data.append(request.path)
        
        # Check if any suspicious pattern is found
        for pattern in self.suspicious_patterns:
            for data in request_data:
                if re.search(pattern, data, re.IGNORECASE):
                    return True
        
        return False


class RateLimitMiddleware:
    """Middleware to implement rate limiting for API endpoints."""
    
    def __init__(self, get_response):
        self.get_response = get_response
        
        # Rate limits per endpoint group (requests per minute)
        self.rate_limits = {
            'api': 60,  # 60 requests per minute for API endpoints
            'search': 30,  # 30 search requests per minute
            'auth': 10,  # 10 authentication requests per minute
        }
    
    def __call__(self, request):
        # Skip rate limiting for admin users
        if request.user.is_authenticated and (request.user.is_superuser or 
            (hasattr(request.user, 'profile') and request.user.profile.is_admin)):
            return self.get_response(request)
        
        path = request.path
        
        # Determine which endpoint group this request belongs to
        limit_group = None
        if path.startswith('/api/'):
            limit_group = 'api'
        elif '/search' in path or 'query' in request.GET:
            limit_group = 'search'
        elif '/login' in path or '/register' in path or '/auth' in path:
            limit_group = 'auth'
        
        # Apply rate limiting if path belongs to a limited group
        if limit_group and not self._check_rate_limit(request, limit_group):
            logger.warning(f"Rate limit exceeded: {path} from {request.META.get('REMOTE_ADDR')}")
            
            # Return JSON response for API requests
            if path.startswith('/api/'):
                return JsonResponse({'error': 'Rate limit exceeded'}, status=429)
            
            # Return error message for normal requests
            messages.error(request, "Too many requests. Please try again later.")
            return redirect('notes:dashboard')
        
        # Proceed with the request
        return self.get_response(request)
    
    def _check_rate_limit(self, request, limit_group):
        """
        Check if request exceeds rate limit for the specified group.
        Returns True if request is allowed, False if rate limit is exceeded.
        """
        # Get rate limit for the group
        requests_per_minute = self.rate_limits.get(limit_group, 60)
        
        # Create a unique key for the client
        client_ip = request.META.get('REMOTE_ADDR')
        if request.user.is_authenticated:
            client_id = f"user_{request.user.id}_{limit_group}"
        else:
            client_id = f"ip_{client_ip}_{limit_group}"
        
        # Get the current minute timestamp (rounded down)
        current_minute = int(time.time() / 60)
        cache_key = f"rate_limit:{client_id}:{current_minute}"
        
        # Get current request count from cache
        request_count = cache.get(cache_key, 0)
        
        # Check if request count exceeds the limit
        if request_count >= requests_per_minute:
            return False
        
        # Increment the request count (expire after 1 minute)
        cache.set(cache_key, request_count + 1, timeout=60)
        
        return True


class ContentSecurityPolicyMiddleware:
    """Middleware to add Content-Security-Policy headers to responses."""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        response = self.get_response(request)
        
        # Define Content Security Policy
        csp_directives = [
            "default-src 'self'",
            "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net",
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net",
            "img-src 'self' data: https:",
            "font-src 'self' https://cdn.jsdelivr.net",
            "connect-src 'self'",
            "frame-ancestors 'none'",
            "form-action 'self'",
        ]
        
        # Add CSP header to the response
        response['Content-Security-Policy'] = '; '.join(csp_directives)
        
        # Add other security headers
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['X-XSS-Protection'] = '1; mode=block'
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        return response 