from django.contrib import admin
from .models import ArtisanProfile


@admin.register(ArtisanProfile)
class ArtisanProfileAdmin(admin.ModelAdmin):
    list_display = (
        "display_name",
        "user",
        "craft_speciality",
        "location",
        "is_approved",
        "is_verified",
        "created_at",
    )
    list_filter = (
        "is_approved",
        "is_verified",
        "craft_speciality",
        "created_at",
    )
    search_fields = (
        "display_name",
        "user__username",
        "user__email",
        "location",
        "craft_speciality",
    )
    list_editable = ("is_approved", "is_verified")
    ordering = ("-created_at",)
    actions = ["verify_selected_artisans", "revoke_verification"]

    @admin.action(description="Approve and verify selected master artisans")
    def verify_selected_artisans(self, request, queryset):
        count = queryset.update(is_approved=True, is_verified=True)
        self.message_user(request, f"{count} artisan(s) successfully verified and approved.")

    @admin.action(description="Revoke verified maker status")
    def revoke_verification(self, request, queryset):
        count = queryset.update(is_verified=False)
        self.message_user(request, f"{count} artisan(s) verification status revoked.")

