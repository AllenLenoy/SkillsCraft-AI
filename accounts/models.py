from django.db import models
from django.contrib.auth.models import User


class ArtisanProfile(models.Model):
    """
    Extends the built-in Django User model with artisan studio details,
    craft specialities, and curation/approval status.
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="artisan_profile",
        help_text="Underlying user account for authentication and credentials."
    )
    display_name = models.CharField(
        max_length=120,
        help_text="Public artisan studio or brand name (e.g. 'Avani Handcrafts')."
    )
    bio = models.TextField(
        blank=True,
        help_text="Artisan story, philosophy, and traditional technique background."
    )
    location = models.CharField(
        max_length=150,
        blank=True,
        help_text="Artisan workshop city or region of origin (e.g. 'Jaipur, Rajasthan')."
    )
    craft_speciality = models.CharField(
        max_length=100,
        help_text="Primary craft domain (e.g. 'Terracotta Pottery', 'Block Printing', 'Handloom')."
    )
    is_approved = models.BooleanField(
        default=False,
        help_text="Whether this artisan has been approved by platform administration to publish products."
    )
    is_verified = models.BooleanField(
        default=False,
        help_text="Whether the artisan's provenance and ethical craftsmanship have been verified."
    )
    profile_image = models.ImageField(
        upload_to="artisans/profiles/",
        blank=True,
        null=True,
        help_text="Profile or workshop photo."
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Artisan Profile"
        verbose_name_plural = "Artisan Profiles"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.display_name} ({self.craft_speciality})"
