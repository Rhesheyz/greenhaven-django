from django.db import models
from django.utils import timezone

class RequestLog(models.Model):
    # Request Metrics
    endpoint = models.CharField(max_length=255)
    method = models.CharField(max_length=10)
    status_code = models.IntegerField()
    timestamp = models.DateTimeField(auto_now_add=True)
    response_time = models.FloatField(help_text="Response time in milliseconds")
    ip_address = models.GenericIPAddressField()
    
    # Performance Metrics
    db_query_time = models.FloatField(help_text="Database query time in milliseconds", null=True)
    memory_usage = models.FloatField(help_text="Memory usage in MB", null=True)
    
    # Content Analytics
    content_type = models.CharField(max_length=50, null=True, blank=True)
    content_id = models.CharField(max_length=50, null=True, blank=True)
    
    # User/Client Metrics
    user_agent = models.TextField(null=True, blank=True)
    device_type = models.CharField(max_length=50, null=True, blank=True)
    browser = models.CharField(max_length=50, null=True, blank=True)
    os = models.CharField(max_length=50, null=True, blank=True)
    country = models.CharField(max_length=100, null=True, blank=True)
    city = models.CharField(max_length=100, null=True, blank=True)
    referrer = models.URLField(max_length=500, null=True, blank=True)
    
    # Error Tracking
    error_type = models.CharField(max_length=255, null=True, blank=True)
    error_message = models.TextField(null=True, blank=True)
    error_stack = models.TextField(null=True, blank=True)
    is_error = models.BooleanField(default=False)
    
    # Rate Limiting Metrics (new)
    rate_limit_key = models.CharField(max_length=255, null=True, blank=True, help_text="Key used for rate limiting (IP or API key)")
    rate_limit_count = models.IntegerField(default=0, help_text="Number of requests within time window")
    rate_limit_window = models.DateTimeField(null=True, blank=True, help_text="Start of the rate limit window")
    is_throttled = models.BooleanField(default=False, help_text="Whether request was throttled")
    
    # Security Metrics (new)
    auth_status = models.CharField(max_length=50, null=True, blank=True, help_text="Authentication status (success/failed)")
    user_id = models.IntegerField(null=True, blank=True, help_text="ID of authenticated user")
    api_key = models.CharField(max_length=255, null=True, blank=True, help_text="API key used for request")
    is_suspicious = models.BooleanField(default=False, help_text="Flag for suspicious activity")
    security_flags = models.JSONField(null=True, blank=True, help_text="Additional security flags and details")
    auth_method = models.CharField(max_length=50, null=True, blank=True, help_text="Method of authentication used")
    
    # Business Metrics (new)
    session_id = models.CharField(max_length=100, null=True, blank=True, help_text="Session identifier")
    user_type = models.CharField(max_length=50, null=True, blank=True, help_text="Type of user (guest/registered/premium)")
    feature_accessed = models.CharField(max_length=100, null=True, blank=True, help_text="Specific feature being accessed")
    interaction_type = models.CharField(max_length=50, null=True, blank=True, help_text="Type of interaction (view/search/filter)")
    conversion_goal = models.CharField(max_length=50, null=True, blank=True, help_text="Conversion goal achieved if any")
    engagement_time = models.IntegerField(null=True, blank=True, help_text="Time spent on feature in seconds")

    class Meta:
        indexes = [
            models.Index(fields=['timestamp']),
            models.Index(fields=['endpoint']),
            models.Index(fields=['content_type']),
            models.Index(fields=['country']),
            models.Index(fields=['device_type']),
            models.Index(fields=['is_error']),
            models.Index(fields=['error_type']),
            models.Index(fields=['rate_limit_key']),
            models.Index(fields=['rate_limit_window']),
            models.Index(fields=['is_throttled']),
            models.Index(fields=['auth_status']),
            models.Index(fields=['user_id']),
            models.Index(fields=['is_suspicious']),
            models.Index(fields=['auth_method']),
            models.Index(fields=['session_id']),
            models.Index(fields=['user_type']),
            models.Index(fields=['feature_accessed']),
            models.Index(fields=['conversion_goal']),
        ]

    def __str__(self):
        return f"{self.method} {self.endpoint} - {self.status_code}"

class CustomEvent(models.Model):
    # Event Information
    event_name = models.CharField(max_length=100, help_text="Name of the custom event")
    event_category = models.CharField(max_length=50, help_text="Category of the event")
    event_value = models.JSONField(null=True, blank=True, help_text="Custom event data/payload")
    timestamp = models.DateTimeField(auto_now_add=True)
    
    # User Context
    session_id = models.CharField(max_length=100, null=True, blank=True)
    user_id = models.IntegerField(null=True, blank=True)
    user_type = models.CharField(max_length=50, null=True, blank=True)
    
    # Journey Context
    previous_event = models.CharField(max_length=100, null=True, blank=True, help_text="Previous event in user journey")
    next_event = models.CharField(max_length=100, null=True, blank=True, help_text="Next event in user journey")
    journey_step = models.IntegerField(default=1, help_text="Step number in the user journey")
    
    # Additional Context
    source = models.CharField(max_length=100, null=True, blank=True, help_text="Source of the event")
    metadata = models.JSONField(null=True, blank=True, help_text="Additional event metadata")
    
    class Meta:
        indexes = [
            models.Index(fields=['event_name']),
            models.Index(fields=['event_category']),
            models.Index(fields=['timestamp']),
            models.Index(fields=['session_id']),
            models.Index(fields=['user_id']),
            models.Index(fields=['journey_step']),
        ]
        
    def __str__(self):
        return f"{self.event_name} - {self.timestamp}"

class ComplianceLog(models.Model):
    # Access Information
    timestamp = models.DateTimeField(auto_now_add=True)
    user_id = models.IntegerField(null=True, blank=True)
    ip_address = models.GenericIPAddressField()
    action_type = models.CharField(max_length=50, help_text="Type of action (access/export/delete)")
    
    # Data Access Details
    data_category = models.CharField(max_length=50, help_text="Category of data accessed")
    data_description = models.TextField(help_text="Description of accessed data")
    affected_users = models.JSONField(null=True, blank=True, help_text="List of affected user IDs")
    
    # GDPR Compliance
    legal_basis = models.CharField(max_length=50, help_text="Legal basis for processing")
    consent_reference = models.CharField(max_length=100, null=True, blank=True, help_text="Reference to user consent")
    data_retention = models.DateTimeField(help_text="When this data should be deleted")
    
    # Privacy Impact
    sensitivity_level = models.CharField(
        max_length=20,
        choices=[
            ('low', 'Low Risk'),
            ('medium', 'Medium Risk'),
            ('high', 'High Risk'),
            ('critical', 'Critical')
        ],
        default='low'
    )
    
    # Audit Information
    request_id = models.CharField(max_length=100, help_text="Unique request identifier")
    source_system = models.CharField(max_length=50, help_text="System initiating the request")
    authorized_by = models.CharField(max_length=100, null=True, blank=True, help_text="Person who authorized access")
    purpose = models.TextField(help_text="Purpose of data access")
    
    # Processing Details
    processing_location = models.CharField(max_length=100, help_text="Location where data is processed")
    cross_border = models.BooleanField(default=False, help_text="Whether data crosses borders")
    third_parties = models.JSONField(null=True, blank=True, help_text="Third parties data is shared with")
    
    # Additional Metadata
    metadata = models.JSONField(null=True, blank=True, help_text="Additional compliance metadata")
    notes = models.TextField(null=True, blank=True, help_text="Additional notes")
    
    class Meta:
        indexes = [
            models.Index(fields=['timestamp']),
            models.Index(fields=['action_type']),
            models.Index(fields=['data_category']),
            models.Index(fields=['sensitivity_level']),
            models.Index(fields=['request_id']),
            models.Index(fields=['user_id']),
        ]
        
    def __str__(self):
        return f"{self.action_type} - {self.data_category} ({self.timestamp})"

    def is_expired(self):
        """Check if data retention period has expired"""
        return timezone.now() > self.data_retention

    def get_impact_level(self):
        """Get numeric impact level"""
        impact_levels = {
            'low': 1,
            'medium': 2,
            'high': 3,
            'critical': 4
        }
        return impact_levels.get(self.sensitivity_level, 0)

    def requires_notification(self):
        """Check if this access requires notification"""
        return self.sensitivity_level in ['high', 'critical']

    def get_affected_user_count(self):
        """Get count of affected users"""
        if self.affected_users:
            return len(self.affected_users)
        return 0
