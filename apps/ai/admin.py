from django.contrib import admin
from .models import Intents, Responses, InteractionLogs, ChatFeedback, AIAnalytics, AIFeedbackAnalytics
from unfold.admin import ModelAdmin
from import_export.admin import ImportExportModelAdmin
from unfold.contrib.import_export.forms import ExportForm, ImportForm
from django.db.models import Avg, Count
from django.db.models.functions import TruncDate
from django.utils import timezone
from datetime import timedelta
from django.db import models
from django.db.models import Q

@admin.register(ChatFeedback)
class ChatFeedbackAdmin(ModelAdmin):
    list_display = ('session_id', 'truncated_message', 'truncated_response', 'rating', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('session_id', 'user_message', 'ai_response', 'comment')
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)

    def truncated_message(self, obj):
        """Truncate user message for display"""
        return (obj.user_message[:75] + '...') if len(obj.user_message) > 75 else obj.user_message
    truncated_message.short_description = 'User Message'

    def truncated_response(self, obj):
        """Truncate AI response for display"""
        return (obj.ai_response[:75] + '...') if len(obj.ai_response) > 75 else obj.ai_response
    truncated_response.short_description = 'AI Response'

    fieldsets = (
        ('Session Information', {
            'fields': ('session_id', 'created_at')
        }),
        ('Interaction Details', {
            'fields': ('user_message', 'ai_response')
        }),
        ('Feedback', {
            'fields': ('rating', 'comment')
        }),
    )

    def has_add_permission(self, request):
        """Disable manual addition of feedback"""
        return False

    def has_change_permission(self, request, obj=None):
        """Make feedback read-only"""
        return False

@admin.register(Intents)
class IntentsAdmin(ModelAdmin, ImportExportModelAdmin):
    import_form_class = ImportForm
    export_form_class = ExportForm
    list_display = ('name', 'description')
    search_fields = ('name',)

@admin.register(Responses)
class ResponsesAdmin(ModelAdmin, ImportExportModelAdmin):
    import_form_class = ImportForm
    export_form_class = ExportForm
    list_display = ('intent', 'response', 'created_at')
    list_filter = ('intent',)
    search_fields = ('response',)

@admin.register(InteractionLogs)
class InteractionLogsAdmin(ModelAdmin, ImportExportModelAdmin):
    import_form_class = ImportForm
    export_form_class = ExportForm
    list_display = ('user_input', 'intent', 'response', 'timestamp')
    list_filter = ('intent', 'timestamp')
    search_fields = ('user_input',)

@admin.register(AIAnalytics)
class AIAnalyticsAdmin(ModelAdmin, ImportExportModelAdmin):
    change_list_template = 'admin/analytics/aianalytics/change_list.html'
    
    list_display = ('session_id', 'endpoint', 'response_time', 'success', 'timestamp')
    list_filter = ('endpoint', 'success', 'timestamp')
    search_fields = ('session_id', 'ip_address')
    
    import_form_class = ImportForm
    export_form_class = ExportForm
    
    def changelist_view(self, request, extra_context=None):
        # Get analytics for last 30 days
        thirty_days_ago = timezone.now() - timedelta(days=30)
        
        # Calculate summary stats
        analytics_qs = AIAnalytics.objects.filter(timestamp__gte=thirty_days_ago)
        total_requests = analytics_qs.count()
        
        # Calculate success rate
        if total_requests > 0:
            success_count = analytics_qs.filter(success=True).count()
            avg_success_rate = (success_count / total_requests) * 100
        else:
            avg_success_rate = 0
            
        # Calculate average response time
        avg_response_time = analytics_qs.aggregate(
            avg_time=Avg('response_time')
        )['avg_time'] or 0
        
        # Daily stats for charts
        daily_stats = (
            analytics_qs
            .annotate(date=TruncDate('timestamp'))
            .values('date')
            .annotate(
                total_requests=Count('id'),
                success_rate=Count('id', filter=Q(success=True)) * 100.0 / Count('id'),
                avg_response_time=Avg('response_time')
            )
            .order_by('date')
        )

        # Endpoint stats for charts
        endpoint_stats = (
            analytics_qs
            .values('endpoint')
            .annotate(
                total_requests=Count('id'),
                success_rate=Count('id', filter=Q(success=True)) * 100.0 / Count('id')
            )
            .order_by('-total_requests')
        )

        extra_context = extra_context or {}
        extra_context.update({
            'total_requests': total_requests,
            'avg_success_rate': avg_success_rate,
            'avg_response_time': avg_response_time,
            'daily_stats': daily_stats,
            'endpoint_stats': endpoint_stats,
        })
        
        return super().changelist_view(request, extra_context=extra_context)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

@admin.register(AIFeedbackAnalytics)
class AIFeedbackAnalyticsAdmin(ModelAdmin, ImportExportModelAdmin):
    change_list_template = 'admin/analytics/aifeedbackanalytics/change_list.html'
    
    list_display = ('session_id', 'rating_display', 'has_comment', 'response_time', 'timestamp')
    list_filter = ('rating', 'has_comment', 'timestamp')
    search_fields = ('session_id', 'ip_address')
    readonly_fields = ('timestamp', 'response_time')
    
    import_form_class = ImportForm
    export_form_class = ExportForm
    
    def rating_display(self, obj):
        return '👍' if obj.rating == 2 else '👎'
    rating_display.short_description = 'Rating'

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def changelist_view(self, request, extra_context=None):
        # Get analytics for last 30 days
        thirty_days_ago = timezone.now() - timedelta(days=30)
        
        # Daily feedback stats
        daily_stats = (
            AIFeedbackAnalytics.objects
            .filter(timestamp__gte=thirty_days_ago)
            .annotate(date=TruncDate('timestamp'))
            .values('date')
            .annotate(
                total_feedback=Count('id'),
                positive_feedback=Count('id', filter=models.Q(rating=2)),
                with_comments=Count('id', filter=models.Q(has_comment=True))
            )
            .order_by('date')
        )

        # Overall stats
        total_feedback = AIFeedbackAnalytics.objects.count()
        
        # Calculate rates
        if total_feedback > 0:
            positive_rate = round((AIFeedbackAnalytics.objects.filter(rating=2).count() * 100.0 / total_feedback), 2)
            negative_rate = round(100 - positive_rate, 2)
            comment_rate = round((AIFeedbackAnalytics.objects.filter(has_comment=True).count() * 100.0 / total_feedback), 2)
            no_comment_rate = round(100 - comment_rate, 2)
        else:
            positive_rate = negative_rate = comment_rate = no_comment_rate = 0

        extra_context = extra_context or {}
        extra_context.update({
            'daily_stats': daily_stats,
            'total_feedback': total_feedback,
            'positive_rate': positive_rate,
            'negative_rate': negative_rate,
            'comment_rate': comment_rate,
            'no_comment_rate': no_comment_rate
        })
        
        return super().changelist_view(request, extra_context=extra_context)

