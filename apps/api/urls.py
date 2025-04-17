from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import *

router = DefaultRouter()

# Destinations
router.register(r'destinations', DestinationsViewset, basename='destinations')
router.register(r'destinations-images', ImageDestinationsViewset, basename='destinations-images')

# Flora
router.register(r'flora', FloraViewset, basename='flora')
router.register(r'flora-images', ImageFloraViewset, basename='flora-images')

# Health
router.register(r'health', HealthViewset, basename='health')
router.register(r'health-images', ImageHealthViewset, basename='health-images')

# Kuliner
router.register(r'kuliner', KulinerViewset, basename='kuliner')
router.register(r'kuliner-images', ImageKulinerViewset, basename='kuliner-images')

# Fauna
router.register(r'fauna', FaunaViewset, basename='fauna')
router.register(r'fauna-images', ImageFaunaViewset, basename='fauna-images')

urlpatterns = [
    path('', include(router.urls)),
    path('latest-content/', LatestContentView.as_view(), name='latest-content'),
]
