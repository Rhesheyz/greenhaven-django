from django.contrib import admin
from unfold.admin import ModelAdmin, StackedInline
from .models import Hotel, DetailRoom, ImageHotel, ImageRoom
import admin_thumbnails
from unfold.contrib.forms.widgets import WysiwygWidget
from django.db import models

@admin_thumbnails.thumbnail('image_room')
class ImageRoomInline(StackedInline):  
    model = ImageRoom
    extra = 1   
    fields = ('image_room', 'alt_text')  # ✅ Menambahkan alt_text

@admin_thumbnails.thumbnail('image_hotel')
class ImageHotelInline(StackedInline):
    model = ImageHotel
    extra = 1
    fields = ('image_hotel', 'alt_text')  # ✅ Menambahkan alt_text

@admin.register(Hotel)
class HotelAdmin(ModelAdmin):
    list_display = ('title', 'location', 'address')
    search_fields = ('title', 'location', 'address')
    list_filter = ('location',)
    ordering = ('title',)
    prepopulated_fields = {'slug': ('title',)}
    inlines = [ImageHotelInline]  
    formfield_overrides = {
        models.TextField: {'widget': WysiwygWidget},
    }

    fieldsets = (
        ("Informasi Hotel", {
            "fields": ("title", "slug", "address", "location", "description")
        }),
        ("SEO & Meta Data", {
            "fields": ("meta_title", "meta_description", "meta_robots"),
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at')

@admin.register(DetailRoom)
class DetailRoomAdmin(ModelAdmin):
    list_display = ('room_name', 'room_type', 'room_price', 'room_capacity', 'room_status')
    search_fields = ('room_name', 'room_slug', 'room_type', 'hotel__title')
    list_filter = ('room_type', 'featured_room', 'room_status', 'allow_pets', 'provide_breakfast')
    list_editable = ('room_status',)
    ordering = ('-created_at',)
    prepopulated_fields = {'room_slug': ('room_name',)}
    inlines = [ImageRoomInline]  
    formfield_overrides = {
        models.TextField: {'widget': WysiwygWidget},  
    }

    fieldsets = (
        ("Informasi Hotel", {
            "fields": ("hotel",) 
        }),
        ("Detail Kamar", {
            "fields": ("room_name", "room_slug", "room_type") 
        }),
        ("Harga & Kapasitas", {
            "fields": ("room_price", "room_size", "room_capacity") 
        }),
        ("Fasilitas", {
            "fields": ("allow_pets", "provide_breakfast", "featured_room", "extra_facilities") 
        }),
        ("Deskripsi", {
            "fields": ("room_description",)
        }),
        ("SEO & Meta Data", {
            "fields": ("meta_title", "meta_description", "meta_robots"),
        }),
        ("Status & Waktu", {
            "fields": ("room_status", "created_at", "updated_at"), 
        }),
    )

    readonly_fields = ('created_at', 'updated_at')
