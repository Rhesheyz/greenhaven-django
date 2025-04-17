import time
import json
from .models import AIAnalytics, AIFeedbackAnalytics
import uuid

class AIAnalyticsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Only track AI endpoints
        if not request.path.startswith('/api/chatbot/'):
            return self.get_response(request)

        # Start timing
        start_time = time.time()
        
        # Store request body and generate anonymous session if needed
        request_data = {}
        session_id = None
        
        if request.method == 'POST':
            try:
                # Save the body content
                body = request.body
                if body:
                    # Create a new stream for the body
                    request._body = body
                    # Parse the body
                    request_data = json.loads(body.decode('utf-8'))
                    session_id = request_data.get('session_id')
            except (json.JSONDecodeError, UnicodeDecodeError):
                pass

        # Generate anonymous session ID if none provided
        if not session_id:
            session_id = f"anon_{str(uuid.uuid4())[:8]}"
        
        response = self.get_response(request)
        
        # Calculate response time
        response_time = time.time() - start_time

        try:
            # Get endpoint type
            endpoint = request.path.split('/')[-2] if request.path.endswith('/') else request.path.split('/')[-1]

            # Get response data
            try:
                response_data = json.loads(response.content.decode('utf-8'))
                error_message = str(response_data.get('error')) if response.status_code >= 400 else None
            except (json.JSONDecodeError, AttributeError):
                error_message = None

            # Store sanitized request data (remove sensitive info if needed)
            safe_request_data = {
                'endpoint': endpoint,
                'method': request.method,
                'path': request.path,
            }
            if request_data:
                # Remove sensitive data if any
                if 'message' in request_data:
                    safe_request_data['message'] = request_data['message']

            # Create analytics entry
            AIAnalytics.objects.create(
                session_id=session_id,  # Now using generated session_id if none provided
                endpoint=endpoint,
                response_time=response_time,
                success=200 <= response.status_code < 300,
                error_message=error_message,
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT'),
                request_data=safe_request_data
            )
        except Exception as e:
            print(f"Error in AIAnalyticsMiddleware: {str(e)}")

        return response 

class AIFeedbackAnalyticsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Only track feedback endpoints
        if not request.path.startswith('/api/chatbot/feedback/'):
            return self.get_response(request)

        # Start timing
        start_time = time.time()
        
        # Store request data
        request_data = {}
        session_id = None
        
        if request.method == 'POST':
            try:
                body = request.body
                if body:
                    request._body = body
                    request_data = json.loads(body.decode('utf-8'))
                    session_id = request_data.get('session_id')
            except (json.JSONDecodeError, UnicodeDecodeError):
                pass

        # Generate anonymous session ID if none provided
        if not session_id:
            session_id = f"anon_{str(uuid.uuid4())[:8]}"
        
        response = self.get_response(request)
        
        # Calculate response time
        response_time = time.time() - start_time

        try:
            # Create feedback analytics entry
            AIFeedbackAnalytics.objects.create(
                session_id=session_id,
                rating=request_data.get('rating'),
                has_comment=bool(request_data.get('comment')),
                response_time=response_time,
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT')
            )
        except Exception as e:
            print(f"Error in AIFeedbackAnalyticsMiddleware: {str(e)}")

        return response 