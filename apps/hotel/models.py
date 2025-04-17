from django.db import models
from apps.aiSeo.seo_generator import generate_seo  

class Hotel(models.Model):
    title = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    address = models.CharField(max_length=500)
    location = models.CharField(max_length=255)
    description = models.TextField()

    meta_title = models.CharField(max_length=255, help_text="Judul untuk SEO (meta title)")
    meta_description = models.TextField(help_text="Deskripsi untuk SEO (meta description)")
    meta_robots = models.CharField(
        max_length=50,
        choices=[
            ("index, follow", "Index, Follow"),
            ("noindex, follow", "NoIndex, Follow"),
            ("noindex, nofollow", "NoIndex, NoFollow"),
        ],
        default="index, follow",
        help_text="Kontrol indexing halaman (robots meta tag)"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.meta_title or not self.meta_description:
            self.meta_title, self.meta_description = generate_seo(self.title, self.description)

        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.title

class DetailRoom(models.Model):
    hotel = models.ForeignKey(Hotel, on_delete=models.CASCADE, related_name="rooms")  
    room_name = models.CharField(max_length=255)
    room_slug = models.SlugField(unique=True)
    room_type = models.CharField(max_length=50)
    room_price = models.DecimalField(max_digits=10, decimal_places=2)
    room_size = models.PositiveIntegerField(help_text="Size in square meters")
    room_capacity = models.PositiveIntegerField(help_text="Maximum number of guests")
    allow_pets = models.BooleanField(default=False)
    provide_breakfast = models.BooleanField(default=False)
    featured_room = models.TextField(blank=True, null=True) 
    room_description = models.TextField()
    extra_facilities = models.TextField(blank=True, null=True)
    room_status = models.BooleanField(default=True, help_text="Available or not")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    meta_title = models.CharField(max_length=255, help_text="Judul untuk SEO (meta title)")
    meta_description = models.TextField(help_text="Deskripsi untuk SEO (meta description)")
    meta_robots = models.CharField(
        max_length=50,
        choices=[
            ("index, follow", "Index, Follow"),
            ("noindex, follow", "NoIndex, Follow"),
            ("noindex, nofollow", "NoIndex, NoFollow"),
        ],
        default="index, follow",
        help_text="Kontrol indexing halaman (robots meta tag)"
    )
    
    def save(self, *args, **kwargs):
        if not self.meta_title or not self.meta_description:
            self.meta_title, self.meta_description = generate_seo(self.title, self.description)

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.room_name} - {self.hotel.title}"
    

class ImageHotel(models.Model):
    hotel = models.ForeignKey(Hotel, on_delete=models.CASCADE, related_name="images")  
    image_hotel = models.ImageField(upload_to='hotel_images/')
    alt_text = models.CharField(
        max_length=255, 
        blank=True, 
        help_text="Deskripsi alternatif untuk gambar hotel (SEO & aksesibilitas)"
    )

    def save(self, *args, **kwargs):
        if not self.alt_text:
            self.alt_text = self.hotel.title 
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Image for {self.hotel.title}"

class ImageRoom(models.Model):
    detail_room = models.ForeignKey(DetailRoom, on_delete=models.CASCADE, related_name="images") 
    image_room = models.ImageField(upload_to='room_images/')
    alt_text = models.CharField(
        max_length=255, 
        blank=True, 
        help_text="Deskripsi alternatif untuk gambar kamar (SEO & aksesibilitas)"
    )

    def save(self, *args, **kwargs):
        if not self.alt_text:
            self.alt_text = self.detail_room.room_name 
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Image for {self.detail_room.room_name}"
