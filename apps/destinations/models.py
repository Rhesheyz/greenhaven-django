from django.db import models
from PIL import Image
from io import BytesIO
from django.core.files.base import ContentFile
import os
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from apps.aiSeo.seo_generator import generate_seo  


class Destinations(models.Model):
    title = models.CharField(
        max_length=255, 
        help_text=_("Dont more than 255 characters")
    )
    slug = models.SlugField(unique=True)
    location = models.CharField(blank=True, max_length=255)
    g_maps = models.URLField(blank=True, help_text=_("Google Maps URL"), max_length=2000)
    open_hours = models.DateTimeField(blank=True, null=True)
    close_hours = models.DateTimeField(blank=True, null=True)
    description = models.TextField(blank=True)
    guides = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # ✅ SEO Meta Tags
    meta_title = models.CharField(
        max_length=255, 
        help_text=_("Title for SEO (meta title)")
    )
    meta_description = models.TextField(
        help_text=_("Description for SEO (meta description)")
    )
    meta_robots = models.CharField(
        max_length=50,
        choices=[
            ("index, follow", "Index, Follow"),
            ("noindex, follow", "NoIndex, Follow"),
            ("noindex, nofollow", "NoIndex, NoFollow"),
        ],
        default="index, follow",
        help_text=_("Control indexing of this page (robots meta tag)")
    )
    
    def save(self, *args, **kwargs):
        if not self.meta_title or not self.meta_description:
            self.meta_title, self.meta_description = generate_seo(self.title, self.description)

        super().save(*args, **kwargs)

    def __str__(self):
        return self.title


class ImageDestinations(models.Model):
    destinations = models.ForeignKey(Destinations, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='destinations/', help_text=_("Image size max 10MB and max resolution 2000x2000px auto compress"))
    alt_text = models.CharField(
        max_length=255, 
        blank=True, 
        help_text=_("Alternative text for the image (SEO & accessibility)")
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        # Jika alt_text kosong, otomatis isi dengan title destination
        if not self.alt_text:
            self.alt_text = self.destinations.title
        super().save(*args, **kwargs)

    def compress_image(self, image, max_size=2000, quality=88):
        img = Image.open(image)
        
        # Pertahankan format original
        img_format = img.format or 'JPEG'
        
        # Convert colorspace jika diperlukan
        if img_format == 'JPEG' and img.mode != 'RGB':
            img = img.convert('RGB')
        elif img_format == 'PNG' and img.mode != 'RGBA':
            img = img.convert('RGBA')
            
        # Cek ukuran file (dalam bytes)
        img_size = image.size
        max_file_size = getattr(settings, 'MAX_IMAGE_SIZE', 5 * 1024 * 1024)  # 5MB default
        
        # Resize dan kompresi progresif
        while img_size > max_file_size:
            buffer = BytesIO()
            
            # Resize jika terlalu besar
            if img.size[0] > max_size or img.size[1] > max_size:
                ratio = min(max_size/img.size[0], max_size/img.size[1])
                new_size = tuple([int(x*ratio) for x in img.size])
                img = img.resize(new_size, Image.Resampling.LANCZOS)
            
            # Simpan dengan progressive JPEG untuk file besar
            if img_format == 'JPEG':
                img.save(buffer, format=img_format, quality=quality, 
                        optimize=True, progressive=True)
            else:
                img.save(buffer, format=img_format, optimize=True)
            
            # Cek ukuran hasil
            img_size = buffer.tell()
            
            # Kurangi quality atau size jika masih terlalu besar
            if img_size > max_file_size:
                quality = max(quality - 5, 60)  # Minimal quality 60
                max_size = int(max_size * 0.8)  # Kurangi size 20%
        
        # Generate nama file
        file_name = os.path.splitext(image.name)[0]
        extension = 'jpg' if img_format == 'JPEG' else img_format.lower()
        new_name = f"{file_name}_compressed.{extension}"
        
        return ContentFile(buffer.getvalue(), name=new_name)

    def __str__(self):
        return f"Image for {self.destinations.title}"