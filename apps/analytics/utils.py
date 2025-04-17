from .models import CustomEvent, ComplianceLog
from django.core.cache import cache
from django.utils import timezone
import uuid
from datetime import timedelta
import json
from django.core.exceptions import ValidationError
from django.conf import settings

class EventTracker:
    """Utility class untuk tracking custom events"""
    
    @staticmethod
    def track(event_name, category, user=None, session_id=None, value=None, source=None, metadata=None):
        """
        Track a custom event
        
        Args:
            event_name (str): Nama event
            category (str): Kategori event
            user (User, optional): User object
            session_id (str, optional): Session ID
            value (dict, optional): Custom event data
            source (str, optional): Source of the event
            metadata (dict, optional): Additional metadata
        """
        # Get user info if available
        user_id = user.id if user and user.is_authenticated else None
        user_type = 'registered' if user and user.is_authenticated else 'guest'
        
        # Get journey context from cache
        journey_key = f"journey:{session_id}" if session_id else None
        previous_event = None
        journey_step = 1
        
        if journey_key:
            journey_data = cache.get(journey_key, {})
            previous_event = journey_data.get('last_event')
            journey_step = journey_data.get('step', 0) + 1
            
            # Update journey in cache
            cache.set(journey_key, {
                'last_event': event_name,
                'step': journey_step,
                'timestamp': timezone.now().isoformat()
            }, timeout=3600)  # 1 hour timeout
        
        # Create event
        event = CustomEvent.objects.create(
            event_name=event_name,
            event_category=category,
            event_value=value,
            session_id=session_id,
            user_id=user_id,
            user_type=user_type,
            previous_event=previous_event,
            journey_step=journey_step,
            source=source,
            metadata=metadata
        )
        
        return event

    @staticmethod
    def track_journey(events, user=None, session_id=None):
        """
        Track multiple events as part of a journey
        
        Args:
            events (list): List of event dictionaries
            user (User, optional): User object
            session_id (str, optional): Session ID
        """
        tracked_events = []
        for event_data in events:
            event = EventTracker.track(
                event_name=event_data['name'],
                category=event_data['category'],
                user=user,
                session_id=session_id,
                value=event_data.get('value'),
                source=event_data.get('source'),
                metadata=event_data.get('metadata')
            )
            tracked_events.append(event)
        return tracked_events

    @staticmethod
    def get_user_journey(session_id):
        """
        Get all events for a specific session
        
        Args:
            session_id (str): Session ID
        """
        return CustomEvent.objects.filter(
            session_id=session_id
        ).order_by('timestamp')

# Example event categories
class EventCategories:
    PAGE_VIEW = 'page_view'
    FEATURE_USAGE = 'feature_usage'
    USER_ACTION = 'user_action'
    SYSTEM_EVENT = 'system_event'
    BUSINESS_EVENT = 'business_event'

# Example event names
class EventNames:
    # Page Views
    VIEW_HOME = 'view_home'
    VIEW_PROFILE = 'view_profile'
    VIEW_SETTINGS = 'view_settings'
    
    # Feature Usage
    SEARCH = 'search'
    FILTER = 'filter'
    SORT = 'sort'
    
    # User Actions
    LOGIN = 'login'
    SIGNUP = 'signup'
    UPDATE_PROFILE = 'update_profile'
    
    # Business Events
    CONTENT_CREATE = 'content_create'
    CONTENT_SHARE = 'content_share'
    CONTENT_DOWNLOAD = 'content_download'

class ComplianceTracker:
    """Utility class untuk tracking compliance dan privacy"""
    
    # Data retention periods (in days)
    RETENTION_PERIODS = {
        'personal': 365,  # 1 year
        'sensitive': 180,  # 6 months
        'financial': 730,  # 2 years
        'analytics': 90,   # 3 months
        'logs': 30,       # 1 month
    }

    # Legal bases for processing
    LEGAL_BASES = {
        'consent': 'Explicit user consent',
        'contract': 'Contractual necessity',
        'legal_obligation': 'Legal obligation',
        'vital_interests': 'Vital interests',
        'public_task': 'Public interest task',
        'legitimate_interests': 'Legitimate interests'
    }

    @staticmethod
    def log_access(
        user_id, 
        ip_address, 
        data_category, 
        data_description, 
        purpose,
        action_type='access',
        affected_users=None,
        legal_basis='consent',
        sensitivity_level='low',
        source_system=None,
        authorized_by=None,
        location=None,
        third_parties=None,
        metadata=None
    ):
        """
        Log a data access event for compliance tracking
        
        Args:
            user_id: ID of user accessing data
            ip_address: IP address of request
            data_category: Category of accessed data
            data_description: Description of accessed data
            purpose: Purpose of access
            action_type: Type of access (access/export/delete)
            affected_users: List of affected user IDs
            legal_basis: Legal basis for processing
            sensitivity_level: Risk level of access
            source_system: System initiating request
            authorized_by: Person authorizing access
            location: Processing location
            third_parties: Third parties data shared with
            metadata: Additional metadata
        """
        # Validate inputs
        if legal_basis not in ComplianceTracker.LEGAL_BASES:
            raise ValidationError(f"Invalid legal basis: {legal_basis}")
            
        # Generate request ID
        request_id = str(uuid.uuid4())
        
        # Calculate retention period
        retention_days = ComplianceTracker.RETENTION_PERIODS.get(
            data_category, 
            365  # default 1 year
        )
        data_retention = timezone.now() + timedelta(days=retention_days)
        
        # Determine if cross-border
        processing_location = location or getattr(settings, 'DATA_PROCESSING_LOCATION', 'local')
        cross_border = processing_location != 'local'
        
        # Create compliance log
        log = ComplianceLog.objects.create(
            timestamp=timezone.now(),
            user_id=user_id,
            ip_address=ip_address,
            action_type=action_type,
            data_category=data_category,
            data_description=data_description,
            affected_users=affected_users,
            legal_basis=legal_basis,
            consent_reference=f"consent_{user_id}_{timezone.now().strftime('%Y%m%d')}",
            data_retention=data_retention,
            sensitivity_level=sensitivity_level,
            request_id=request_id,
            source_system=source_system or 'web',
            authorized_by=authorized_by,
            purpose=purpose,
            processing_location=processing_location,
            cross_border=cross_border,
            third_parties=third_parties,
            metadata=metadata
        )
        
        # Handle high-risk access
        if log.requires_notification():
            ComplianceTracker.notify_data_access(log)
        
        return log

    @staticmethod
    def notify_data_access(log):
        """
        Send notifications for high-risk data access
        """
        # TODO: Implement notification system
        # This could send emails, Slack messages, etc.
        pass

    @staticmethod
    def get_expired_data():
        """
        Get all data that has exceeded retention period
        """
        return ComplianceLog.objects.filter(
            data_retention__lt=timezone.now()
        )

    @staticmethod
    def generate_privacy_report(start_date=None, end_date=None):
        """
        Generate privacy compliance report
        """
        if not start_date:
            start_date = timezone.now() - timedelta(days=30)
        if not end_date:
            end_date = timezone.now()

        logs = ComplianceLog.objects.filter(
            timestamp__range=(start_date, end_date)
        )

        report = {
            'total_accesses': logs.count(),
            'by_category': {},
            'by_sensitivity': {},
            'cross_border_transfers': logs.filter(cross_border=True).count(),
            'high_risk_accesses': logs.filter(
                sensitivity_level__in=['high', 'critical']
            ).count(),
            'retention_violations': ComplianceTracker.get_expired_data().count(),
            'period': {
                'start': start_date,
                'end': end_date
            }
        }

        # Aggregate by category
        for category in logs.values_list('data_category', flat=True).distinct():
            report['by_category'][category] = logs.filter(
                data_category=category
            ).count()

        # Aggregate by sensitivity
        for level in ['low', 'medium', 'high', 'critical']:
            report['by_sensitivity'][level] = logs.filter(
                sensitivity_level=level
            ).count()

        return report
