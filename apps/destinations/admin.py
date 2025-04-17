from django.contrib import admin
from .models import Destinations, ImageDestinations
from unfold.admin import ModelAdmin
from django.contrib.auth.models import User, Group
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin, GroupAdmin as BaseGroupAdmin
from import_export.admin import ImportExportModelAdmin
from unfold.contrib.import_export.forms import ExportForm, ImportForm, SelectableFieldsExportForm
from apps.analytics.models import CustomEvent, ComplianceLog
from django.utils import timezone
import uuid
from unfold.contrib.forms.widgets import WysiwygWidget
from django.db import models
from unfold.admin import TabularInline

# Unregister default admin
admin.site.unregister(User)
admin.site.unregister(Group)

class UserEventTracker:
    @staticmethod
    def track_compliance(event_name, admin_user, affected_user, action=None, metadata=None):
        ComplianceLog.objects.create(
            timestamp=timezone.now(),
            user_id=admin_user.id,
            ip_address='127.0.0.1', 
            action_type=action,
            data_category='user_data',
            data_description=f"User: {affected_user.username} - Action: {action}",
            affected_users=[affected_user.id], 
            legal_basis='legitimate_interest',
            data_retention=timezone.now() + timezone.timedelta(days=365),
            sensitivity_level='high', 
            request_id=str(uuid.uuid4()),
            source_system='admin_interface',
            authorized_by=admin_user.username,
            purpose=f"Administrative {action} on user data",
            processing_location='local',
            cross_border=False,
            third_parties=None,
            metadata=metadata or {},
            notes=f"Event: {event_name}"
        )

@admin.register(User)
class UserAdmin(BaseUserAdmin, ModelAdmin):
    def save_model(self, request, obj, form, change):
        # Track user data changes
        is_password_change = 'password' in form.changed_data
        is_permission_change = any(field in form.changed_data 
                                 for field in ['is_staff', 'is_superuser', 'groups', 'user_permissions'])
        
        super().save_model(request, obj, form, change)

        if change:
            event_name = 'user_updated'
            action = 'update'
            if is_password_change:
                action = 'password_change'
            elif is_permission_change:
                action = 'permission_change'
        else:
            event_name = 'user_created'
            action = 'create'

        # Track sensitive changes in compliance log
        if is_password_change or is_permission_change or not change:
            UserEventTracker.track_compliance(
                event_name=event_name,
                admin_user=request.user,
                affected_user=obj,
                action=action,
                metadata={
                    'changed_fields': form.changed_data,
                    'admin_user': request.user.username,
                    'is_password_change': is_password_change,
                    'is_permission_change': is_permission_change
                }
            )

    def delete_model(self, request, obj):
        # Track user deletion
        UserEventTracker.track_compliance(
            event_name='user_deleted',
            admin_user=request.user,
            affected_user=obj,
            action='delete',
            metadata={
                'admin_user': request.user.username,
                'deleted_username': obj.username
            }
        )
        super().delete_model(request, obj)

    def delete_queryset(self, request, queryset):
        # Track bulk user deletion
        for obj in queryset:
            UserEventTracker.track_compliance(
                event_name='user_deleted',
                admin_user=request.user,
                affected_user=obj,
                action='bulk_delete',
                metadata={
                    'admin_user': request.user.username,
                    'deleted_username': obj.username
                }
            )
        super().delete_queryset(request, queryset)

    def change_password(self, request, user_id):
        # Track password changes through admin interface
        user = self.get_object(request, user_id)
        UserEventTracker.track_compliance(
            event_name='user_password_changed',
            admin_user=request.user,
            affected_user=user,
            action='password_change',
            metadata={
                'admin_user': request.user.username,
                'changed_by_admin': True
            }
        )
        return super().change_password(request, user_id)

@admin.register(Group)
class GroupAdmin(BaseGroupAdmin, ModelAdmin, ImportExportModelAdmin):
    import_form_class = ImportForm
    export_form_class = ExportForm
    
    def save_model(self, request, obj, form, change):
        # Track group changes
        is_permission_change = 'permissions' in form.changed_data
        
        super().save_model(request, obj, form, change)

        event_name = 'group_updated' if change else 'group_created'
        action = 'update' if change else 'create'

        # Always track group changes as they affect permissions
        GroupEventTracker.track_compliance(
            event_name=event_name,
            admin_user=request.user,
            group=obj,
            action=action,
            metadata={
                'changed_fields': form.changed_data,
                'admin_user': request.user.username,
                'is_permission_change': is_permission_change,
                'affected_users_count': obj.user_set.count()
            }
        )

    def delete_model(self, request, obj):
        # Track group deletion
        GroupEventTracker.track_compliance(
            event_name='group_deleted',
            admin_user=request.user,
            group=obj,
            action='delete',
            metadata={
                'admin_user': request.user.username,
                'deleted_group_name': obj.name,
                'affected_users_count': obj.user_set.count(),
                'affected_users': list(obj.user_set.values_list('username', flat=True))
            }
        )
        super().delete_model(request, obj)

    def delete_queryset(self, request, queryset):
        # Track bulk group deletion
        for obj in queryset:
            GroupEventTracker.track_compliance(
                event_name='group_deleted',
                admin_user=request.user,
                group=obj,
                action='bulk_delete',
                metadata={
                    'admin_user': request.user.username,
                    'deleted_group_name': obj.name,
                    'affected_users_count': obj.user_set.count(),
                    'affected_users': list(obj.user_set.values_list('username', flat=True))
                }
            )
        super().delete_queryset(request, queryset)

    def save_related(self, request, form, formsets, change):
        if change:
            old_users = set(form.instance.user_set.all())
        
        super().save_related(request, form, formsets, change)
        
        # Track membership changes if this is an update
        if change:
            new_users = set(form.instance.user_set.all())
            added_users = new_users - old_users
            removed_users = old_users - new_users
            
            if added_users or removed_users:
                GroupEventTracker.track_compliance(
                    event_name='group_membership_changed',
                    admin_user=request.user,
                    group=form.instance,
                    action='membership_update',
                    metadata={
                        'admin_user': request.user.username,
                        'added_users': [user.username for user in added_users],
                        'removed_users': [user.username for user in removed_users],
                        'total_users': form.instance.user_set.count()
                    }
                )

class DestinationEventTracker:
    @staticmethod
    def track_compliance(event_name, user, destination, action=None, metadata=None):
        ComplianceLog.objects.create(
            timestamp=timezone.now(),
            user_id=user.id if user else None,
            ip_address='127.0.0.1', 
            action_type=action,
            data_category='destination',
            data_description=f"Destination: {destination.title if destination else 'Multiple'} - Action: {action}",
            affected_users=None, 
            legal_basis='legitimate_interest',
            data_retention=timezone.now() + timezone.timedelta(days=365),
            sensitivity_level='low', 
            request_id=str(uuid.uuid4()),
            source_system='admin_interface',
            authorized_by=user.username if user else None,
            purpose=f"Administrative {action} on destination data",
            processing_location='local',
            cross_border=False,
            third_parties=None,
            metadata=metadata or {},
            notes=f"Event: {event_name}"
        )

    @staticmethod
    def track_event(event_name, user, destination, action=None, metadata=None):
        CustomEvent.objects.create(
            event_name=event_name,
            event_category='destination',
            user_id=user.id if user else None,
            user_type='staff' if user and user.is_staff else 'user',
            session_id=str(uuid.uuid4()),
            event_value={
                'destination_id': destination.id if destination else None,
                'destination_title': destination.title if destination else None,
                'action': action,
                'timestamp': timezone.now().isoformat()
            },
            source='admin',
            metadata=metadata or {}
        )
        
        if action in ['delete', 'bulk_delete', 'export']:
            DestinationEventTracker.track_compliance(
                event_name=event_name,
                user=user,
                destination=destination,
                action=action,
                metadata=metadata
            )

class ImageDestinationsInline(TabularInline):
    model = ImageDestinations
    extra = 1
    fields = ('image', 'alt_text')

@admin.register(Destinations)
class DestinationsAdmin(ModelAdmin):
    list_display = ('title', 'slug', 'location', 'created_at', 'updated_at')
    list_filter = ('created_at', 'updated_at')
    search_fields = ('title', 'description', 'location')
    prepopulated_fields = {'slug': ('title',)}
    inlines = [ImageDestinationsInline]

    # ✅ Menambahkan SEO fields ke dalam admin panel
    fieldsets = (
        ("Informasi Destinasi", {
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

    # Gunakan WysiwygWidget untuk field 'description' dan 'guides'
    formfield_overrides = {
        models.TextField: {'widget': WysiwygWidget},  # Default untuk semua TextField
    }

    def formfield_for_dbfield(self, db_field, **kwargs):
        # Khusus untuk description dan guides saja
        if db_field.name in ['description', 'guides']:
            kwargs['widget'] = WysiwygWidget
        return super().formfield_for_dbfield(db_field, **kwargs)

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        event_name = 'destination_updated' if change else 'destination_created'
        metadata = {
            'changed_fields': form.changed_data if change else None,
            'admin_user': request.user.username,
        }
        
        DestinationEventTracker.track_event(
            event_name=event_name,
            user=request.user,
            destination=obj,
            action='update' if change else 'create',
            metadata=metadata
        )

        if change and set(form.changed_data) & {'status', 'is_published', 'price'}:
            DestinationEventTracker.track_compliance(
                event_name=event_name,
                user=request.user,
                destination=obj,
                action='sensitive_update',
                metadata={
                    'changed_fields': list(set(form.changed_data) & {'status', 'is_published', 'price'}),
                    'admin_user': request.user.username
                }
            )

    def delete_model(self, request, obj):
        # Track both event and compliance for deletion
        DestinationEventTracker.track_event(
            event_name='destination_deleted',
            user=request.user,
            destination=obj,
            action='delete',
            metadata={'admin_user': request.user.username}
        )
        super().delete_model(request, obj)

    def delete_queryset(self, request, queryset):
        # Track both event and compliance for bulk deletion
        for obj in queryset:
            DestinationEventTracker.track_event(
                event_name='destination_deleted',
                user=request.user,
                destination=obj,
                action='bulk_delete',
                metadata={'admin_user': request.user.username}
            )
        super().delete_queryset(request, queryset)

    def export_action(self, request, queryset):
        # Track compliance for data export
        DestinationEventTracker.track_compliance(
            event_name='destination_data_exported',
            user=request.user,
            destination=None,
            action='export',
            metadata={
                'admin_user': request.user.username,
                'export_count': queryset.count(),
                'export_fields': self.get_export_fields()
            }
        )
        return super().export_action(request, queryset)

    def save_formset(self, request, form, formset, change):
        # Track inline changes (images)
        instances = formset.save(commit=False)
        
        # Track added/updated images
        for obj in instances:
            if isinstance(obj, ImageDestinations):
                event_name = 'destination_image_updated' if obj.pk else 'destination_image_added'
                DestinationEventTracker.track_event(
                    event_name=event_name,
                    user=request.user,
                    destination=obj.destinations,
                    action='update_image' if obj.pk else 'add_image',
                    metadata={
                        'admin_user': request.user.username,
                        'image_id': obj.pk
                    }
                )
        
        # Track deleted images
        for obj in formset.deleted_objects:
            if isinstance(obj, ImageDestinations):
                DestinationEventTracker.track_event(
                    event_name='destination_image_deleted',
                    user=request.user,
                    destination=obj.destinations,
                    action='delete_image',
                    metadata={
                        'admin_user': request.user.username,
                        'image_id': obj.pk
                    }
                )
        
        super().save_formset(request, form, formset, change)

@admin.register(ImageDestinations)
class ImageDestinationsAdmin(ModelAdmin):
    list_display = ('destinations', 'image', 'alt_text', 'created_at')  
    list_filter = ('created_at', 'updated_at')
    search_fields = ('destinations__title',)
    fields = ('destinations', 'image', 'alt_text', 'created_at', 'updated_at')  
    readonly_fields = ('created_at', 'updated_at')

class UserEventTracker:
    @staticmethod
    def track_compliance(event_name, admin_user, affected_user, action=None, metadata=None):
        ComplianceLog.objects.create(
            timestamp=timezone.now(),
            user_id=admin_user.id,
            ip_address='127.0.0.1',  # Ideally should get from request
            action_type=action,
            data_category='user_data',
            data_description=f"User: {affected_user.username} - Action: {action}",
            affected_users=[affected_user.id],  # Track affected user
            legal_basis='legitimate_interest',
            data_retention=timezone.now() + timezone.timedelta(days=365),
            sensitivity_level='high',  # User data is typically sensitive
            request_id=str(uuid.uuid4()),
            source_system='admin_interface',
            authorized_by=admin_user.username,
            purpose=f"Administrative {action} on user data",
            processing_location='local',
            cross_border=False,
            third_parties=None,
            metadata=metadata or {},
            notes=f"Event: {event_name}"
        )

    def save_model(self, request, obj, form, change):
        # Track user data changes
        is_password_change = 'password' in form.changed_data
        is_permission_change = any(field in form.changed_data 
                                 for field in ['is_staff', 'is_superuser', 'groups', 'user_permissions'])
        
        super().save_model(request, obj, form, change)

        if change:
            event_name = 'user_updated'
            action = 'update'
            if is_password_change:
                action = 'password_change'
            elif is_permission_change:
                action = 'permission_change'
        else:
            event_name = 'user_created'
            action = 'create'

        # Track sensitive changes in compliance log
        if is_password_change or is_permission_change or not change:
            UserEventTracker.track_compliance(
                event_name=event_name,
                admin_user=request.user,
                affected_user=obj,
                action=action,
                metadata={
                    'changed_fields': form.changed_data,
                    'admin_user': request.user.username,
                    'is_password_change': is_password_change,
                    'is_permission_change': is_permission_change
                }
            )

    def delete_model(self, request, obj):
        # Track user deletion
        UserEventTracker.track_compliance(
            event_name='user_deleted',
            admin_user=request.user,
            affected_user=obj,
            action='delete',
            metadata={
                'admin_user': request.user.username,
                'deleted_username': obj.username
            }
        )
        super().delete_model(request, obj)

    def delete_queryset(self, request, queryset):
        # Track bulk user deletion
        for obj in queryset:
            UserEventTracker.track_compliance(
                event_name='user_deleted',
                admin_user=request.user,
                affected_user=obj,
                action='bulk_delete',
                metadata={
                    'admin_user': request.user.username,
                    'deleted_username': obj.username
                }
            )
        super().delete_queryset(request, queryset)

    def change_password(self, request, user_id):
        # Track password changes through admin interface
        user = self.get_object(request, user_id)
        UserEventTracker.track_compliance(
            event_name='user_password_changed',
            admin_user=request.user,
            affected_user=user,
            action='password_change',
            metadata={
                'admin_user': request.user.username,
                'changed_by_admin': True
            }
        )
        return super().change_password(request, user_id)

class GroupEventTracker:
    @staticmethod
    def track_compliance(event_name, admin_user, group, action=None, metadata=None):
        ComplianceLog.objects.create(
            timestamp=timezone.now(),
            user_id=admin_user.id,
            ip_address='127.0.0.1',
            action_type=action,
            data_category='group_permissions',
            data_description=f"Group: {group.name} - Action: {action}",
            affected_users=[user.id for user in group.user_set.all()],  # Track all users in group
            legal_basis='legitimate_interest',
            data_retention=timezone.now() + timezone.timedelta(days=365),
            sensitivity_level='high',  # Group permissions are sensitive
            request_id=str(uuid.uuid4()),
            source_system='admin_interface',
            authorized_by=admin_user.username,
            purpose=f"Administrative {action} on group permissions",
            processing_location='local',
            cross_border=False,
            third_parties=None,
            metadata=metadata or {},
            notes=f"Event: {event_name}"
        )