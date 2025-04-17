from django.contrib import admin
from unfold.admin import ModelAdmin
from .models import KategoriArtikel, Artikel
from django.db import models
from unfold.contrib.forms.widgets import WysiwygWidget

@admin.register(KategoriArtikel)
class KategoriArtikelAdmin(ModelAdmin):
    list_display = ('title', 'created_at', 'updated_at')
    search_fields = ('title', 'slug')
    ordering = ('-created_at',)
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ( 'created_at', 'updated_at')

@admin.register(Artikel)
class ArtikelAdmin(ModelAdmin):
    list_display = ('title', 'kategori_artikel', 'publish', 'total_view', 'created_at')
    search_fields = ('title', 'slug', 'kategori_artikel__title')
    list_filter = ('kategori_artikel', 'publish')
    ordering = ('-created_at',)
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ('total_view', 'created_at', 'updated_at')

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        if db_field.name == "description":
            kwargs["widget"] = WysiwygWidget  
        return super().formfield_for_dbfield(db_field, request, **kwargs)

    fieldsets = (
        ("Kategori & Informasi Artikel", {
            "fields": ("kategori_artikel", "title", "slug",)  
        }),
        ("Konten", {
            "fields": ("preview_description", "description", "image", "alt_text"),
        }),
        ("SEO & Meta Data", {
            "fields": ("meta_title", "meta_description", "meta_robots"),
        }),
        ("Status & Statistik", {
            "fields": ("publish", "total_view", "created_at", "updated_at"),  
        }),
    )
