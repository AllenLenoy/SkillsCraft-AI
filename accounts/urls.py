from django.urls import path
from . import views

app_name = "accounts"

urlpatterns = [
    # Authentication & Onboarding
    path("auth/", views.AuthView.as_view(), name="auth"),
    path("login/", views.AuthView.as_view(), name="login"),
    path("register/", views.AuthView.as_view(), name="register"),
    path("logout/", views.LogoutView.as_view(), name="logout"),

    # Role-Aware Central Router
    path("dashboard/", views.DashboardRedirectView.as_view(), name="dashboard"),

    # Dedicated Buyer Dashboard
    path("buyer/", views.BuyerDashboardView.as_view(), name="buyer_dashboard"),
    path("dashboard/buyer/", views.BuyerDashboardView.as_view(), name="buyer_dashboard_alt"),

    # Dedicated Seller Dashboard (Artisan Studio)
    path("seller/", views.ArtisanStudioView.as_view(), name="seller_dashboard"),
    path("studio/", views.ArtisanStudioView.as_view(), name="artisan_studio"),
    path("dashboard/seller/", views.ArtisanStudioView.as_view(), name="seller_dashboard_alt"),
    path("become-artisan/", views.BecomeArtisanView.as_view(), name="become_artisan"),
    path("studio/ai-assistant/", views.AIAssistantSuggestView.as_view(), name="ai_assistant_suggest"),

    # Dedicated Admin Dashboard (Moderation & Curation Portal)
    path("admin-portal/", views.ModerationPortalView.as_view(), name="admin_dashboard"),
    path("moderation/", views.ModerationPortalView.as_view(), name="moderation"),
    path("dashboard/admin/", views.ModerationPortalView.as_view(), name="admin_dashboard_alt"),

    # Public Artisan Studio Showcase
    path("artisans/<int:pk>/", views.ArtisanDetailView.as_view(), name="artisan_detail"),
]
