from django.db import models
from apps.destinations.models import Destinations 
from PIL import Image
from io import BytesIO
from django.core.files.base import ContentFile
from django.conf import settings
import os
from django.utils.translation import gettext_lazy as _
from apps.aiSeo.seo_generator import generate_seo  

class Flora(models.Model):
    destinations = models.ForeignKey(Destinations, on_delete=models.CASCADE, related_name='flora')
    title = models.CharField(
        max_length=255, 
        help_text=_("Dont more than 255 characters")
    )
    slug = models.SlugField(unique=True)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

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

class ImageFlora(models.Model):
    flora = models.ForeignKey(Flora, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='flora/', help_text=_("Image size max 10MB and max resolution 2000x2000px auto compress"))
    alt_text = models.CharField(
        max_length=255, 
        blank=True, 
        help_text=_("Alternative text for the image (SEO & accessibility)")
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def compress_image(self, image, max_size=2000, quality=88):
        img = Image.open(image)
        
        img_format = img.format or 'JPEG'
        
        if img_format == 'JPEG' and img.mode != 'RGB':
            img = img.convert('RGB')
        elif img_format == 'PNG' and img.mode != 'RGBA':
            img = img.convert('RGBA')
            
        buffer = BytesIO()
        
        # Cek ukuran file (dalam bytes)
        img_size = image.size
        max_file_size = getattr(settings, 'MAX_IMAGE_SIZE', 5 * 1024 * 1024)  
        
        # Resize jika terlalu besar
        if img.size[0] > max_size or img.size[1] > max_size:
            ratio = min(max_size/img.size[0], max_size/img.size[1])
            new_size = tuple([int(x*ratio) for x in img.size])
            img = img.resize(new_size, Image.Resampling.LANCZOS)
        
        # Kompresi 
        while True:
            buffer.seek(0)
            buffer.truncate()
            
            if img_format == 'JPEG':
                img.save(buffer, format=img_format, quality=quality, 
                        optimize=True, progressive=True)
            else:
                img.save(buffer, format=img_format, optimize=True)
            
            img_size = buffer.tell()
            
            if img_size <= max_file_size:
                break
                
            quality = max(quality - 5, 60)  # Minimal quality 60
            if quality == 60:  # Jika quality sudah minimal, kurangi ukuran
                max_size = int(max_size * 0.8)  # Kurangi size 20%
                ratio = min(max_size/img.size[0], max_size/img.size[1])
                new_size = tuple([int(x*ratio) for x in img.size])
                img = img.resize(new_size, Image.Resampling.LANCZOS)
            
            # Jika ukuran sudah minimal dan quality juga minimal, keluar dari loop
            if quality == 60 and max_size < 800:  # Minimal size 800px
                break
        
        # Generate nama file
        file_name = os.path.splitext(image.name)[0]
        extension = 'jpg' if img_format == 'JPEG' else img_format.lower()
        new_name = f"{file_name}_compressed.{extension}"
        
        return ContentFile(buffer.getvalue(), name=new_name)

    def save(self, *args, **kwargs):
        # Jika alt_text kosong, otomatis isi title flora
        if not self.alt_text:
            self.alt_text = self.flora.title
        super().save(*args, **kwargs)
        
        if self.image:
            # Kompresi hanya dilakukan saat upload gambar baru
            if not self.id:
                self.image = self.compress_image(self.image)
            elif hasattr(self, '_original_image') and self._original_image != self.image:
                self.image = self.compress_image(self.image)
        super().save(*args, **kwargs)
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Simpan gambar original untuk pengecekan perubahan
        self._original_image = self.image if self.id else None

    def __str__(self):
        return f"Image for {self.flora.title}"
