from apps.analytics.models import RequestLog
from django.db.models import Count, Avg
from django.utils import timezone
from django.core.cache import cache
from datetime import timedelta

def analytics_data(request):
    """
    Context processor untuk menyediakan data analytics secara global
    """
    # Coba ambil dari cache dulu
    cache_key = 'analytics_dashboard_data'
    cached_data = cache.get(cache_key)
    
    if cached_data:
        return cached_data
    
    # Ambil data 30 hari terakhir
    thirty_days_ago = timezone.now() - timedelta(days=30)
    
    # Statistik dasar
    stats = {
        'total_requests': RequestLog.objects.count(),
        'unique_visitors': RequestLog.objects.values('ip_address').distinct().count(),
        'total_errors': RequestLog.objects.filter(is_error=True).count(),
    }
    
    # Statistik per fitur
    feature_stats = (
        RequestLog.objects.filter(timestamp__gte=thirty_days_ago)
        .values('feature_accessed')
        .annotate(count=Count('id'))
        .exclude(feature_accessed__isnull=True)
    )
    
    # Konversi stats
    conversion_stats = (
        RequestLog.objects.filter(
            timestamp__gte=thirty_days_ago,
            conversion_goal__isnull=False
        )
        .values('conversion_goal')
        .annotate(count=Count('id'))
    )
    
    # Browser stats
    browser_stats = (
        RequestLog.objects.filter(timestamp__gte=thirty_days_ago)
        .values('browser')
        .annotate(count=Count('id'))
        .order_by('-count')[:5]
    )
    
    # Response time average
    avg_response_time = RequestLog.objects.filter(
        timestamp__gte=thirty_days_ago
    ).aggregate(avg_time=Avg('response_time'))['avg_time']

    # Prepare data untuk template
    data = {
        'analytics_stats': stats,
        'feature_stats': {item['feature_accessed']: item['count'] for item in feature_stats},
        'conversion_stats': {item['conversion_goal']: item['count'] for item in conversion_stats},
        'browser_stats': {item['browser']: item['count'] for item in browser_stats},
        'avg_response_time': avg_response_time,
    }
    
    # Simpan ke cache selama 5 menit
    cache.set(cache_key, data, 300)
    
    return data 




