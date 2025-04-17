from apps.destinations.models import Destinations
from apps.flora.models import Flora
from apps.fauna.models import Fauna
from apps.health.models import Health
from apps.kuliner.models import Kuliner
from django.core.cache import cache

def admin_stats(request):
    """
    Context processor untuk menyediakan statistik admin secara global
    """
    # Cek path untuk admin termasuk prefix bahasa
    if not any(lang in request.path for lang in ['/admin/', '/en/admin/', '/id/admin/']):
        return {}
    
    # Coba ambil dari cache dulu
    cache_key = 'admin_dashboard_stats'
    cached_data = cache.get(cache_key)
    
    if cached_data:
        return cached_data
        
    try:
        stats = {
            'total_destinations': Destinations.objects.count(),
            'total_flora': Flora.objects.count(),
            'total_fauna': Fauna.objects.count(),
            'total_health': Health.objects.count(),
            'total_kuliner': Kuliner.objects.count(),
        }
        
        # Simpan ke cache selama 5 menit
        cache.set(cache_key, stats, 300)
        
        return stats
        
    except Exception:
        return {
            'total_destinations': 0,
            'total_flora': 0,
            'total_fauna': 0,
            'total_health': 0,
            'total_kuliner': 0,
        } 