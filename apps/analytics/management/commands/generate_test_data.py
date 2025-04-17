from django.core.management.base import BaseCommand
from analytics.models import RequestLog
from django.utils import timezone
import random
from datetime import timedelta

class Command(BaseCommand):
    help = 'Generates test data for RequestLog'

    def handle(self, *args, **kwargs):
        endpoints = [
            '/api/users/',
            '/api/products/',
            '/api/orders/',
            '/api/categories/',
            '/api/auth/login/',
        ]
        
        methods = ['GET', 'POST', 'PUT', 'DELETE']
        devices = ['Desktop', 'Mobile', 'Tablet']
        browsers = ['Chrome', 'Firefox', 'Safari']
        os_list = ['Windows', 'MacOS', 'iOS', 'Android']
        
        # Generate data for last 7 days
        for i in range(7):
            date = timezone.now() - timedelta(days=i)
            # Generate 50-100 requests per day
            for _ in range(random.randint(50, 100)):
                RequestLog.objects.create(
                    endpoint=random.choice(endpoints),
                    method=random.choice(methods),
                    status_code=random.choice([200, 201, 400, 401, 403, 404, 500]),
                    response_time=random.uniform(100, 1000),
                    ip_address=f"192.168.1.{random.randint(1, 255)}",
                    device_type=random.choice(devices),
                    browser=random.choice(browsers),
                    os=random.choice(os_list),
                    timestamp=date + timedelta(
                        hours=random.randint(0, 23),
                        minutes=random.randint(0, 59)
                    ),
                    is_error=random.random() < 0.1,  # 10% chance of error
                )
        
        self.stdout.write(self.style.SUCCESS('Successfully generated test data')) 