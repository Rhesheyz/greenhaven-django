from django.db import models
from django.utils.text import slugify
from apps.aiSeo.seo_generator import generate_seo  

class KategoriArtikel(models.Model):
    title = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)  
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

class Artikel(models.Model):
    kategori_artikel = models.ForeignKey(KategoriArtikel, on_delete=models.CASCADE, related_name="artikels")
    title = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)  
    preview_description = models.TextField()
    description = models.TextField()

    # ✅ Gambar untuk Artikel
    image = models.ImageField(upload_to="artikel_images/", blank=True, null=True)
    alt_text = models.CharField(
        max_length=255,
        blank=True,
        help_text="Deskripsi alternatif untuk gambar (SEO & aksesibilitas)"
    )

    # ✅ Meta tags untuk SEO
    meta_title = models.CharField(max_length=255, blank=True, help_text="Judul untuk SEO (meta title)")
    meta_description = models.TextField(blank=True, help_text="Deskripsi untuk SEO (meta description)")
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

    total_view = models.PositiveIntegerField(default=0, editable=False)  
    publish = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)  

        # Jika alt_text kosong, otomatis isi dengan title artikel
        if not self.alt_text:
            self.alt_text = self.title

        # AI SEO: Jika meta_title & meta_description kosong, otomatis generate
        if not self.meta_title or not self.meta_description:
            self.meta_title, self.meta_description = generate_seo(self.title, self.description)

        super().save(*args, **kwargs)

    def __str__(self):
        return self.title
