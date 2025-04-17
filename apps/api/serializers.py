from rest_framework import serializers
from apps.destinations.models import Destinations, ImageDestinations
from apps.flora.models import Flora, ImageFlora
from apps.health.models import Health, ImageHealth, FasilitasHealth
from apps.kuliner.models import Kuliner, ImageKuliner, ListMenuKuliner
from apps.fauna.models import Fauna, ImageFauna       

# flora
class ImageFloraSerializer(serializers.ModelSerializer):
    class Meta:
        model = ImageFlora
        fields = ['flora', 'image', 'created_at', 'updated_at']
    
class FloraSerializer(serializers.ModelSerializer):
    images = ImageFloraSerializer(many=True, read_only=True)
    class Meta:
        model = Flora
        fields = ['title', 'slug', 'description', 'created_at', 'updated_at', 'images']

# health
class ImageHealthSerializer(serializers.ModelSerializer):
    class Meta:
        model = ImageHealth
        fields = ['health', 'image', 'created_at', 'updated_at']
        
class FasilitasHealthSerializer(serializers.ModelSerializer):
    class Meta:
        model = FasilitasHealth
        fields = ['health', 'fasilitas', 'created_at', 'updated_at']
        
class HealthSerializer(serializers.ModelSerializer):
    images = ImageHealthSerializer(many=True, read_only=True)
    fasilitas = FasilitasHealthSerializer(many=True, read_only=True)
    class Meta:
        model = Health
        fields = ['title', 'slug', 'location', 'g_maps', 'guides', 'open_hours', 'close_hours', 'description', 'created_at', 'updated_at', 'images', 'fasilitas']
        
# kuliner
class ImageKulinerSerializer(serializers.ModelSerializer):
    class Meta:
        model = ImageKuliner
        fields = ['kuliner', 'image', 'created_at', 'updated_at']
        
class ListMenuKulinerSerializer(serializers.ModelSerializer):
    class Meta:
        model = ListMenuKuliner
        fields = ['kuliner', 'list_menu', 'harga', 'created_at', 'updated_at']
        
class KulinerSerializer(serializers.ModelSerializer):
    images = ImageKulinerSerializer(many=True, read_only=True)
    list_menu = ListMenuKulinerSerializer(many=True, read_only=True)
    class Meta:
        model = Kuliner
        fields = ['title', 'slug', 'location', 'g_maps', 'guides', 'open_hours', 'close_hours', 'description', 'created_at', 'updated_at', 'images', 'list_menu']

# fauna
class ImageFaunaSerializer(serializers.ModelSerializer):
    class Meta:
        model = ImageFauna
        fields = ['fauna', 'image', 'created_at', 'updated_at']

class FaunaSerializer(serializers.ModelSerializer):
    images = ImageFaunaSerializer(many=True, read_only=True)
    class Meta:
        model = Fauna
        fields = ['title', 'slug', 'description', 'created_at', 'updated_at', 'images']

# destinations
class ImageDestinationsSerializer(serializers.ModelSerializer):
    class Meta:
        model = ImageDestinations
        fields = ['destinations', 'image', 'created_at', 'updated_at']

class DestinationsSerializer(serializers.ModelSerializer):
    fauna = FaunaSerializer(many=True, read_only=True)
    images = ImageDestinationsSerializer(many=True, read_only=True)
    flora = FloraSerializer(many=True, read_only=True)
    class Meta:
        model = Destinations
        fields = ['title', 'slug', 'description', 'location', 'g_maps', 'guides', 'open_hours', 'close_hours', 'created_at', 'updated_at', 'images', 'fauna', 'flora'] 