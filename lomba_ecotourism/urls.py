from django.urls import path, include
from django.conf.urls.static import static
from django.conf import settings
from django.contrib import admin
from django.conf.urls.i18n import i18n_patterns
from django.shortcuts import redirect

# Fungsi untuk redirect
# def redirect_to_greenhaven(request):
#     return redirect('https://greenhaven.rwiconsulting.tech/destinations')

urlpatterns = [
    # path('', redirect_to_greenhaven),  # Tambahkan ini untuk redirect URL utama
    path('i18n/', include('django.conf.urls.i18n')),
    path('api/', include('apps.ai.urls')),
    path('api/', include('apps.api.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

urlpatterns += i18n_patterns(
    path('admin/', admin.site.urls),
    path('analytics/', include('apps.analytics.urls')),
    # path('__debug__/', include('debug_toolbar.urls')),
)