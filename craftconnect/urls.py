from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from accounts import views as account_views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("marketplace.urls")),
    path("accounts/", include("accounts.urls")),
    
    # Direct convenience routes
    path("login/", account_views.AuthView.as_view(), name="login_alias"),
    path("register/", account_views.AuthView.as_view(), name="register_alias"),
    path("dashboard/", account_views.DashboardRedirectView.as_view(), name="dashboard_alias"),
    path("dashboard/buyer/", account_views.BuyerDashboardView.as_view(), name="dashboard_buyer_alias"),
    path("dashboard/seller/", account_views.ArtisanStudioView.as_view(), name="dashboard_seller_alias"),
    path("dashboard/admin/", account_views.ModerationPortalView.as_view(), name="dashboard_admin_alias"),
    path("seller/", account_views.ArtisanStudioView.as_view(), name="seller_alias"),
    path("studio/", account_views.ArtisanStudioView.as_view(), name="studio_alias"),
    path("buyer/", account_views.BuyerDashboardView.as_view(), name="buyer_alias"),
    path("moderation/", account_views.ModerationPortalView.as_view(), name="moderation_alias"),
]

# Syllabus Unit II: Custom HTTP Error Handlers
handler404 = "marketplace.views.custom_404_view"
handler500 = "marketplace.views.custom_500_view"


# Serve media files in local development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
