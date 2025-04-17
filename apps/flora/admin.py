from django.contrib import admin
from .models import Flora, ImageFlora
from unfold.admin import ModelAdmin
from apps.analytics.models import CustomEvent
from django.utils import timezone
import uuid
from unfold.contrib.forms.widgets import WysiwygWidget
from django.db import models
from unfold.admin import TabularInline

class FloraEventTracker:
    @staticmethod
    def track_event(event_name, user, flora, action=None, metadata=None):
        CustomEvent.objects.create(
            event_name=event_name,
            event_category='flora',
            user_id=user.id if user else None,
            user_type='staff' if user and user.is_staff else 'user',
            session_id=str(uuid.uuid4()),
            event_value={
                'flora_id': flora.id if flora else None,
                'flora_title': flora.title if flora else None,
                'action': action,
                'timestamp': timezone.now().isoformat()
            },
            source='admin',
            metadata=metadata or {}
        )

class ImageFloraInline(TabularInline):
    model = ImageFlora
    extra = 1
    fields = ('image', 'alt_text')

@admin.register(Flora)
class FloraAdmin(ModelAdmin):
    list_display = ('title', 'slug', 'created_at', 'updated_at')
    search_fields = ('title', 'slug')
    prepopulated_fields = {'slug': ('title',)}
    inlines = [ImageFloraInline]

    fieldsets = (
        ("Informasi Flora", {
            "fields": ("destinations", "title", "slug", "description"),
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


    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        # Track flora creation/update
        event_name = 'flora_updated' if change else 'flora_created'
        metadata = {
            'changed_fields': form.changed_data if change else None,
            'admin_user': request.user.username,
        }
        
        FloraEventTracker.track_event(
            event_name=event_name,
            user=request.user,
            flora=obj,
            action='update' if change else 'create',
            metadata=metadata
        )

    def delete_model(self, request, obj):
        # Track single flora deletion
        FloraEventTracker.track_event(
            event_name='flora_deleted',
            user=request.user,
            flora=obj,
            action='delete',
            metadata={'admin_user': request.user.username}
        )
        super().delete_model(request, obj)

    def delete_queryset(self, request, queryset):
        # Track bulk deletion
        for obj in queryset:
            FloraEventTracker.track_event(
                event_name='flora_deleted',
                user=request.user,
                flora=obj,
                action='bulk_delete',
                metadata={'admin_user': request.user.username}
            )
        super().delete_queryset(request, queryset)

    def save_formset(self, request, form, formset, change):
        # Track inline changes (images)
        instances = formset.save(commit=False)
        
        # Track added/updated images
        for obj in instances:
            if isinstance(obj, ImageFlora):
                event_name = 'flora_image_updated' if obj.pk else 'flora_image_added'
                FloraEventTracker.track_event(
                    event_name=event_name,
                    user=request.user,
                    flora=obj.flora,
                    action='update_image' if obj.pk else 'add_image',
                    metadata={
                        'admin_user': request.user.username,
                        'image_id': obj.pk
                    }
                )
        
        # Track deleted images
        for obj in formset.deleted_objects:
            if isinstance(obj, ImageFlora):
                FloraEventTracker.track_event(
                    event_name='flora_image_deleted',
                    user=request.user,
                    flora=obj.flora,
                    action='delete_image',
                    metadata={
                        'admin_user': request.user.username,
                        'image_id': obj.pk
                    }
                )
        
        super().save_formset(request, form, formset, change)

@admin.register(ImageFlora)
class ImageFloraAdmin(ModelAdmin):
    list_display = ('flora', 'image', 'alt_text', 'created_at', 'updated_at')  
    list_filter = ('flora',)
    search_fields = ('flora__title',)
    fields = ('flora', 'image', 'alt_text', 'created_at', 'updated_at')  
    readonly_fields = ('created_at', 'updated_at')