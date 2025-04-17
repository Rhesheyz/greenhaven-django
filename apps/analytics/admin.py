from django.contrib import admin
from .models import RequestLog, CustomEvent,ComplianceLog
from unfold.admin import ModelAdmin
from django.urls import path
from .views import analytics_dashboard_view
from django.utils.html import format_html
from django.db.models import Count, Avg, Q, ExpressionWrapper, FloatField, Max
from django.db.models.functions import Cast

from django.utils import timezone
from datetime import timedelta
from django.shortcuts import render
from django.urls import path
import json
from django.db.models.functions import TruncDay, ExtractHour, TruncDate
from import_export.admin import ImportExportModelAdmin
from unfold.contrib.import_export.forms import ExportForm, ImportForm, SelectableFieldsExportForm

@admin.register(RequestLog)
class RequestLogAdmin(ModelAdmin, ImportExportModelAdmin):
    RATE_LIMIT = 100
    change_list_template = 'admin/analytics/requestlog/change_list.html'
    
    list_display = (
        'timestamp', 'method', 'endpoint', 'status_code', 
        'response_time', 'user_type', 'feature_accessed',
        'interaction_type', 'engagement_status',
        'error_status', 'rate_limit_status', 'security_status'
    )
    
    list_filter = (
        'method', 'status_code', 'content_type', 
        'device_type', 'browser', 'os', 'timestamp',
        'is_error', 'error_type', 'is_throttled',
        'auth_status', 'is_suspicious', 'auth_method',
        'user_type', 'feature_accessed', 
        'interaction_type', 'conversion_goal'
    )
    
    search_fields = (
        'endpoint', 'ip_address', 'content_type', 
        'browser', 'device_type', 'os',
        'error_type', 'error_message',
        'rate_limit_key', 'api_key',
        'security_flags',
        'session_id', 'feature_accessed',
        'conversion_goal'
    )
    
    date_hierarchy = 'timestamp'
    
    fieldsets = (
        ('Request Information', {
            'fields': (
                'endpoint', 'method', 'status_code', 
                'timestamp', 'response_time', 'ip_address'
            )
        }),
        ('Business Metrics', {
            'fields': (
                'session_id', 'user_type', 'feature_accessed',
                'interaction_type', 'conversion_goal', 'engagement_time'
            ),
            'classes': ('collapse',)
        }),
        ('Performance Metrics', {
            'fields': ('db_query_time', 'memory_usage')
        }),
        ('Content Information', {
            'fields': ('content_type', 'content_id')
        }),
        ('Client Information', {
            'fields': (
                'user_agent', 'device_type', 'browser', 
                'os', 'referrer'
            )
        }),
        ('Security Information', {
            'fields': (
                'auth_status', 'user_id', 'api_key', 
                'auth_method', 'is_suspicious', 'security_flags'
            ),
            'classes': ('collapse',)
        }),
        ('Error Information', {
            'fields': (
                'is_error', 'error_type', 'error_message', 
                'error_stack'
            ),
            'classes': ('collapse',)
        }),
        ('Rate Limiting', {
            'fields': (
                'rate_limit_key', 'rate_limit_count',
                'rate_limit_window', 'is_throttled'
            ),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = (
        'endpoint', 'method', 'status_code', 'timestamp', 
        'response_time', 'ip_address', 'db_query_time', 
        'memory_usage', 'content_type', 'content_id',
        'user_agent', 'device_type', 'browser', 'os', 
        'referrer', 'is_error', 'error_type', 'error_message', 
        'error_stack', 'rate_limit_key', 'rate_limit_count',
        'rate_limit_window', 'is_throttled',
        'auth_status', 'user_id', 'api_key', 'auth_method',
        'is_suspicious', 'security_flags',
        'session_id', 'user_type', 'feature_accessed',
        'interaction_type', 'conversion_goal', 'engagement_time'
    )
    
    import_form_class = ImportForm
    export_form_class = ExportForm
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('dashboard/', self.admin_site.admin_view(self.dashboard_view),
                 name='analytics_dashboard'),
        ]
        return custom_urls + urls
    
    def dashboard_view(self, request):
        # Data untuk Chart.js
        data = RequestLog.objects.filter(timestamp__gte=timezone.now()-timedelta(days=7))\
                                  .extra({'day': "DATE(timestamp)"})\
                                  .values('day')\
                                  .annotate(total_requests=Count('id'), avg_response_time=Avg('response_time'))\
                                  .order_by('day')

        context = {
            'days': [entry['day'].strftime('%a') for entry in data],
            'total_requests': [entry['total_requests'] for entry in data],
            'avg_response_time': [entry['avg_response_time'] for entry in data],
        }

    def engagement_status(self, obj):
        if obj.conversion_goal:
            return format_html('<span style="color: green;">🎯 {}</span>', obj.conversion_goal)
        if obj.engagement_time and obj.engagement_time > 10000:  # > 10 seconds
            return format_html('<span style="color: blue;">👥 Engaged</span>')
        return format_html('<span style="color: gray;">👀 Viewed</span>')
    engagement_status.short_description = 'Engagement'

    def error_status(self, obj):
        if obj.is_error:
            return '❌ ' + (obj.error_type or 'Error')
        return '✅ OK'
    error_status.short_description = 'Status'

    def rate_limit_status(self, obj):
        """Custom column to show rate limit status with icon"""
        if obj.is_throttled:
            return '🚫 Throttled'
        return f'✓ {obj.rate_limit_count}/{self.RATE_LIMIT}'
    rate_limit_status.short_description = 'Rate Limit'

    def security_status(self, obj):
        """Custom column to show security status with icon"""
        if obj.is_suspicious:
            return format_html('<span style="color: red;">🚨 Suspicious</span>')
        if obj.auth_status == 'failed':
            return format_html('<span style="color: orange;">⚠️ Auth Failed</span>')
        if obj.auth_status == 'success':
            return format_html('<span style="color: green;">🔒 Authenticated</span>')
        return format_html('<span style="color: gray;">👤 Anonymous</span>')
    security_status.short_description = 'Security'

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def changelist_view(self, request, extra_context=None):
        end_date = timezone.now()
        start_date = end_date - timedelta(days=7)
        
        # Calculate error rate
        total_requests = RequestLog.objects.filter(timestamp__gte=start_date).count()
        error_requests = RequestLog.objects.filter(
            timestamp__gte=start_date,
            is_error=True
        ).count()
        
        error_rate = (error_requests / total_requests * 100) if total_requests > 0 else 0

        # Statistik dasar
        daily_stats = (
            RequestLog.objects.filter(timestamp__gte=start_date)
            .annotate(day=TruncDay('timestamp'))
            .values('day')
            .annotate(
                total_requests=Count('id'),
                avg_response_time=Avg('response_time'),
                error_count=Count('id', filter=Q(is_error=True)),
                success_rate=ExpressionWrapper(
                    (1 - Cast(Count('id', filter=Q(is_error=True)), FloatField()) / Cast(Count('id'), FloatField())) * 100,
                    output_field=FloatField()
                )
            )
            .order_by('day')
        )

        # Top Endpoints
        top_endpoints = (
            RequestLog.objects.filter(timestamp__gte=start_date)
            .values('endpoint')
            .annotate(
                count=Count('id'),
                avg_response_time=Avg('response_time'),
                error_rate=ExpressionWrapper(
                    Cast(Count('id', filter=Q(is_error=True)), FloatField()) / Cast(Count('id'), FloatField()) * 100,
                    output_field=FloatField()
                )
            )
            .order_by('-count')[:10]
        )

        # Browser & Device Stats
        browser_stats = (
            RequestLog.objects.filter(timestamp__gte=start_date)
            .values('browser')
            .annotate(count=Count('id'))
            .order_by('-count')
        )
        
        device_stats = (
            RequestLog.objects.filter(timestamp__gte=start_date)
            .values('device_type')
            .annotate(count=Count('id'))
            .order_by('-count')
        )

        # Performance Metrics
        performance_stats = {
            'avg_db_time': RequestLog.objects.filter(
                timestamp__gte=start_date
            ).aggregate(avg=Avg('db_query_time'))['avg'] or 0,
            'avg_memory': RequestLog.objects.filter(
                timestamp__gte=start_date
            ).aggregate(avg=Avg('memory_usage'))['avg'] or 0,
            'peak_response_time': RequestLog.objects.filter(
                timestamp__gte=start_date
            ).aggregate(max=Max('response_time'))['max'] or 0
        }

        # Security Metrics
        security_stats = {
            'suspicious_requests': RequestLog.objects.filter(
                timestamp__gte=start_date,
                is_suspicious=True
            ).count(),
            'auth_failures': RequestLog.objects.filter(
                timestamp__gte=start_date,
                auth_status='failed'
            ).count(),
            'throttled_requests': RequestLog.objects.filter(
                timestamp__gte=start_date,
                is_throttled=True
            ).count()
        }

        # User Engagement
        user_engagement = {
            'avg_session_duration': RequestLog.objects.filter(
                timestamp__gte=start_date
            ).aggregate(avg=Avg('engagement_time'))['avg'] or 0,
            'conversion_rate': (
                RequestLog.objects.filter(
                    timestamp__gte=start_date,
                    conversion_goal__isnull=False
                ).count() /
                max(RequestLog.objects.filter(
                    timestamp__gte=start_date
                ).count(), 1) * 100
            )
        }

        # Prepare data untuk charts
        days = [stat['day'].strftime('%Y-%m-%d') for stat in daily_stats]
        total_requests_series = [int(stat['total_requests']) for stat in daily_stats]
        avg_response_times = [
            round(float(stat['avg_response_time']), 2) if stat['avg_response_time'] 
            else 0 for stat in daily_stats
        ]

        # HTTP Methods distribution
        method_stats = (
            RequestLog.objects.filter(timestamp__gte=start_date)
            .values('method')
            .annotate(count=Count('id'))
            .order_by('-count')
        )
        method_stats_dict = {
            stat['method']: stat['count'] 
            for stat in method_stats
        }

        # Status codes distribution
        status_code_stats = (
            RequestLog.objects.filter(timestamp__gte=start_date)
            .values('status_code')
            .annotate(count=Count('id'))
            .order_by('-count')
        )
        status_code_stats_dict = {
            str(stat['status_code']): stat['count'] 
            for stat in status_code_stats
        }

        # Convert ke JSON
        extra_context = extra_context or {}
        extra_context.update({
            'days_json': json.dumps(days),
            'requests_json': json.dumps(total_requests_series),
            'response_times_json': json.dumps(avg_response_times),
            'method_stats_json': json.dumps(method_stats_dict),
            'status_code_stats_json': json.dumps(status_code_stats_dict),
            'browser_stats_json': json.dumps({
                stat['browser']: stat['count'] for stat in browser_stats
            }),
            'device_stats_json': json.dumps({
                stat['device_type']: stat['count'] for stat in device_stats
            }),
            'top_endpoints': top_endpoints,
            'performance_stats': performance_stats,
            'security_stats': security_stats,
            'user_engagement': user_engagement,
            'total_requests_7days': sum(total_requests_series),
            'error_rate': error_rate,
            'success_rate': round(100 - error_rate, 1),
            'peak_traffic_hour': self.get_peak_traffic_hour(start_date),
        })

        return super().changelist_view(request, extra_context=extra_context)

    def get_peak_traffic_hour(self, start_date):
        hourly_stats = (
            RequestLog.objects.filter(timestamp__gte=start_date)
            .annotate(hour=ExtractHour('timestamp'))
            .values('hour')
            .annotate(count=Count('id'))
            .order_by('-count')
            .first()
        )
        return hourly_stats['hour'] if hourly_stats else 0

@admin.register(CustomEvent)
class CustomEventAdmin(ModelAdmin, ImportExportModelAdmin):
    change_list_template = 'admin/analytics/customevent/change_list.html'
    import_form_class = ImportForm
    export_form_class = ExportForm
    
    list_display = (
        'timestamp', 'event_name', 'event_category', 
        'user_type', 'journey_step', 'event_status'
    )
    
    list_filter = (
        'event_category', 'user_type', 
        'source', 'timestamp',
        'journey_step'
    )
    
    search_fields = (
        'event_name', 'session_id', 
        'user_id', 'source',
        'previous_event', 'next_event'
    )
    
    date_hierarchy = 'timestamp'
    
    fieldsets = (
        ('Event Information', {
            'fields': (
                'event_name', 'event_category', 
                'event_value', 'timestamp'
            )
        }),
        ('User Context', {
            'fields': (
                'session_id', 'user_id', 
                'user_type'
            )
        }),
        ('Journey Context', {
            'fields': (
                'previous_event', 'next_event',
                'journey_step'
            ),
            'classes': ('collapse',)
        }),
        ('Additional Context', {
            'fields': (
                'source', 'metadata'
            ),
            'classes': ('collapse',)
        })
    )
    
    readonly_fields = (
        'event_name', 'event_category', 
        'event_value', 'timestamp',
        'session_id', 'user_id', 
        'user_type', 'previous_event',
        'next_event', 'journey_step',
        'source', 'metadata'
    )

    def event_status(self, obj):
        """Custom column to show event status with icon"""
        category_icons = {
            'page_view': '👁️',
            'feature_usage': '⚡',
            'user_action': '👤',
            'system_event': '🔧',
            'business_event': '💼'
        }
        icon = category_icons.get(obj.event_category, '📝')
        return format_html(
            '<span title="{}">{} {}</span>',
            obj.event_category,
            icon,
            obj.event_name
        )
    event_status.short_description = 'Event'

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def changelist_view(self, request, extra_context=None):
        # Get data untuk charts
        response = super().changelist_view(request, extra_context=extra_context)
        
        try:
            qs = self.get_queryset(request)
            
            # Event activity over time (last 30 days)
            thirty_days_ago = timezone.now() - timedelta(days=30)
            daily_events = (
                qs.filter(timestamp__gte=thirty_days_ago)
                .annotate(date=TruncDate('timestamp'))
                .values('date')
                .annotate(count=Count('id'))
                .order_by('date')
            )

            # Event categories distribution
            category_stats = (
                qs.values('event_category')
                .annotate(count=Count('id'))
                .order_by('-count')
            )

            # Event names distribution (top 10)
            event_stats = (
                qs.values('event_name')
                .annotate(count=Count('id'))
                .order_by('-count')[:10]
            )

            # User type distribution
            user_type_stats = (
                qs.values('user_type')
                .annotate(count=Count('id'))
                .order_by('-count')
            )

            # Prepare data for charts
            extra_context = {
                'daily_events_json': {
                    'labels': [str(entry['date']) for entry in daily_events],
                    'data': [entry['count'] for entry in daily_events]
                },
                'category_stats_json': {
                    'labels': [entry['event_category'] for entry in category_stats],
                    'data': [entry['count'] for entry in category_stats]
                },
                'event_stats_json': {
                    'labels': [entry['event_name'] for entry in event_stats],
                    'data': [entry['count'] for entry in event_stats]
                },
                'user_type_stats_json': {
                    'labels': [entry['user_type'] for entry in user_type_stats],
                    'data': [entry['count'] for entry in user_type_stats]
                }
            }
            
            response.context_data.update(extra_context)
        except:
            pass

        return response

@admin.register(ComplianceLog)
class ComplianceLogAdmin(ModelAdmin, ImportExportModelAdmin):
    import_form_class = ImportForm
    export_form_class = ExportForm
    
    change_list_template = 'admin/analytics/compliancelog/change_list.html'
    
    list_display = (
        'timestamp', 'action_type', 'data_category',
        'sensitivity_badge', 'compliance_status',
        'user_id', 'request_id', 'retention_status'
    )
    
    list_filter = (
        'action_type',
        'data_category',
        'sensitivity_level',
        'legal_basis',
        'cross_border',
        'timestamp',
    )
    
    search_fields = (
        'request_id',
        'user_id',
        'ip_address',
        'data_description',
        'purpose',
        'authorized_by',
    )
    
    date_hierarchy = 'timestamp'
    
    fieldsets = (
        ('Access Information', {
            'fields': (
                'timestamp', 'user_id', 'ip_address',
                'action_type', 'request_id'
            )
        }),
        ('Data Details', {
            'fields': (
                'data_category', 'data_description',
                'affected_users', 'sensitivity_level'
            )
        }),
        ('GDPR Compliance', {
            'fields': (
                'legal_basis', 'consent_reference',
                'data_retention', 'purpose'
            ),
            'classes': ('collapse',)
        }),
        ('Processing Details', {
            'fields': (
                'processing_location', 'cross_border',
                'third_parties', 'source_system',
                'authorized_by'
            ),
            'classes': ('collapse',)
        }),
        ('Additional Information', {
            'fields': (
                'metadata', 'notes'
            ),
            'classes': ('collapse',)
        })
    )
    
    readonly_fields = (
        'timestamp', 'request_id', 'user_id',
        'ip_address', 'action_type', 'data_category',
        'data_description', 'affected_users',
        'legal_basis', 'consent_reference',
        'data_retention', 'sensitivity_level',
        'source_system', 'authorized_by', 'purpose',
        'processing_location', 'cross_border',
        'third_parties', 'metadata', 'notes'
    )

    def sensitivity_badge(self, obj):
        """Custom column to show sensitivity level with color"""
        colors = {
            'low': 'green',
            'medium': 'orange',
            'high': 'red',
            'critical': 'purple'
        }
        return format_html(
            '<span style="color: {};">⬤</span> {}',
            colors.get(obj.sensitivity_level, 'gray'),
            obj.sensitivity_level.upper()
        )
    sensitivity_badge.short_description = 'Sensitivity'

    def compliance_status(self, obj):
        """Custom column to show compliance status"""
        if obj.cross_border:
            return format_html(
                '<span style="color: orange;">🌍 Cross-Border</span>'
            )
        if obj.sensitivity_level in ['high', 'critical']:
            return format_html(
                '<span style="color: red;">⚠️ High Risk</span>'
            )
        return format_html(
            '<span style="color: green;">✓ Compliant</span>'
        )
    compliance_status.short_description = 'Status'

    def retention_status(self, obj):
        """Custom column to show data retention status"""
        if obj.is_expired():
            return format_html(
                '<span style="color: red;">❌ Expired</span>'
            )
        days_left = (obj.data_retention - timezone.now()).days
        if days_left < 30:
            return format_html(
                '<span style="color: orange;">⚠️ {} days left</span>',
                days_left
            )
        return format_html(
            '<span style="color: green;">✓ {} days left</span>',
            days_left
        )
    retention_status.short_description = 'Retention'

    def changelist_view(self, request, extra_context=None):
        # Get data untuk charts
        end_date = timezone.now()
        start_date = end_date - timedelta(days=30)
        
        # Access type distribution
        access_stats = (
            ComplianceLog.objects.filter(timestamp__gte=start_date)
            .values('action_type')
            .annotate(count=Count('id'))
            .order_by('-count')
        )
        
        # Sensitivity level distribution dengan filter untuk high dan critical
        high_risk_count = (
            ComplianceLog.objects
            .filter(
                timestamp__gte=start_date,
                sensitivity_level__in=['high', 'critical']
            )
            .count()
        )
        
        # Sensitivity level distribution
        sensitivity_stats = (
            ComplianceLog.objects.filter(timestamp__gte=start_date)
            .values('sensitivity_level')
            .annotate(count=Count('id'))
            .order_by('sensitivity_level')
        )
        
        # Daily activity
        daily_activity = (
            ComplianceLog.objects.filter(timestamp__gte=start_date)
            .annotate(date=TruncDate('timestamp'))
            .values('date')
            .annotate(count=Count('id'))
            .order_by('date')
        )

        # Data categories distribution
        data_categories = (
            ComplianceLog.objects.filter(timestamp__gte=start_date)
            .values('data_category')
            .annotate(count=Count('id'))
            .order_by('-count')
        )
        
        # Prepare data for JSON
        access_stats_json = {
            'labels': [stat['action_type'] for stat in access_stats],
            'data': [stat['count'] for stat in access_stats]
        }
        
        sensitivity_stats_json = {
            'labels': [stat['sensitivity_level'] for stat in sensitivity_stats],
            'data': [stat['count'] for stat in sensitivity_stats]
        }
        
        daily_activity_json = {
            'labels': [activity['date'].strftime('%Y-%m-%d') for activity in daily_activity],
            'data': [activity['count'] for activity in daily_activity]
        }
        
        data_categories_json = {
            'labels': [cat['data_category'] for cat in data_categories],
            'data': [cat['count'] for cat in data_categories]
        }
        
        extra_context = extra_context or {}
        extra_context.update({
            'access_stats_json': access_stats_json,
            'sensitivity_stats_json': sensitivity_stats_json,
            'daily_activity_json': daily_activity_json,
            'data_categories_json': data_categories_json,
            'high_risk_count': high_risk_count,
            'cross_border_count': ComplianceLog.objects.filter(
                timestamp__gte=start_date,
                cross_border=True
            ).count(),
            'expired_count': ComplianceLog.objects.filter(
                data_retention__lt=timezone.now()
            ).count()
        })
        
        return super().changelist_view(request, extra_context=extra_context)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    
