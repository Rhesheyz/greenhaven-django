from django.contrib import admin
from .models import Health, ImageHealth
from unfold.admin import ModelAdmin
from apps.analytics.models import CustomEvent
from django.utils import timezone
import uuid
from unfold.contrib.forms.widgets import WysiwygWidget
from django.db import models
from .models import FasilitasHealth
from unfold.admin import TabularInline

class HealthEventTracker:
    @staticmethod
    def track_event(event_name, user, health, action=None, metadata=None):
        CustomEvent.objects.create(
            event_name=event_name,
            event_category='health',
            user_id=user.id if user else None,
            user_type='staff' if user and user.is_staff else 'user',
            session_id=str(uuid.uuid4()),
            event_value={
                'health_id': health.id if health else None,
                'health_title': health.title if health else None,
                'action': action,
                'timestamp': timezone.now().isoformat()
            },
            source='admin',
            metadata=metadata or {}
        )

class ImageHealthInline(TabularInline):
    model = ImageHealth
    extra = 1
    fields = ('image', 'alt_text')

class FasilitasHealthInline(TabularInline):
    model = FasilitasHealth
    extra = 1

@admin.register(Health)
class HealthAdmin(ModelAdmin):
    list_display = ('title', 'slug', 'created_at', 'updated_at')
    search_fields = ('title', 'slug')
    prepopulated_fields = {'slug': ('title',)}
    inlines = [ImageHealthInline]  

    fieldsets = (
        ("Informasi Health", {
            "fields": ("title", "slug", "location", "g_maps", "open_hours", "close_hours", "description", "guides"),
        }),
        ("SEO & Meta Data", {
            "fields": ("meta_title", "meta_description", "meta_robots"),
        }),
        ("Waktu Pembuatan", {
            "fields": ("created_at", "updated_at"),
        }),
    )

    readonly_fields = ('created_at', 'updated_at')

    formfield_overrides = {
        models.TextField: {'widget': WysiwygWidget},  
    }
    
    def formfield_for_dbfield(self, db_field, **kwargs):
        if db_field.name in ['description', 'guides']:
            kwargs['widget'] = WysiwygWidget
        return super().formfield_for_dbfield(db_field, **kwargs)

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        event_name = 'health_updated' if change else 'health_created'
        metadata = {
            'changed_fields': form.changed_data if change else None,
            'admin_user': request.user.username,
        }
        
        HealthEventTracker.track_event(
            event_name=event_name,
            user=request.user,
            health=obj,
            action='update' if change else 'create',
            metadata=metadata
        )

    def delete_model(self, request, obj):
        # Track single health deletion
        HealthEventTracker.track_event(
            event_name='health_deleted',
            user=request.user,
            health=obj,
            action='delete',
            metadata={'admin_user': request.user.username}
        )
        super().delete_model(request, obj)

    def delete_queryset(self, request, queryset):
        # Track bulk deletion
        for obj in queryset:
            HealthEventTracker.track_event(
                event_name='health_deleted',
                user=request.user,
                health=obj,
                action='bulk_delete',
                metadata={'admin_user': request.user.username}
            )
        super().delete_queryset(request, queryset)

    def save_formset(self, request, form, formset, change):
        instances = formset.save(commit=False)
        
        for obj in instances:
            if isinstance(obj, ImageHealth):
                event_name = 'health_image_updated' if obj.pk else 'health_image_added'
                HealthEventTracker.track_event(
                    event_name=event_name,
                    user=request.user,
                    health=obj.health,
                    action='update_image' if obj.pk else 'add_image',
                    metadata={
                        'admin_user': request.user.username,
                        'image_id': obj.pk
                    }
                )
        
        # Track deleted images
        for obj in formset.deleted_objects:
            if isinstance(obj, ImageHealth):
                HealthEventTracker.track_event(
                    event_name='health_image_deleted',
                    user=request.user,
                    health=obj.health,
                    action='delete_image',
                    metadata={
                        'admin_user': request.user.username,
                        'image_id': obj.pk
                    }
                )
        
        super().save_formset(request, form, formset, change)

@admin.register(ImageHealth)
class ImageHealthAdmin(ModelAdmin):
    list_display = ('health', 'image', 'alt_text', 'created_at', 'updated_at')
    list_filter = ('health',)
    search_fields = ('health__title',)
    fields = ('health', 'image', 'alt_text', 'created_at', 'updated_at') 
    readonly_fields = ('created_at', 'updated_at') 
        
@admin.register(FasilitasHealth)
class FasilitasHealthAdmin(ModelAdmin):
    list_display = ('health', 'fasilitas', 'created_at', 'updated_at')
    list_filter = ('health',)

