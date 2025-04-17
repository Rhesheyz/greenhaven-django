from django.core.cache import cache
from django.db.models import Count
from .models import AIAnalytics
from django.utils import timezone
from datetime import timedelta

def ai_analytics_data(request):
    """
    Context processor untuk menyediakan data AI analytics secara global
    """
    # Coba ambil dari cache dulu
    cache_key = 'ai_analytics_dashboard_data'
    cached_data = cache.get(cache_key)
    
    if cached_data:
        return cached_data
    
    try:
        # Statistik dasar
        total_requests = AIAnalytics.objects.count()
        successful_requests = AIAnalytics.objects.filter(success=True).count()
        
        # Statistik 24 jam terakhir
        last_24h = timezone.now() - timedelta(hours=24)
        requests_24h = AIAnalytics.objects.filter(timestamp__gte=last_24h).count()
        
        # Statistik per endpoint
        endpoint_stats = (
            AIAnalytics.objects.values('endpoint')
            .annotate(count=Count('id'))
            .order_by('-count')
        )

        data = {
            'ai_analytics': {
                'total_requests': total_requests,
                'successful_requests': successful_requests,
                'requests_24h': requests_24h,
                'endpoint_stats': {item['endpoint']: item['count'] for item in endpoint_stats},
            }
        }
        
        # Cache data selama 5 menit
        cache.set(cache_key, data, 300)
        
        return data
        
    except Exception:
        # Return default data jika terjadi error
        return {
            'ai_analytics': {
                'total_requests': 0,
                'successful_requests': 0,
                'requests_24h': 0,
                'endpoint_stats': {},
            }
        } 