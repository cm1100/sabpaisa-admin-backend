"""
Custom middleware for error handling and request processing
Following Django middleware best practices
"""
import json
import logging
import time
import uuid
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.db import DatabaseError, IntegrityError
from rest_framework import status
from rest_framework.exceptions import (
    APIException, AuthenticationFailed, NotAuthenticated,
    PermissionDenied, NotFound, MethodNotAllowed
)

logger = logging.getLogger(__name__)


class ErrorHandlingMiddleware(MiddlewareMixin):
    """
    Comprehensive error handling middleware
    Catches and formats all exceptions consistently
    """
    
    def process_exception(self, request, exception):
        """
        Process exceptions and return formatted JSON responses
        """
        # Generate unique error ID for tracking
        error_id = str(uuid.uuid4())
        
        # Log the error with full context
        logger.error(
            f"Error ID: {error_id} | "
            f"Path: {request.path} | "
            f"Method: {request.method} | "
            f"User: {getattr(request, 'user', 'Anonymous')} | "
            f"Exception: {str(exception)}",
            exc_info=True
        )
        
        # Determine error response based on exception type
        if isinstance(exception, NotAuthenticated):
            return self.create_error_response(
                error_id=error_id,
                message="Authentication required",
                status_code=status.HTTP_401_UNAUTHORIZED,
                error_type="AUTHENTICATION_ERROR"
            )
        
        elif isinstance(exception, AuthenticationFailed):
            return self.create_error_response(
                error_id=error_id,
                message="Authentication failed",
                status_code=status.HTTP_401_UNAUTHORIZED,
                error_type="AUTHENTICATION_ERROR"
            )
        
        elif isinstance(exception, PermissionDenied):
            return self.create_error_response(
                error_id=error_id,
                message="Permission denied",
                status_code=status.HTTP_403_FORBIDDEN,
                error_type="PERMISSION_ERROR"
            )
        
        elif isinstance(exception, NotFound) or isinstance(exception, ObjectDoesNotExist):
            return self.create_error_response(
                error_id=error_id,
                message="Resource not found",
                status_code=status.HTTP_404_NOT_FOUND,
                error_type="NOT_FOUND_ERROR"
            )
        
        elif isinstance(exception, MethodNotAllowed):
            return self.create_error_response(
                error_id=error_id,
                message=f"Method {request.method} not allowed",
                status_code=status.HTTP_405_METHOD_NOT_ALLOWED,
                error_type="METHOD_ERROR"
            )
        
        elif isinstance(exception, ValidationError):
            return self.create_error_response(
                error_id=error_id,
                message="Validation error",
                status_code=status.HTTP_400_BAD_REQUEST,
                error_type="VALIDATION_ERROR",
                details=exception.message_dict if hasattr(exception, 'message_dict') else str(exception)
            )
        
        elif isinstance(exception, IntegrityError):
            return self.create_error_response(
                error_id=error_id,
                message="Database integrity error",
                status_code=status.HTTP_409_CONFLICT,
                error_type="DATABASE_ERROR"
            )
        
        elif isinstance(exception, DatabaseError):
            return self.create_error_response(
                error_id=error_id,
                message="Database error occurred",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                error_type="DATABASE_ERROR"
            )
        
        elif isinstance(exception, APIException):
            return self.create_error_response(
                error_id=error_id,
                message=str(exception),
                status_code=exception.status_code,
                error_type="API_ERROR"
            )
        
        else:
            # Generic error handler for unexpected exceptions
            return self.create_error_response(
                error_id=error_id,
                message="An unexpected error occurred",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                error_type="INTERNAL_ERROR"
            )
    
    def create_error_response(self, error_id, message, status_code, error_type, details=None):
        """
        Create a standardized error response
        """
        error_data = {
            'error': {
                'id': error_id,
                'type': error_type,
                'message': message,
                'status_code': status_code,
            }
        }
        
        if details:
            error_data['error']['details'] = details
        
        return JsonResponse(error_data, status=status_code)


class RequestLoggingMiddleware(MiddlewareMixin):
    """
    Middleware for logging all API requests and responses
    """
    
    def process_request(self, request):
        """
        Log incoming requests
        """
        # Skip logging for static files and health checks
        if self.should_skip_logging(request.path):
            return
        
        # Add request ID for tracking
        request.request_id = str(uuid.uuid4())
        request.start_time = time.time()
        
        # Log request details
        logger.info(
            f"Request ID: {request.request_id} | "
            f"Method: {request.method} | "
            f"Path: {request.path} | "
            f"User: {getattr(request, 'user', 'Anonymous')}"
        )
    
    def process_response(self, request, response):
        """
        Log response details
        """
        # Skip logging for static files and health checks
        if self.should_skip_logging(request.path):
            return response
        
        # Calculate request duration
        duration = None
        if hasattr(request, 'start_time'):
            duration = round((time.time() - request.start_time) * 1000, 2)
        
        # Log response details
        logger.info(
            f"Request ID: {getattr(request, 'request_id', 'N/A')} | "
            f"Status: {response.status_code} | "
            f"Duration: {duration}ms"
        )
        
        # Add custom headers
        if hasattr(request, 'request_id'):
            response['X-Request-ID'] = request.request_id
        if duration:
            response['X-Response-Time'] = f"{duration}ms"
        
        return response
    
    def should_skip_logging(self, path):
        """
        Check if path should be skipped from logging
        """
        skip_patterns = [
            '/static/',
            '/media/',
            '/health/',
            '/favicon.ico',
            '/__debug__/',
        ]
        return any(pattern in path for pattern in skip_patterns)


class RateLimitingMiddleware(MiddlewareMixin):
    """
    Simple rate limiting middleware
    """
    
    def __init__(self, get_response):
        super().__init__(get_response)
        self.request_counts = {}
        self.window_size = 60  # 1 minute window
        self.max_requests = 100  # Max requests per window
    
    def process_request(self, request):
        """
        Check rate limits for the request
        """
        # Skip rate limiting for certain paths
        if self.should_skip_rate_limit(request.path):
            return
        
        # Get client identifier (IP address or user)
        client_id = self.get_client_id(request)
        current_time = time.time()
        
        # Clean old entries
        self.clean_old_entries(current_time)
        
        # Check rate limit
        if client_id in self.request_counts:
            requests = self.request_counts[client_id]
            recent_requests = [t for t in requests if current_time - t < self.window_size]
            
            if len(recent_requests) >= self.max_requests:
                logger.warning(f"Rate limit exceeded for client: {client_id}")
                return JsonResponse({
                    'error': {
                        'type': 'RATE_LIMIT_ERROR',
                        'message': 'Too many requests. Please try again later.',
                        'status_code': 429
                    }
                }, status=429)
            
            self.request_counts[client_id] = recent_requests + [current_time]
        else:
            self.request_counts[client_id] = [current_time]
    
    def get_client_id(self, request):
        """
        Get unique client identifier
        """
        if request.user and request.user.is_authenticated:
            return f"user_{request.user.id}"
        else:
            # Use IP address for anonymous users
            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
            if x_forwarded_for:
                ip = x_forwarded_for.split(',')[0]
            else:
                ip = request.META.get('REMOTE_ADDR')
            return f"ip_{ip}"
    
    def clean_old_entries(self, current_time):
        """
        Remove old entries from request counts
        """
        for client_id in list(self.request_counts.keys()):
            requests = self.request_counts[client_id]
            recent_requests = [t for t in requests if current_time - t < self.window_size]
            if recent_requests:
                self.request_counts[client_id] = recent_requests
            else:
                del self.request_counts[client_id]
    
    def should_skip_rate_limit(self, path):
        """
        Check if path should be skipped from rate limiting
        """
        skip_patterns = [
            '/static/',
            '/media/',
            '/health/',
            '/api/docs/',
        ]
        return any(pattern in path for pattern in skip_patterns)


class SecurityHeadersMiddleware(MiddlewareMixin):
    """
    Middleware to add security headers to responses
    """
    
    def process_response(self, request, response):
        """
        Add security headers to response
        """
        # Content Security Policy
        response['Content-Security-Policy'] = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline';"
        
        # X-Content-Type-Options
        response['X-Content-Type-Options'] = 'nosniff'
        
        # X-Frame-Options
        response['X-Frame-Options'] = 'DENY'
        
        # X-XSS-Protection
        response['X-XSS-Protection'] = '1; mode=block'
        
        # Strict-Transport-Security (HSTS)
        if request.is_secure():
            response['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        
        # Referrer-Policy
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        return response