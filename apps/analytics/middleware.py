import time
import psutil
import traceback
import re
import uuid
from user_agents import parse
from .models import RequestLog, ComplianceLog
from django.http import Http404, HttpResponseBadRequest
from django.utils import timezone
from datetime import timedelta
from django.core.cache import cache
import logging

logger = logging.getLogger(__name__)

class AnalyticsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.RATE_LIMIT = 100
        self.RATE_WINDOW = 3600
        # Patterns untuk mendeteksi aktivitas mencurigakan
        self.SUSPICIOUS_PATTERNS = [
            r"(?i)(union|select|insert|delete|drop|update|;|\-\-)",  # SQL Injection
            r"(?i)<script.*?>",  # XSS
            r"(?i)(\.\.\/|\.\.\\)",  # Path Traversal
        ]

    def is_suspicious_request(self, request):
        """Check for suspicious patterns in request"""
        # Check query parameters
        for param, value in request.GET.items():
            for pattern in self.SUSPICIOUS_PATTERNS:
                if re.search(pattern, str(value)):
                    return True, "Suspicious query parameter"

        # Check POST data
        for param, value in request.POST.items():
            for pattern in self.SUSPICIOUS_PATTERNS:
                if re.search(pattern, str(value)):
                    return True, "Suspicious POST data"

        # Check headers for common attack vectors
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        if not user_agent or user_agent in ['', 'None', 'curl', 'wget']:
            return True, "Suspicious user agent"

        return False, None

    def get_auth_info(self, request):
        """Get authentication information from request"""
        auth_status = None
        user_id = None
        api_key = None
        auth_method = None

        # Check API key in headers
        api_key = request.META.get('HTTP_X_API_KEY')
        if api_key:
            auth_method = 'api_key'

        # Check user authentication
        if hasattr(request, 'user') and request.user.is_authenticated:
            auth_status = 'success'
            user_id = request.user.id
            auth_method = auth_method or 'session'
        else:
            auth_status = 'anonymous'

        return auth_status, user_id, api_key, auth_method

    def get_rate_limit_key(self, request):
        """Generate rate limit key based on IP"""
        ip = request.META.get('HTTP_X_FORWARDED_FOR', '') or request.META.get('REMOTE_ADDR')
        return f"rate_limit:{ip}"

    def check_rate_limit(self, key):
        """Check if request should be rate limited"""
        now = timezone.now()
        window_start = now - timedelta(seconds=self.RATE_WINDOW)
        
        # Get current count from cache
        cache_key = f"cache_{key}"
        count = cache.get(cache_key, 0)
        
        if count >= self.RATE_LIMIT:
            return True, count
        
        # Increment counter
        cache.set(cache_key, count + 1, self.RATE_WINDOW)
        return False, count + 1

    def get_session_id(self, request):
        """Get or create session ID"""
        session_id = request.session.get('analytics_session_id')
        if not session_id:
            session_id = str(uuid.uuid4())
            request.session['analytics_session_id'] = session_id
        return session_id

    def get_user_type(self, request):
        """Determine user type"""
        if not hasattr(request, 'user') or not request.user.is_authenticated:
            return 'guest'
        # Anda bisa menambahkan logika custom di sini
        # Contoh: if request.user.is_premium: return 'premium'
        return 'registered'

    def get_feature_info(self, request):
        """Extract feature and interaction information"""
        path = request.path.strip('/').split('/')
        feature = None
        interaction = 'view'

        # Detect feature
        if path and path[0] == 'api':
            if len(path) > 1:
                feature = path[1]
            
            # Detect interaction type
            if request.GET.get('search'):
                interaction = 'search'
            elif request.GET.get('filter'):
                interaction = 'filter'
            elif request.method == 'POST':
                interaction = 'create'
            elif request.method == 'PUT':
                interaction = 'update'
            elif request.method == 'DELETE':
                interaction = 'delete'

        return feature, interaction

    def detect_conversion(self, request, response):
        """Detect if a conversion goal was achieved"""
        # Contoh logika konversi sederhana
        if response.status_code == 201:  # Created
            return 'content_created'
        if 'download' in request.path:
            return 'content_downloaded'
        if 'share' in request.path:
            return 'content_shared'
        return None

    def __call__(self, request):
        logger.info(f"Processing request: {request.path}")
        # Catat waktu mulai
        start_time = time.time()
        
        # Catat penggunaan memori awal
        process = psutil.Process()
        memory_start = process.memory_info().rss / 1024 / 1024  # Convert to MB
        
        # Security checks
        is_suspicious, suspicious_reason = self.is_suspicious_request(request)
        auth_status, user_id, api_key, auth_method = self.get_auth_info(request)
        
        # Business metrics preparation
        session_id = self.get_session_id(request)
        user_type = self.get_user_type(request)
        feature_accessed, interaction_type = self.get_feature_info(request)
        request.start_time = start_time  # Store for engagement time calculation
        
        # Rate limiting check
        is_error = False
        error_type = None
        error_message = None
        error_stack = None
        rate_limit_key = None
        rate_limit_count = 0
        is_throttled = False
        
        try:
            if request.path.startswith('/api/'):
                rate_limit_key = self.get_rate_limit_key(request)
                is_throttled, rate_limit_count = self.check_rate_limit(rate_limit_key)
                
                if is_throttled:
                    is_error = True
                    error_type = "RateLimit"
                    error_message = "Too many requests"
                    return HttpResponseBadRequest("Rate limit exceeded")
            
            # Proses request
            response = self.get_response(request)
            is_error = 400 <= response.status_code < 600
            
            # Detect conversion after response
            conversion_goal = self.detect_conversion(request, response)
            
            # Calculate engagement time
            engagement_time = int((time.time() - start_time) * 1000)  # in milliseconds

            # Jika ada error dari response
            if is_error:
                error_type = f"HTTP{response.status_code}"
                error_message = response.reason_phrase
                if response.status_code in [401, 403]:
                    auth_status = 'failed'
            
        except Http404 as e:
            is_error = True
            error_type = "Http404"
            error_message = str(e)
            error_stack = traceback.format_exc()
            response = self.get_response(request)
            
        except Exception as e:
            is_error = True
            error_type = e.__class__.__name__
            error_message = str(e)
            error_stack = traceback.format_exc()
            raise
        
        finally:
            if request.path.startswith('/api/'):
                # Hitung metrics
                response_time = (time.time() - start_time) * 1000
                memory_used = (process.memory_info().rss / 1024 / 1024) - memory_start
                
                # Parse User-Agent
                user_agent_string = request.META.get('HTTP_USER_AGENT', '')
                user_agent = parse(user_agent_string)
                
                # Get IP address
                ip_address = request.META.get('HTTP_X_FORWARDED_FOR', '') or request.META.get('REMOTE_ADDR')
                
                # Tentukan content type dan ID
                content_type = None
                content_id = None
                
                if 'latest-content' in request.path:
                    content_type = 'latest-content'
                elif any(model in request.path for model in ['destinations', 'flora', 'fauna', 'kuliner', 'health']):
                    path_parts = request.path.strip('/').split('/')
                    content_type = path_parts[1]
                    if len(path_parts) > 2:
                        content_id = path_parts[2]
                
                # Simpan log
                RequestLog.objects.create(
                    # Request Metrics
                    endpoint=request.path,
                    method=request.method,
                    status_code=getattr(response, 'status_code', 500),
                    response_time=response_time,
                    ip_address=ip_address,
                    db_query_time=getattr(request, '_db_time', None),
                    memory_usage=memory_used,
                    content_type=content_type,
                    content_id=content_id,
                    
                    # User/Client Metrics
                    user_agent=user_agent_string,
                    device_type=user_agent.device.family,
                    browser=user_agent.browser.family,
                    os=user_agent.os.family,
                    referrer=request.META.get('HTTP_REFERER', None),
                    
                    # Error Tracking
                    is_error=is_error,
                    error_type=error_type,
                    error_message=error_message,
                    error_stack=error_stack,
                    
                    # Rate Limiting
                    rate_limit_key=rate_limit_key,
                    rate_limit_count=rate_limit_count,
                    rate_limit_window=timezone.now(),
                    is_throttled=is_throttled,
                    
                    # Security Metrics (new)
                    auth_status=auth_status,
                    user_id=user_id,
                    api_key=api_key,
                    is_suspicious=is_suspicious,
                    security_flags={
                        'suspicious_reason': suspicious_reason,
                        'auth_failures': auth_status == 'failed',
                        'unusual_timing': response_time > 5000,  # Flag if response time > 5s
                    },
                    auth_method=auth_method,

                    # Business Metrics (new)
                    session_id=session_id,
                    user_type=user_type,
                    feature_accessed=feature_accessed,
                    interaction_type=interaction_type,
                    conversion_goal=conversion_goal,
                    engagement_time=engagement_time,
                )
        
        return response

class ComplianceLoggingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Pre-processing
        response = self.get_response(request)
        
        # Post-processing
        sensitive_paths = [
            '/api/users/',
            '/api/payment/',
            '/api/documents/'
        ]
        
        if any(path in request.path for path in sensitive_paths):
            ComplianceLog.objects.create(
                user_id=request.user.id if request.user.is_authenticated else None,
                ip_address=request.META.get('REMOTE_ADDR'),
                action_type='access',
                data_category=self._get_data_category(request.path),
                sensitivity_level=self._get_sensitivity_level(request.path),
                purpose='API Access',
                processing_location='local',
            )
        
        return response

    def _get_data_category(self, path):
        # Logic untuk menentukan kategori data
        if 'users' in path:
            return 'user_data'
        elif 'payment' in path:
            return 'financial_data'
        return 'general'

    def _get_sensitivity_level(self, path):
        if 'payment' in path:
            return 'critical'
        elif 'users' in path:
            return 'high'
        return 'low'
