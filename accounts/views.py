import json
from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import TemplateView, DetailView, View
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.models import User
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.http import JsonResponse
from django.utils.text import slugify

from .models import ArtisanProfile
from .forms import LoginForm, RegisterForm, ArtisanProductForm, BecomeArtisanForm
from marketplace.models import Product, Category, Enquiry, SavedProduct, Order
from marketplace.ai_service import generate_catalogue_assistant_suggestions


# ==============================================================================
# ROLE-BASED ACCESS CONTROL MIXINS
# ==============================================================================

class BuyerRequiredMixin(LoginRequiredMixin):
    """
    Enforces authentication for Patron / Buyer spaces.
    If unauthenticated, redirects to login with an informative message.
    """
    login_url = "accounts:login"

    def handle_no_permission(self):
        messages.info(self.request, "Please sign in to access your Patron Sanctuary.")
        return super().handle_no_permission()


class SellerRequiredMixin(LoginRequiredMixin):
    """
    Enforces authentication AND verifies that the user possesses an associated ArtisanProfile.
    If the user is an authenticated Buyer without an ArtisanProfile, redirects them
    to the 'Become an Artisan' atelier onboarding setup.
    """
    login_url = "accounts:login"

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.info(request, "Please sign in to access the Artisan Studio.")
            return self.handle_no_permission()

        if not hasattr(request.user, "artisan_profile"):
            messages.info(
                request,
                "You are currently signed in as a Patron. Set up your Artisan Studio below to begin listing handcrafted pieces!"
            )
            return redirect("accounts:become_artisan")

        return super().dispatch(request, *args, **kwargs)


class AdminRequiredMixin(LoginRequiredMixin):
    """
    Enforces authentication AND verifies administrator credentials (is_staff or is_superuser).
    Non-staff users are rejected with an access denied alert and redirected safely.
    """
    login_url = "accounts:login"

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.info(request, "Please sign in with administrator credentials.")
            return self.handle_no_permission()

        if not (request.user.is_staff or request.user.is_superuser):
            messages.error(
                request,
                "Access restricted: Guild Curation & Moderation requires administrator privileges."
            )
            return redirect("accounts:buyer_dashboard")

        return super().dispatch(request, *args, **kwargs)


# ==============================================================================
# CENTRAL DASHBOARD ROUTER
# ==============================================================================

class DashboardRedirectView(LoginRequiredMixin, View):
    """
    Central role-aware dispatcher (/dashboard/). Inspects the active user
    and redirects to their dedicated dashboard (Admin, Seller, or Buyer).
    """
    login_url = "accounts:login"

    def get(self, request):
        if request.user.is_staff or request.user.is_superuser:
            return redirect("accounts:admin_dashboard")
        elif hasattr(request.user, "artisan_profile"):
            return redirect("accounts:seller_dashboard")
        return redirect("accounts:buyer_dashboard")


# ==============================================================================
# AUTHENTICATION & ONBOARDING
# ==============================================================================

class AuthView(View):
    """
    Renders the split-screen minimalist authentication & onboarding portal.
    Handles Sign In and Create Account actions for Buyers and Artisans,
    with automatic role-based routing upon successful authentication.
    """
    template_name = "accounts/auth.html"

    def get(self, request):
        if request.user.is_authenticated:
            if request.user.is_staff or request.user.is_superuser:
                return redirect("accounts:admin_dashboard")
            elif hasattr(request.user, "artisan_profile"):
                return redirect("accounts:seller_dashboard")
            return redirect("accounts:buyer_dashboard")

        action = request.GET.get("action", "login")
        role = request.GET.get("role", "buyer")

        login_form = LoginForm()
        register_form = RegisterForm(initial={"role": role})

        return render(request, self.template_name, {
            "login_form": login_form,
            "register_form": register_form,
            "active_tab": action,
            "active_role": role,
        })

    def post(self, request):
        action = request.POST.get("auth_action", "login")
        role = request.POST.get("role", "buyer")

        if action == "login":
            login_form = LoginForm(request.POST)
            register_form = RegisterForm(initial={"role": role})
            if login_form.is_valid():
                user = login_form.user
                login(request, user)
                messages.success(request, f"Welcome back, {user.first_name or user.username}!")
                next_url = request.GET.get("next") or request.POST.get("next")
                if next_url:
                    return redirect(next_url)

                if user.is_staff or user.is_superuser:
                    return redirect("accounts:admin_dashboard")
                elif hasattr(user, "artisan_profile"):
                    return redirect("accounts:seller_dashboard")
                return redirect("accounts:buyer_dashboard")
            else:
                return render(request, self.template_name, {
                    "login_form": login_form,
                    "register_form": register_form,
                    "active_tab": "login",
                    "active_role": role,
                })

        elif action == "signup":
            register_form = RegisterForm(request.POST)
            login_form = LoginForm()
            if register_form.is_valid():
                username = register_form.cleaned_data["username"]
                email = register_form.cleaned_data["email"]
                full_name = register_form.cleaned_data["full_name"]
                password = register_form.cleaned_data["password"]
                role = register_form.cleaned_data["role"]

                # Create user
                first_name = full_name.split()[0] if full_name else username
                last_name = " ".join(full_name.split()[1:]) if len(full_name.split()) > 1 else ""
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password=password,
                    first_name=first_name,
                    last_name=last_name
                )

                if role == "artisan":
                    speciality = register_form.cleaned_data.get("craft_speciality") or "Traditional Crafts"
                    location = register_form.cleaned_data.get("location") or "India"
                    bio = register_form.cleaned_data.get("bio") or ""
                    ArtisanProfile.objects.create(
                        user=user,
                        display_name=full_name or username,
                        craft_speciality=speciality,
                        location=location,
                        bio=bio,
                        is_approved=True,
                        is_verified=True
                    )
                    login(request, user)
                    messages.success(
                        request,
                        f"Welcome, Master Artisan {full_name or username}! Your studio workspace is ready."
                    )
                    return redirect("accounts:seller_dashboard")
                else:
                    login(request, user)
                    messages.success(
                        request,
                        f"Welcome to CraftConnect, {full_name or username}! Your conscious patron sanctuary is active."
                    )
                    return redirect("accounts:buyer_dashboard")
            else:
                return render(request, self.template_name, {
                    "login_form": login_form,
                    "register_form": register_form,
                    "active_tab": "signup",
                    "active_role": role,
                })

        return redirect("accounts:auth")


class LogoutView(View):
    def get(self, request):
        logout(request)
        messages.info(request, "You have been safely signed out. Until next time!")
        return redirect("marketplace:home")

    def post(self, request):
        logout(request)
        messages.info(request, "You have been safely signed out. Until next time!")
        return redirect("marketplace:home")


# ==============================================================================
# DEDICATED BUYER DASHBOARD
# ==============================================================================

class BuyerDashboardView(BuyerRequiredMixin, View):
    """
    Dedicated dashboard for conscious patrons / buyers.
    Displays saved crafts, sent inquiries to artisans, fair-trade impact metrics,
    and recommended creations.
    """
    template_name = "accounts/buyer_dashboard.html"

    def get(self, request):
        user = request.user
        saved_items = SavedProduct.objects.filter(buyer=user).select_related("product__artisan", "product__category")
        orders = Order.objects.filter(buyer=user).select_related("product__artisan", "product__category").order_by("-created_at")
        enquiries = Enquiry.objects.filter(buyer=user).select_related("product__artisan").order_by("-created_at")

        # Curated recommendations from public catalog
        recommended_products = Product.objects.public().select_related("artisan", "category")[:6]

        saved_count = saved_items.count()
        orders_count = orders.count()
        enquiries_count = enquiries.count()
        total_spent = sum(o.total_price for o in orders)
        artisans_supported_count = (
            orders.values("artisan").distinct().count()
            or enquiries.values("product__artisan").distinct().count()
        )

        context = {
            "user_context": user,
            "saved_items": saved_items,
            "orders": orders,
            "orders_count": orders_count,
            "enquiries": enquiries,
            "recommended_products": recommended_products,
            "saved_count": saved_count,
            "enquiries_count": enquiries_count,
            "total_impact_inr": f"{int(total_spent):,}" if total_spent else (f"{(saved_count * 1250):,}" if saved_count else "0"),
            "artisans_supported_count": artisans_supported_count,
        }
        return render(request, self.template_name, context)


# ==============================================================================
# DEDICATED SELLER DASHBOARD (ARTISAN STUDIO)
# ==============================================================================

class ArtisanStudioView(SellerRequiredMixin, View):
    """
    Dedicated workspace for master artisans and sellers.
    Allows managing inventory, publishing new handcrafted pieces, responding to inquiries,
    and using the AI Storytelling & Listing Assistant.
    """
    template_name = "accounts/artisan_dashboard.html"

    def get(self, request):
        artisan = request.user.artisan_profile

        products_qs = Product.objects.filter(artisan=artisan).select_related("category").order_by("-created_at")
        received_orders = Order.objects.filter(artisan=artisan).select_related("buyer", "product").order_by("-created_at")
        received_enquiries = Enquiry.objects.filter(product__artisan=artisan).select_related("buyer", "product").order_by("-created_at")

        product_form = ArtisanProductForm()
        categories = Category.objects.all()

        total_pieces = products_qs.count()
        live_listings = products_qs.filter(is_approved=True, is_available=True).count()
        pending_moderation = products_qs.filter(is_approved=False).count()
        total_revenue = sum(o.artisan_share for o in received_orders)

        context = {
            "artisan": artisan,
            "products": products_qs,
            "received_orders": received_orders,
            "received_orders_count": received_orders.count(),
            "total_revenue": total_revenue,
            "received_enquiries": received_enquiries,
            "product_form": product_form,
            "categories": categories,
            "total_pieces": total_pieces,
            "live_listings": live_listings,
            "pending_moderation": pending_moderation,
        }
        return render(request, self.template_name, context)

    def post(self, request):
        """Handle new product creation from the studio form."""
        artisan = request.user.artisan_profile

        form = ArtisanProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save(commit=False)
            product.artisan = artisan
            product.is_approved = True
            product.save()
            messages.success(request, f"'{product.title}' has been added to your studio collection!")
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field.capitalize()}: {error}")

        return redirect("accounts:seller_dashboard")


class BecomeArtisanView(BuyerRequiredMixin, View):
    """
    Allows an existing patron/buyer to upgrade their account and create
    an Artisan Studio without having to register a separate account.
    """
    template_name = "accounts/become_artisan.html"

    def get(self, request):
        if hasattr(request.user, "artisan_profile"):
            messages.info(request, "You already have an active Artisan Studio profile!")
            return redirect("accounts:seller_dashboard")

        form = BecomeArtisanForm(initial={
            "display_name": request.user.get_full_name() or request.user.username,
        })
        return render(request, self.template_name, {"form": form})

    def post(self, request):
        if hasattr(request.user, "artisan_profile"):
            return redirect("accounts:seller_dashboard")

        form = BecomeArtisanForm(request.POST, request.FILES)
        if form.is_valid():
            profile = form.save(commit=False)
            profile.user = request.user
            profile.is_approved = True
            profile.is_verified = True
            profile.save()
            messages.success(
                request,
                f"Congratulations, Master Artisan {profile.display_name}! Your Artisan Atelier is now active."
            )
            return redirect("accounts:seller_dashboard")

        return render(request, self.template_name, {"form": form})


class AIAssistantSuggestView(SellerRequiredMixin, View):
    """
    JSON API endpoint for the interactive Artisan Catalogue Assistant.
    Accepts rough artisan notes, material, and category, and returns
    rich AI-generated suggestions for titles, descriptions, categories, and tags.
    """
    def post(self, request):
        try:
            data = json.loads(request.body.decode("utf-8")) if request.body else request.POST
            title = data.get("title", "")
            notes = data.get("notes", "")
            material = data.get("material", "")
            category = data.get("category", "")

            suggestions = generate_catalogue_assistant_suggestions(
                title=title,
                raw_notes=notes,
                material=material,
                category_name=category
            )
            return JsonResponse({"status": "success", "data": suggestions})
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=400)


# ==============================================================================
# DEDICATED ADMIN DASHBOARD (MODERATION & CURATION PORTAL)
# ==============================================================================

class ModerationPortalView(AdminRequiredMixin, View):
    """
    Dedicated dashboard for Guild Administrators and Curators.
    Supervises artisan verification, catalog moderation, audit logs, and platform health.
    """
    template_name = "accounts/moderation.html"

    def get(self, request):
        pending_artisans = ArtisanProfile.objects.filter(is_approved=False).order_by("-created_at")
        approved_artisans = ArtisanProfile.objects.filter(is_approved=True).order_by("-created_at")

        pending_products = Product.objects.filter(is_approved=False).select_related("artisan", "category").order_by("-created_at")
        approved_products = Product.objects.filter(is_approved=True).select_related("artisan", "category").order_by("-created_at")

        total_artisans = ArtisanProfile.objects.count()
        verified_artisans = approved_artisans.count()
        total_products = Product.objects.count()
        pending_submissions = pending_products.count()

        context = {
            "pending_artisans": pending_artisans,
            "approved_artisans": approved_artisans,
            "pending_products": pending_products,
            "approved_products": approved_products,
            "total_artisans": total_artisans,
            "verified_artisans": verified_artisans,
            "total_products": total_products,
            "pending_submissions": pending_submissions,
        }
        return render(request, self.template_name, context)

    def post(self, request):
        action = request.POST.get("action")
        target_type = request.POST.get("type")
        target_id = request.POST.get("id")

        if target_type == "artisan":
            artisan = get_object_or_404(ArtisanProfile, id=target_id)
            if action == "approve":
                artisan.is_approved = True
                artisan.is_verified = True
                artisan.save()
                messages.success(request, f"Artisan '{artisan.display_name}' has been verified and approved.")
            elif action == "reject":
                artisan.is_approved = False
                artisan.save()
                messages.info(request, f"Artisan '{artisan.display_name}' has been marked unapproved.")

        elif target_type == "product":
            product = get_object_or_404(Product, id=target_id)
            if action == "approve":
                product.is_approved = True
                product.save()
                messages.success(request, f"Product '{product.title}' has been approved for public discovery.")
            elif action == "reject":
                product.is_approved = False
                product.save()
                messages.info(request, f"Product '{product.title}' has been set to unapproved.")

        return redirect("accounts:admin_dashboard")


# ==============================================================================
# PUBLIC ARTISAN SHOWCASE
# ==============================================================================

class ArtisanDetailView(DetailView):
    """
    Public artisan studio showcase. Displays the artisan's bio,
    location, craft speciality, verification badge, and approved public pieces.
    """
    model = ArtisanProfile
    template_name = "accounts/artisan_detail.html"
    context_object_name = "artisan"
    pk_url_kwarg = "pk"

    def get_queryset(self):
        return ArtisanProfile.objects.filter(is_approved=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["creations"] = Product.objects.public().filter(artisan=self.object)
        return context
