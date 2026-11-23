"""
Comprehensive Test Suite — accounts app
========================================
Covers:
  • ArtisanProfile model (creation, defaults, relationships, __str__, Meta)
  • LoginForm (valid, invalid, email-based login, remember_me)
  • RegisterForm (buyer path, artisan path, duplicate username/email, artisan
    without speciality)
  • BecomeArtisanForm (valid, missing required fields)
  • ArtisanProductForm (valid, missing required fields)
  • RBAC Mixins (BuyerRequiredMixin, SellerRequiredMixin, AdminRequiredMixin)
  • DashboardRedirectView (central role-based routing for all three roles)
  • AuthView (GET, POST login, POST signup for buyer & artisan, next redirect,
    already-authenticated redirect)
  • LogoutView (GET, POST)
  • BuyerDashboardView (context data, metrics, recommendations)
  • ArtisanStudioView (GET context, POST product creation)
  • BecomeArtisanView (GET, POST, already-artisan guard)
  • AIAssistantSuggestView (POST JSON, error handling)
  • ModerationPortalView (GET context, POST approve/reject artisan/product)
  • ArtisanDetailView (public, unapproved returns 404)
"""

from decimal import Decimal
import json
from unittest.mock import patch

from django.test import TestCase, RequestFactory
from django.contrib.auth.models import User
from django.urls import reverse

from .models import ArtisanProfile
from .forms import LoginForm, RegisterForm, BecomeArtisanForm, ArtisanProductForm
from marketplace.models import Category, Product, Order, SavedProduct, Enquiry


# =============================================================================
# MODEL TESTS
# =============================================================================

class ArtisanProfileModelTests(TestCase):
    """Tests for the ArtisanProfile model."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="priyamvada",
            email="priyamvada@example.com",
            password="securepassword123"
        )
        self.profile = ArtisanProfile.objects.create(
            user=self.user,
            display_name="Avani Earthenware",
            bio="Third-generation terracotta potter specializing in wheel-thrown kitchenware.",
            location="Jaipur, Rajasthan",
            craft_speciality="Terracotta Pottery"
        )

    def test_artisan_profile_relationship(self):
        """Verify OneToOne relationship between User and ArtisanProfile."""
        self.assertEqual(self.user.artisan_profile, self.profile)
        self.assertEqual(self.profile.user.username, "priyamvada")

    def test_default_approval_and_verification_flags(self):
        """New artisan profiles should default to unapproved and unverified."""
        self.assertFalse(self.profile.is_approved)
        self.assertFalse(self.profile.is_verified)

    def test_artisan_string_representation(self):
        """__str__ should format display name and craft speciality."""
        expected = "Avani Earthenware (Terracotta Pottery)"
        self.assertEqual(str(self.profile), expected)

    def test_artisan_profile_ordering(self):
        """Profiles should be ordered by -created_at (Meta.ordering)."""
        self.assertEqual(ArtisanProfile._meta.ordering, ["-created_at"])

    def test_artisan_profile_verbose_name(self):
        """Meta verbose name is 'Artisan Profile'."""
        self.assertEqual(ArtisanProfile._meta.verbose_name, "Artisan Profile")
        self.assertEqual(ArtisanProfile._meta.verbose_name_plural, "Artisan Profiles")

    def test_artisan_profile_image_blank_null(self):
        """profile_image can be null/blank."""
        self.assertIsNone(self.profile.profile_image.name or None)

    def test_timestamps_auto_populated(self):
        """created_at and updated_at should be auto-set."""
        self.assertIsNotNone(self.profile.created_at)
        self.assertIsNotNone(self.profile.updated_at)

    def test_artisan_with_approval(self):
        """Can create an approved and verified artisan."""
        user2 = User.objects.create_user(username="approved_one", password="pass1234")
        profile = ArtisanProfile.objects.create(
            user=user2,
            display_name="Approved Studio",
            craft_speciality="Handloom",
            is_approved=True,
            is_verified=True
        )
        self.assertTrue(profile.is_approved)
        self.assertTrue(profile.is_verified)


# =============================================================================
# FORM TESTS
# =============================================================================

class LoginFormTests(TestCase):
    """Tests for the LoginForm."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            email="testuser@example.com",
            password="correctpassword"
        )

    def test_valid_login_by_username(self):
        """Valid credentials by username should authenticate."""
        form = LoginForm(data={"username": "testuser", "password": "correctpassword"})
        self.assertTrue(form.is_valid())
        self.assertEqual(form.user, self.user)

    def test_valid_login_by_email(self):
        """Valid credentials by email should authenticate."""
        form = LoginForm(data={"username": "testuser@example.com", "password": "correctpassword"})
        self.assertTrue(form.is_valid())
        self.assertEqual(form.user, self.user)

    def test_invalid_password(self):
        """Wrong password should make form invalid."""
        form = LoginForm(data={"username": "testuser", "password": "wrongpassword"})
        self.assertFalse(form.is_valid())
        self.assertIn("__all__", form.errors)

    def test_nonexistent_user(self):
        """Nonexistent user should make form invalid."""
        form = LoginForm(data={"username": "nobody", "password": "anything"})
        self.assertFalse(form.is_valid())

    def test_empty_fields(self):
        """Empty fields should make form invalid."""
        form = LoginForm(data={"username": "", "password": ""})
        self.assertFalse(form.is_valid())

    def test_remember_me_defaults_true(self):
        """remember_me field defaults to True."""
        form = LoginForm()
        self.assertTrue(form.fields["remember_me"].initial)

    def test_invalid_email_format_in_login(self):
        """Entering malformed email in login username field should fail validation."""
        form = LoginForm(data={"username": "bademail@notreal", "password": "password123"})
        self.assertFalse(form.is_valid())
        self.assertIn("__all__", form.errors)


class RegisterFormTests(TestCase):
    """Tests for the RegisterForm."""

    def test_valid_buyer_registration(self):
        """Buyer registration with all valid fields."""
        form = RegisterForm(data={
            "role": "buyer",
            "username": "new_buyer",
            "email": "new_buyer@example.com",
            "full_name": "Priya Sharma",
            "password": "securepass123",
        })
        self.assertTrue(form.is_valid())

    def test_valid_artisan_registration(self):
        """Artisan registration with speciality."""
        form = RegisterForm(data={
            "role": "artisan",
            "username": "new_artisan",
            "email": "new_artisan@example.com",
            "full_name": "Ramesh Prajapati",
            "password": "securepass123",
            "craft_speciality": "Terracotta Pottery",
            "location": "Gorakhpur, UP",
            "bio": "Master potter",
        })
        self.assertTrue(form.is_valid())

    def test_artisan_without_speciality_invalid(self):
        """Artisan registration without craft_speciality should fail."""
        form = RegisterForm(data={
            "role": "artisan",
            "username": "artisan_no_spec",
            "email": "nospec@example.com",
            "full_name": "No Spec Artisan",
            "password": "securepass123",
            "craft_speciality": "",
        })
        self.assertFalse(form.is_valid())
        self.assertIn("craft_speciality", form.errors)

    def test_duplicate_username_rejected(self):
        """Duplicate username should be rejected."""
        User.objects.create_user(username="existing_user", password="pass")
        form = RegisterForm(data={
            "role": "buyer",
            "username": "existing_user",
            "email": "unique@example.com",
            "full_name": "Someone",
            "password": "pass1234",
        })
        self.assertFalse(form.is_valid())
        self.assertIn("username", form.errors)

    def test_duplicate_email_rejected(self):
        """Duplicate email should be rejected."""
        User.objects.create_user(username="user1", email="taken@example.com", password="pass")
        form = RegisterForm(data={
            "role": "buyer",
            "username": "user2",
            "email": "taken@example.com",
            "full_name": "Someone",
            "password": "pass1234",
        })
        self.assertFalse(form.is_valid())
        self.assertIn("email", form.errors)

    def test_email_normalized_to_lowercase(self):
        """Email should be normalized to lowercase."""
        form = RegisterForm(data={
            "role": "buyer",
            "username": "casetest",
            "email": "TestCase@Example.COM",
            "full_name": "Case Test",
            "password": "pass1234",
        })
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data["email"], "testcase@example.com")

    def test_full_name_with_numbers_rejected(self):
        """Full name containing numbers should be rejected."""
        form = RegisterForm(data={
            "role": "buyer",
            "username": "user_num",
            "email": "user_num@example.com",
            "full_name": "Ramesh123 Kumar",
            "password": "securepass123",
        })
        self.assertFalse(form.is_valid())
        self.assertIn("full_name", form.errors)

    def test_full_name_with_symbols_rejected(self):
        """Full name containing symbols should be rejected."""
        form = RegisterForm(data={
            "role": "buyer",
            "username": "user_sym",
            "email": "user_sym@example.com",
            "full_name": "User@Admin!",
            "password": "securepass123",
        })
        self.assertFalse(form.is_valid())
        self.assertIn("full_name", form.errors)

    def test_full_name_valid_letters_and_spaces(self):
        """Full name with letters, spaces, hyphens, and apostrophes should be valid."""
        form = RegisterForm(data={
            "role": "buyer",
            "username": "user_valid",
            "email": "user_valid@example.com",
            "full_name": "Mary-Jane O'Connor",
            "password": "securepass123",
        })
        self.assertTrue(form.is_valid())

    def test_invalid_email_format_rejected(self):
        """Invalid email formats should be rejected."""
        invalid_emails = ["notanemail", "user@", "user@domain", "user@.com", "user@domain..com"]
        for bad_email in invalid_emails:
            form = RegisterForm(data={
                "role": "buyer",
                "username": f"user_{hash(bad_email)}",
                "email": bad_email,
                "full_name": "Valid Name",
                "password": "securepass123",
            })
            self.assertFalse(form.is_valid(), f"Email '{bad_email}' should be rejected as invalid")
            self.assertIn("email", form.errors)

    def test_indian_phone_number_valid(self):
        """Indian phone (+91) with 10 digits starting with 6-9 should be valid."""
        form = RegisterForm(data={
            "role": "buyer",
            "username": "buyer_phone_in",
            "email": "phone_in@example.com",
            "full_name": "Aarav Sharma",
            "country_code": "+91",
            "phone_number": "9876543210",
            "password": "securepass123",
        })
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data["phone_number"], "9876543210")

    def test_indian_phone_number_invalid_length(self):
        """Indian phone (+91) with less or more than 10 digits should be rejected."""
        form = RegisterForm(data={
            "role": "buyer",
            "username": "buyer_short_phone",
            "email": "short_phone@example.com",
            "full_name": "Aarav Sharma",
            "country_code": "+91",
            "phone_number": "98765432",
            "password": "securepass123",
        })
        self.assertFalse(form.is_valid())
        self.assertIn("phone_number", form.errors)

    def test_indian_phone_number_invalid_starting_digit(self):
        """Indian phone (+91) starting with 1, 2, 3, 4, 5 should be rejected."""
        form = RegisterForm(data={
            "role": "buyer",
            "username": "buyer_bad_prefix",
            "email": "bad_prefix@example.com",
            "full_name": "Aarav Sharma",
            "country_code": "+91",
            "phone_number": "2876543210",
            "password": "securepass123",
        })
        self.assertFalse(form.is_valid())
        self.assertIn("phone_number", form.errors)

    def test_us_phone_number_valid(self):
        """US phone (+1) with 10 digits should be valid."""
        form = RegisterForm(data={
            "role": "buyer",
            "username": "buyer_phone_us",
            "email": "phone_us@example.com",
            "full_name": "John Doe",
            "country_code": "+1",
            "phone_number": "5551234567",
            "password": "securepass123",
        })
        self.assertTrue(form.is_valid(), form.errors)

    def test_us_phone_number_invalid_length(self):
        """US phone (+1) with less than 10 digits should be rejected."""
        form = RegisterForm(data={
            "role": "buyer",
            "username": "buyer_phone_us_short",
            "email": "us_short@example.com",
            "full_name": "John Doe",
            "country_code": "+1",
            "phone_number": "5551234",
            "password": "securepass123",
        })
        self.assertFalse(form.is_valid())
        self.assertIn("phone_number", form.errors)


class BecomeArtisanFormTests(TestCase):
    """Tests for BecomeArtisanForm."""

    def test_valid_become_artisan_form(self):
        """Valid data should pass validation."""
        form = BecomeArtisanForm(data={
            "display_name": "Priya Handlooms",
            "craft_speciality": "Chanderi Weaving",
            "location": "Chanderi, MP",
            "bio": "Handspun organic cotton saris.",
        })
        self.assertTrue(form.is_valid())

    def test_missing_required_display_name(self):
        """Missing display_name should fail."""
        form = BecomeArtisanForm(data={
            "display_name": "",
            "craft_speciality": "Weaving",
        })
        self.assertFalse(form.is_valid())
        self.assertIn("display_name", form.errors)

    def test_missing_required_craft_speciality(self):
        """Missing craft_speciality should fail."""
        form = BecomeArtisanForm(data={
            "display_name": "Some Studio",
            "craft_speciality": "",
        })
        self.assertFalse(form.is_valid())
        self.assertIn("craft_speciality", form.errors)


class ArtisanProductFormTests(TestCase):
    """Tests for ArtisanProductForm."""

    def setUp(self):
        self.category = Category.objects.create(name="Ceramics", slug="ceramics")

    def test_valid_product_form(self):
        """Valid product data should pass."""
        form = ArtisanProductForm(data={
            "title": "Terracotta Vase",
            "category": self.category.pk,
            "description": "A beautiful handmade terracotta vase.",
            "price": "1500.00",
            "stock_quantity": 10,
            "is_available": True,
        })
        self.assertTrue(form.is_valid())

    def test_missing_title_invalid(self):
        """Missing title should fail."""
        form = ArtisanProductForm(data={
            "title": "",
            "category": self.category.pk,
            "description": "Description.",
            "price": "1500.00",
            "stock_quantity": 10,
        })
        self.assertFalse(form.is_valid())
        self.assertIn("title", form.errors)

    def test_negative_price_invalid(self):
        """Negative price should fail validators."""
        form = ArtisanProductForm(data={
            "title": "Negative Price Product",
            "category": self.category.pk,
            "description": "Description.",
            "price": "-100.00",
            "stock_quantity": 10,
        })
        self.assertFalse(form.is_valid())
        self.assertIn("price", form.errors)


# =============================================================================
# VIEW TESTS — AUTHENTICATION & ONBOARDING
# =============================================================================

class AuthViewTests(TestCase):
    """Tests for the AuthView (login/register portal)."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="authtest",
            email="auth@example.com",
            password="password123",
            first_name="Auth"
        )

    def test_get_auth_page(self):
        """GET /accounts/login/ should render the auth template."""
        response = self.client.get(reverse("accounts:login"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "accounts/auth.html")
        self.assertIn("login_form", response.context)
        self.assertIn("register_form", response.context)

    def test_get_auth_defaults_to_login_tab(self):
        """Default active_tab should be 'login'."""
        response = self.client.get(reverse("accounts:login"))
        self.assertEqual(response.context["active_tab"], "login")

    def test_get_auth_with_action_signup(self):
        """action=signup should set active_tab to signup."""
        response = self.client.get(reverse("accounts:auth") + "?action=signup")
        self.assertEqual(response.context["active_tab"], "signup")

    def test_authenticated_buyer_redirected_from_auth(self):
        """Already logged-in buyer should be redirected to buyer dashboard."""
        self.client.login(username="authtest", password="password123")
        response = self.client.get(reverse("accounts:login"))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("accounts:buyer_dashboard"))

    def test_authenticated_staff_redirected_to_admin(self):
        """Staff user should be redirected to admin dashboard."""
        self.user.is_staff = True
        self.user.save()
        self.client.login(username="authtest", password="password123")
        response = self.client.get(reverse("accounts:login"))
        self.assertRedirects(response, reverse("accounts:admin_dashboard"))

    def test_authenticated_artisan_redirected_to_studio(self):
        """Artisan should be redirected to seller dashboard."""
        ArtisanProfile.objects.create(
            user=self.user, display_name="Studio", craft_speciality="Pottery",
            is_approved=True
        )
        self.client.login(username="authtest", password="password123")
        response = self.client.get(reverse("accounts:login"))
        self.assertRedirects(response, reverse("accounts:seller_dashboard"))

    def test_post_login_valid(self):
        """Valid login POST should authenticate and redirect."""
        response = self.client.post(reverse("accounts:login"), {
            "auth_action": "login",
            "username": "authtest",
            "password": "password123",
        })
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("accounts:buyer_dashboard"))

    def test_post_login_invalid(self):
        """Invalid login POST should re-render with errors."""
        response = self.client.post(reverse("accounts:login"), {
            "auth_action": "login",
            "username": "authtest",
            "password": "wrong",
        })
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "accounts/auth.html")

    def test_post_login_with_next(self):
        """Login with ?next= should redirect to that URL."""
        response = self.client.post(
            reverse("accounts:login") + "?next=/catalogue/",
            {"auth_action": "login", "username": "authtest", "password": "password123"}
        )
        self.assertRedirects(response, "/catalogue/", fetch_redirect_response=False)

    def test_post_signup_buyer(self):
        """Buyer signup should create user, login, and redirect to buyer dashboard."""
        response = self.client.post(reverse("accounts:login"), {
            "auth_action": "signup",
            "role": "buyer",
            "username": "new_buyer",
            "email": "new_buyer@test.com",
            "full_name": "New Buyer",
            "password": "strongpass123",
        })
        self.assertRedirects(response, reverse("accounts:buyer_dashboard"))
        self.assertTrue(User.objects.filter(username="new_buyer").exists())
        user = User.objects.get(username="new_buyer")
        self.assertEqual(user.first_name, "New")
        self.assertEqual(user.last_name, "Buyer")
        self.assertFalse(hasattr(user, "artisan_profile"))

    def test_post_signup_artisan(self):
        """Artisan signup should create user + ArtisanProfile and redirect to studio."""
        response = self.client.post(reverse("accounts:login"), {
            "auth_action": "signup",
            "role": "artisan",
            "username": "new_artisan",
            "email": "new_artisan@test.com",
            "full_name": "New Artisan",
            "password": "strongpass123",
            "craft_speciality": "Pottery",
            "location": "Jaipur",
        })
        self.assertRedirects(response, reverse("accounts:seller_dashboard"))
        user = User.objects.get(username="new_artisan")
        self.assertTrue(hasattr(user, "artisan_profile"))
        self.assertTrue(user.artisan_profile.is_approved)
        self.assertTrue(user.artisan_profile.is_verified)

    def test_post_signup_invalid_form(self):
        """Invalid signup should re-render with errors."""
        # Duplicate username
        response = self.client.post(reverse("accounts:login"), {
            "auth_action": "signup",
            "role": "buyer",
            "username": "authtest",  # already exists
            "email": "unique@test.com",
            "full_name": "Someone",
            "password": "pass1234",
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["active_tab"], "signup")

    def test_post_unknown_action_redirects(self):
        """Unknown auth_action should redirect to auth page."""
        response = self.client.post(reverse("accounts:login"), {
            "auth_action": "unknown",
        })
        self.assertRedirects(response, reverse("accounts:auth"))


class LogoutViewTests(TestCase):
    """Tests for LogoutView."""

    def setUp(self):
        self.user = User.objects.create_user(username="logoutuser", password="pass123")

    def test_get_logout(self):
        """GET logout should log out and redirect to home."""
        self.client.login(username="logoutuser", password="pass123")
        response = self.client.get(reverse("accounts:logout"))
        self.assertRedirects(response, reverse("marketplace:home"))
        # Verify logged out
        response2 = self.client.get(reverse("accounts:buyer_dashboard"))
        self.assertEqual(response2.status_code, 302)

    def test_post_logout(self):
        """POST logout should also work."""
        self.client.login(username="logoutuser", password="pass123")
        response = self.client.post(reverse("accounts:logout"))
        self.assertRedirects(response, reverse("marketplace:home"))


# =============================================================================
# VIEW TESTS — RBAC MIXINS & DASHBOARD ROUTING
# =============================================================================

class RoleBasedAuthenticationTests(TestCase):
    """Tests for RBAC mixins and DashboardRedirectView."""

    def setUp(self):
        # 1. Pure Buyer (No ArtisanProfile, not staff)
        self.buyer_user = User.objects.create_user(
            username="buyer_priya", email="priya@example.com", password="password123"
        )
        # 2. Artisan / Seller
        self.seller_user = User.objects.create_user(
            username="artisan_devraj", email="devraj@example.com", password="password123"
        )
        self.artisan_profile = ArtisanProfile.objects.create(
            user=self.seller_user, display_name="Kutch Clay Works",
            bio="Terracotta clay artisan", location="Bhuj, Gujarat",
            craft_speciality="Pottery", is_approved=True, is_verified=True
        )
        # 3. Admin / Staff
        self.admin_user = User.objects.create_user(
            username="staff_curator", email="curator@craftconnect.org",
            password="password123", is_staff=True
        )

    def test_anonymous_redirected_from_all_dashboards(self):
        """Unauthenticated visitors must be redirected to auth portal."""
        for url in ["/accounts/buyer/", "/accounts/seller/",
                     "/accounts/admin-portal/", "/accounts/dashboard/"]:
            response = self.client.get(url)
            self.assertEqual(response.status_code, 302, f"Failed for {url}")
            self.assertTrue(
                response.url.startswith("/accounts/login/")
                or response.url.startswith("/accounts/auth/")
                or response.url.startswith("/login/"),
                f"Unexpected redirect for {url}: {response.url}"
            )

    def test_buyer_access_buyer_dashboard(self):
        """Buyer should have clean access to Buyer Sanctuary."""
        self.client.login(username="buyer_priya", password="password123")
        response = self.client.get("/accounts/buyer/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Buyer / Patron Workspace")

    def test_buyer_redirected_to_become_artisan_when_accessing_seller_studio(self):
        """A buyer accessing seller studio is guided to become-artisan."""
        self.client.login(username="buyer_priya", password="password123")
        response = self.client.get("/accounts/seller/")
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, "/accounts/become-artisan/")

    def test_buyer_denied_admin_portal(self):
        """Regular buyers cannot access admin portal."""
        self.client.login(username="buyer_priya", password="password123")
        response = self.client.get("/accounts/admin-portal/")
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, "/accounts/buyer/")

    def test_seller_access_seller_dashboard(self):
        """Artisans should have clean access to their Studio."""
        self.client.login(username="artisan_devraj", password="password123")
        response = self.client.get("/accounts/seller/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Seller / Artisan Studio Workspace")
        self.assertContains(response, "Kutch Clay Works")

    def test_staff_access_admin_portal(self):
        """Staff should access Guild Moderation Portal."""
        self.client.login(username="staff_curator", password="password123")
        response = self.client.get("/accounts/admin-portal/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Admin &amp; Staff Curator Portal")

    def test_central_dashboard_routing_staff(self):
        """Staff → Admin Portal."""
        self.client.login(username="staff_curator", password="password123")
        response = self.client.get("/accounts/dashboard/")
        self.assertRedirects(response, "/accounts/admin-portal/")

    def test_central_dashboard_routing_seller(self):
        """Seller → Seller Studio."""
        self.client.login(username="artisan_devraj", password="password123")
        response = self.client.get("/accounts/dashboard/")
        self.assertRedirects(response, "/accounts/seller/")

    def test_central_dashboard_routing_buyer(self):
        """Buyer → Buyer Sanctuary."""
        self.client.login(username="buyer_priya", password="password123")
        response = self.client.get("/accounts/dashboard/")
        self.assertRedirects(response, "/accounts/buyer/")

    def test_superuser_routes_to_admin_portal(self):
        """Superuser should be treated as admin."""
        su = User.objects.create_superuser(
            username="superadmin", email="super@test.com", password="pass123"
        )
        self.client.login(username="superadmin", password="pass123")
        response = self.client.get("/accounts/dashboard/")
        self.assertRedirects(response, "/accounts/admin-portal/")


# =============================================================================
# VIEW TESTS — BUYER DASHBOARD
# =============================================================================

class BuyerDashboardViewTests(TestCase):
    """Tests for BuyerDashboardView context and metrics."""

    def setUp(self):
        self.buyer = User.objects.create_user(
            username="buyer1", email="buyer1@test.com", password="pass123"
        )
        self.artisan_user = User.objects.create_user(username="artisan1", password="pass123")
        self.artisan = ArtisanProfile.objects.create(
            user=self.artisan_user, display_name="Test Studio",
            craft_speciality="Pottery", is_approved=True
        )
        self.category = Category.objects.create(name="Ceramics", slug="ceramics")
        self.product = Product.objects.create(
            artisan=self.artisan, category=self.category,
            title="Test Vase", description="Desc",
            price=Decimal("1000.00"), stock_quantity=5,
            is_approved=True, is_available=True
        )

    def test_buyer_dashboard_context_keys(self):
        """Dashboard context should contain all expected keys."""
        self.client.login(username="buyer1", password="pass123")
        response = self.client.get(reverse("accounts:buyer_dashboard"))
        self.assertEqual(response.status_code, 200)
        for key in ["user_context", "saved_items", "orders", "enquiries",
                     "recommended_products", "saved_count", "orders_count",
                     "enquiries_count", "total_impact_inr", "artisans_supported_count"]:
            self.assertIn(key, response.context, f"Missing key: {key}")

    def test_buyer_dashboard_with_order(self):
        """Dashboard should count orders and compute metrics."""
        self.client.login(username="buyer1", password="pass123")
        Order.objects.create(
            buyer=self.buyer, product=self.product, artisan=self.artisan,
            quantity=1, unit_price=Decimal("1000.00"),
            total_price=Decimal("1000.00"), artisan_share=Decimal("880.00"),
            shipping_address="123 Street"
        )
        response = self.client.get(reverse("accounts:buyer_dashboard"))
        self.assertEqual(response.context["orders_count"], 1)
        self.assertEqual(response.context["artisans_supported_count"], 1)

    def test_buyer_dashboard_with_saved_items(self):
        """Should show saved products."""
        self.client.login(username="buyer1", password="pass123")
        SavedProduct.objects.create(buyer=self.buyer, product=self.product)
        response = self.client.get(reverse("accounts:buyer_dashboard"))
        self.assertEqual(response.context["saved_count"], 1)


# =============================================================================
# VIEW TESTS — ARTISAN STUDIO
# =============================================================================

class ArtisanStudioViewTests(TestCase):
    """Tests for ArtisanStudioView GET and POST."""

    def setUp(self):
        self.artisan_user = User.objects.create_user(
            username="studio_artisan", password="pass123"
        )
        self.artisan = ArtisanProfile.objects.create(
            user=self.artisan_user, display_name="Studio Artisan",
            craft_speciality="Metalwork", is_approved=True
        )
        self.category = Category.objects.create(name="Metalcraft", slug="metalcraft")

    def test_studio_get_context(self):
        """GET should render studio template with expected context."""
        self.client.login(username="studio_artisan", password="pass123")
        response = self.client.get(reverse("accounts:seller_dashboard"))
        self.assertEqual(response.status_code, 200)
        for key in ["artisan", "products", "received_orders", "product_form",
                     "categories", "total_pieces", "live_listings", "pending_moderation"]:
            self.assertIn(key, response.context, f"Missing key: {key}")

    def test_studio_post_create_product(self):
        """POST should create a new product."""
        self.client.login(username="studio_artisan", password="pass123")
        response = self.client.post(reverse("accounts:seller_dashboard"), {
            "title": "Bronze Diya",
            "category": self.category.pk,
            "description": "Hand-cast bronze diya.",
            "price": "2000.00",
            "stock_quantity": 5,
            "is_available": True,
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Product.objects.filter(title="Bronze Diya").exists())
        product = Product.objects.get(title="Bronze Diya")
        self.assertEqual(product.artisan, self.artisan)
        self.assertTrue(product.is_approved)

    def test_studio_post_invalid_form(self):
        """Invalid POST should redirect with error messages."""
        self.client.login(username="studio_artisan", password="pass123")
        response = self.client.post(reverse("accounts:seller_dashboard"), {
            "title": "",  # missing
            "category": self.category.pk,
            "description": "Desc",
            "price": "100.00",
        })
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Product.objects.filter(description="Desc").exists())


# =============================================================================
# VIEW TESTS — BECOME ARTISAN
# =============================================================================

class BecomeArtisanViewTests(TestCase):
    """Tests for BecomeArtisanView."""

    def setUp(self):
        self.buyer = User.objects.create_user(
            username="buyer_upgrade", password="pass123",
            first_name="Priya", last_name="S"
        )

    def test_get_become_artisan(self):
        """GET renders the form."""
        self.client.login(username="buyer_upgrade", password="pass123")
        response = self.client.get(reverse("accounts:become_artisan"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Open Your Artisan Atelier")

    def test_post_become_artisan(self):
        """POST creates ArtisanProfile and redirects to studio."""
        self.client.login(username="buyer_upgrade", password="pass123")
        response = self.client.post(reverse("accounts:become_artisan"), {
            "display_name": "Priya Handlooms",
            "craft_speciality": "Chanderi Weaving",
            "location": "Chanderi, MP",
            "bio": "Traditional weaving."
        })
        self.assertRedirects(response, reverse("accounts:seller_dashboard"))
        self.buyer.refresh_from_db()
        self.assertTrue(hasattr(self.buyer, "artisan_profile"))
        self.assertEqual(self.buyer.artisan_profile.display_name, "Priya Handlooms")
        self.assertTrue(self.buyer.artisan_profile.is_approved)

    def test_already_artisan_redirected(self):
        """Already-artisan user should be redirected from become-artisan."""
        ArtisanProfile.objects.create(
            user=self.buyer, display_name="Existing",
            craft_speciality="Pottery", is_approved=True
        )
        self.client.login(username="buyer_upgrade", password="pass123")
        response = self.client.get(reverse("accounts:become_artisan"))
        self.assertRedirects(response, reverse("accounts:seller_dashboard"))

    def test_post_already_artisan_redirected(self):
        """POST by already-artisan should redirect without creating duplicate."""
        ArtisanProfile.objects.create(
            user=self.buyer, display_name="Existing",
            craft_speciality="Pottery", is_approved=True
        )
        self.client.login(username="buyer_upgrade", password="pass123")
        response = self.client.post(reverse("accounts:become_artisan"), {
            "display_name": "Duplicate",
            "craft_speciality": "Weaving",
        })
        self.assertRedirects(response, reverse("accounts:seller_dashboard"))
        self.assertEqual(ArtisanProfile.objects.filter(user=self.buyer).count(), 1)


# =============================================================================
# VIEW TESTS — AI ASSISTANT
# =============================================================================

class AIAssistantSuggestViewTests(TestCase):
    """Tests for AIAssistantSuggestView."""

    def setUp(self):
        self.artisan_user = User.objects.create_user(
            username="ai_artisan", password="pass123"
        )
        self.artisan = ArtisanProfile.objects.create(
            user=self.artisan_user, display_name="AI Studio",
            craft_speciality="Pottery", is_approved=True
        )

    def test_unauthenticated_rejected(self):
        """Unauthenticated user should be redirected."""
        response = self.client.post(reverse("accounts:ai_assistant_suggest"))
        self.assertEqual(response.status_code, 302)

    def test_buyer_without_profile_rejected(self):
        """Buyer without ArtisanProfile should be redirected."""
        buyer = User.objects.create_user(username="plain_buyer", password="pass123")
        self.client.login(username="plain_buyer", password="pass123")
        response = self.client.post(reverse("accounts:ai_assistant_suggest"))
        self.assertEqual(response.status_code, 302)

    @patch("accounts.views.generate_catalogue_assistant_suggestions")
    def test_valid_post_returns_json(self, mock_suggest):
        """Artisan submitting valid data should get JSON response."""
        mock_suggest.return_value = {
            "suggested_title": "Wheel-Thrown Clay Pot",
            "suggested_description": "Crafted with care.",
            "suggested_category": "Ceramics & Terracotta",
            "suggested_tags": "clay, pot",
            "suggested_price": "1200.00",
            "confidence_score": 98.2,
        }
        self.client.login(username="ai_artisan", password="pass123")
        response = self.client.post(
            reverse("accounts:ai_assistant_suggest"),
            data=json.dumps({"title": "Clay Pot", "notes": "Terracotta",
                             "material": "Clay", "category": "Ceramics"}),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "success")
        self.assertIn("data", data)
        self.assertEqual(data["data"]["suggested_title"], "Wheel-Thrown Clay Pot")


# =============================================================================
# VIEW TESTS — MODERATION PORTAL
# =============================================================================

class ModerationPortalViewTests(TestCase):
    """Tests for ModerationPortalView."""

    def setUp(self):
        self.admin_user = User.objects.create_user(
            username="mod_admin", password="pass123", is_staff=True
        )
        self.artisan_user = User.objects.create_user(
            username="mod_artisan", password="pass123"
        )
        self.artisan = ArtisanProfile.objects.create(
            user=self.artisan_user, display_name="Pending Artisan",
            craft_speciality="Pottery", is_approved=False
        )
        self.category = Category.objects.create(name="Ceramics", slug="ceramics-mod")
        self.product = Product.objects.create(
            artisan=self.artisan, category=self.category,
            title="Pending Product", description="Desc",
            price=Decimal("500.00"), stock_quantity=5,
            is_approved=False, is_available=True
        )

    def test_moderation_get_context(self):
        """GET should display pending items."""
        self.client.login(username="mod_admin", password="pass123")
        response = self.client.get(reverse("accounts:admin_dashboard"))
        self.assertEqual(response.status_code, 200)
        for key in ["pending_artisans", "approved_artisans", "pending_products",
                     "approved_products", "total_artisans", "total_products"]:
            self.assertIn(key, response.context)

    def test_approve_artisan(self):
        """POST approve artisan should set is_approved=True."""
        self.client.login(username="mod_admin", password="pass123")
        response = self.client.post(reverse("accounts:admin_dashboard"), {
            "action": "approve", "type": "artisan", "id": self.artisan.pk
        })
        self.assertRedirects(response, reverse("accounts:admin_dashboard"))
        self.artisan.refresh_from_db()
        self.assertTrue(self.artisan.is_approved)
        self.assertTrue(self.artisan.is_verified)

    def test_reject_artisan(self):
        """POST reject artisan should set is_approved=False."""
        self.artisan.is_approved = True
        self.artisan.save()
        self.client.login(username="mod_admin", password="pass123")
        self.client.post(reverse("accounts:admin_dashboard"), {
            "action": "reject", "type": "artisan", "id": self.artisan.pk
        })
        self.artisan.refresh_from_db()
        self.assertFalse(self.artisan.is_approved)

    def test_approve_product(self):
        """POST approve product should set is_approved=True."""
        self.client.login(username="mod_admin", password="pass123")
        self.client.post(reverse("accounts:admin_dashboard"), {
            "action": "approve", "type": "product", "id": self.product.pk
        })
        self.product.refresh_from_db()
        self.assertTrue(self.product.is_approved)

    def test_reject_product(self):
        """POST reject product should set is_approved=False."""
        self.product.is_approved = True
        self.product.save()
        self.client.login(username="mod_admin", password="pass123")
        self.client.post(reverse("accounts:admin_dashboard"), {
            "action": "reject", "type": "product", "id": self.product.pk
        })
        self.product.refresh_from_db()
        self.assertFalse(self.product.is_approved)


# =============================================================================
# VIEW TESTS — PUBLIC ARTISAN DETAIL
# =============================================================================

class ArtisanDetailViewTests(TestCase):
    """Tests for ArtisanDetailView."""

    def setUp(self):
        self.artisan_user = User.objects.create_user(username="pub_artisan", password="pass")
        self.approved_artisan = ArtisanProfile.objects.create(
            user=self.artisan_user, display_name="Public Studio",
            craft_speciality="Pottery", is_approved=True
        )

    def test_approved_artisan_public_page(self):
        """Approved artisan page should return 200."""
        response = self.client.get(
            reverse("accounts:artisan_detail", kwargs={"pk": self.approved_artisan.pk})
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Public Studio")

    def test_unapproved_artisan_returns_404(self):
        """Unapproved artisan detail should return 404."""
        unapproved_user = User.objects.create_user(username="hidden_artisan", password="pass")
        unapproved = ArtisanProfile.objects.create(
            user=unapproved_user, display_name="Hidden Studio",
            craft_speciality="Pottery", is_approved=False
        )
        response = self.client.get(
            reverse("accounts:artisan_detail", kwargs={"pk": unapproved.pk})
        )
        self.assertEqual(response.status_code, 404)

    def test_artisan_detail_shows_creations(self):
        """Artisan detail page should include their public products."""
        category = Category.objects.create(name="Ceramics", slug="ceramics-det")
        Product.objects.create(
            artisan=self.approved_artisan, category=category,
            title="Display Vase", description="A vase.",
            price=Decimal("1000.00"), stock_quantity=5,
            is_approved=True, is_available=True
        )
        response = self.client.get(
            reverse("accounts:artisan_detail", kwargs={"pk": self.approved_artisan.pk})
        )
        self.assertIn("creations", response.context)
        self.assertEqual(response.context["creations"].count(), 1)


# =============================================================================
# URL TESTS
# =============================================================================

class AccountsURLTests(TestCase):
    """Tests for accounts URL configuration."""

    def test_url_names_reverse_correctly(self):
        """All named URLs should reverse without error."""
        urls_to_check = {
            "accounts:auth": "/accounts/auth/",
            "accounts:login": "/accounts/login/",
            "accounts:register": "/accounts/register/",
            "accounts:logout": "/accounts/logout/",
            "accounts:dashboard": "/accounts/dashboard/",
            "accounts:buyer_dashboard": "/accounts/buyer/",
            "accounts:seller_dashboard": "/accounts/seller/",
            "accounts:become_artisan": "/accounts/become-artisan/",
            "accounts:admin_dashboard": "/accounts/admin-portal/",
        }
        for name, expected in urls_to_check.items():
            self.assertEqual(reverse(name), expected, f"URL {name} mismatch")

    def test_artisan_detail_url(self):
        """Artisan detail URL with pk parameter."""
        url = reverse("accounts:artisan_detail", kwargs={"pk": 42})
        self.assertEqual(url, "/accounts/artisans/42/")
