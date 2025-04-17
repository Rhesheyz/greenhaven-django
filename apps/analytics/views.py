from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Count, Avg, F, ExpressionWrapper, FloatField, Q
from django.db.models.functions import TruncDay
from django.utils import timezone
from datetime import timedelta
from .models import RequestLog
import json

@staff_member_required
def analytics_dashboard_view(request):
    """View untuk menampilkan dashboard analytics"""
    
    # Set rentang waktu (7 hari terakhir)
    end_date = timezone.now()
    start_date = end_date - timedelta(days=7)

    print("\n=== DEBUG ANALYTICS DASHBOARD ===")
    print(f"Time Range: {start_date} to {end_date}")

    # Cek total data di RequestLog
    total_logs = RequestLog.objects.count()
    print(f"\nTotal records in RequestLog: {total_logs}")

    # Ambil beberapa sample data untuk memastikan struktur
    sample_logs = RequestLog.objects.all()[:5]
    print("\nSample RequestLog data:")
    for log in sample_logs:
        print(f"- {log.timestamp}: {log.endpoint} ({log.method})")

    # Statistik harian
    daily_stats = (
        RequestLog.objects.filter(timestamp__gte=start_date)
        .annotate(day=TruncDay('timestamp'))
        .values('day')
        .annotate(
            total_requests=Count('id'),
            avg_response_time=Avg('response_time'),
            error_count=Count('id', filter=Q(is_error=True))
        )
        .order_by('day')
    )

    print("\nDaily Stats Query:")
    print(daily_stats.query)
    
    daily_stats_list = list(daily_stats)
    print("\nDaily Stats Results:")
    print(f"Number of days with data: {len(daily_stats_list)}")
    for stat in daily_stats_list:
        print(f"Day: {stat['day']}, Requests: {stat['total_requests']}, Avg Response Time: {stat['avg_response_time']}")

    # Prepare data untuk charts
    days = [stat['day'].strftime('%Y-%m-%d') for stat in daily_stats_list]
    total_requests_series = [int(stat['total_requests']) for stat in daily_stats_list]
    avg_response_times = [
        round(float(stat['avg_response_time']), 2) if stat['avg_response_time'] 
        else 0 for stat in daily_stats_list
    ]

    print("\nPrepared Chart Data:")
    print(f"Days: {days}")
    print(f"Request Counts: {total_requests_series}")
    print(f"Response Times: {avg_response_times}")

    # Convert ke JSON
    try:
        days_json = json.dumps(days)
        requests_json = json.dumps(total_requests_series)
        response_times_json = json.dumps(avg_response_times)
        
        print("\nJSON Conversion Successful:")
        print(f"Days JSON length: {len(days_json)}")
        print(f"Requests JSON length: {len(requests_json)}")
        print(f"Response Times JSON length: {len(response_times_json)}")
    except Exception as e:
        print(f"\nError converting to JSON: {e}")
        days_json = json.dumps([])
        requests_json = json.dumps([])
        response_times_json = json.dumps([])

    context = {
        'days_json': days_json,
        'requests_json': requests_json,
        'response_times_json': response_times_json,
        'popular_endpoints': daily_stats_list,
        'total_requests_today': RequestLog.objects.filter(
            timestamp__gte=timezone.now().replace(
                hour=0, minute=0, second=0, microsecond=0
            )
        ).count(),
        'avg_response_time': RequestLog.objects.filter(
            timestamp__gte=start_date
        ).aggregate(avg=Avg('response_time'))['avg'] or 0,
        'error_rate': (
            RequestLog.objects.filter(
                timestamp__gte=start_date, 
                is_error=True
            ).count() / 
            max(RequestLog.objects.filter(
                timestamp__gte=start_date
            ).count(), 1) * 100
        ),
        'unique_users': RequestLog.objects.filter(
            timestamp__gte=start_date
        ).values('user_id').distinct().count(),
    }

    print("\nContext Data:")
    print(f"Total Requests Today: {context['total_requests_today']}")
    print(f"Average Response Time: {context['avg_response_time']}")
    print(f"Error Rate: {context['error_rate']}%")
    print(f"Unique Users: {context['unique_users']}")
    print("=== END DEBUG ===\n")

