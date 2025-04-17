from django.db import models

class Intents(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()

    def __str__(self):
        return self.name

class Responses(models.Model):
    intent = models.ForeignKey(Intents, on_delete=models.CASCADE, related_name='responses')
    response = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Response for {self.intent.name}"

class InteractionLogs(models.Model):
    user_input = models.TextField()
    intent = models.ForeignKey(Intents, on_delete=models.CASCADE, related_name='logs')
    response = models.ForeignKey(Responses, on_delete=models.CASCADE, related_name='logs')
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Log {self.id} - {self.intent.name}"

class ChatFeedback(models.Model):
    session_id = models.CharField(max_length=255)
    user_message = models.TextField()
    ai_response = models.TextField()
    rating = models.IntegerField(choices=[
        (1, '👎 Tidak Membantu'),
        (2, '👍 Membantu')
    ])
    comment = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Feedback for session {self.session_id}"

class AIAnalytics(models.Model):
    session_id = models.CharField(max_length=255, null=True, blank=True)
    endpoint = models.CharField(max_length=100)
    timestamp = models.DateTimeField(auto_now_add=True)
    response_time = models.FloatField(help_text='Response time in seconds')
    success = models.BooleanField(default=True)
    error_message = models.TextField(null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)
    request_data = models.JSONField(null=True, blank=True)
    
    class Meta:
        verbose_name = 'AI Analytics'
        verbose_name_plural = 'AI Analytics'
        ordering = ['-timestamp']

    def __str__(self):
        return f"AI Usage - {self.session_id or 'Anonymous'} at {self.timestamp}"

class AIFeedbackAnalytics(models.Model):
    session_id = models.CharField(max_length=255, null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    rating = models.IntegerField(choices=[
        (1, '👎 Tidak Membantu'),
        (2, '👍 Membantu')
    ])
    has_comment = models.BooleanField(default=False)  # Track if user left a comment
    response_time = models.FloatField(help_text='Response time in seconds')
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)
    
    class Meta:
        verbose_name = 'AI Feedback Analytics'
        verbose_name_plural = 'AI Feedback Analytics'
        ordering = ['-timestamp']

    def __str__(self):
        return f"Feedback Analytics - {self.session_id or 'Anonymous'} at {self.timestamp}"
