from django.test import TestCase
from django.contrib.auth.models import User
from .models import ArtisanProfile


class ArtisanProfileModelTests(TestCase):
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
        """New artisan profiles should default to unapproved and unverified for curation safety."""
        self.assertFalse(self.profile.is_approved)
        self.assertFalse(self.profile.is_verified)

    def test_artisan_string_representation(self):
        """__str__ should format display name and craft speciality."""
        expected = "Avani Earthenware (Terracotta Pottery)"
        self.assertEqual(str(self.profile), expected)


class RoleBasedAuthenticationTests(TestCase):
    def setUp(self):
        # 1. Pure Buyer (No ArtisanProfile, not staff)
        self.buyer_user = User.objects.create_user(
            username="buyer_priya",
            email="priya@example.com",
            password="password123"
        )

        # 2. Artisan / Seller (Has ArtisanProfile)
        self.seller_user = User.objects.create_user(
            username="artisan_devraj",
            email="devraj@example.com",
            password="password123"
        )
        self.artisan_profile = ArtisanProfile.objects.create(
            user=self.seller_user,
            display_name="Kutch Clay Works",
            bio="Terracotta clay artisan",
            location="Bhuj, Gujarat",
            craft_speciality="Pottery",
            is_approved=True,
            is_verified=True
        )

        # 3. Admin / Staff Curator
        self.admin_user = User.objects.create_user(
            username="staff_curator",
            email="curator@craftconnect.org",
            password="password123",
            is_staff=True
        )

    def test_anonymous_redirected_from_all_dashboards(self):
        """Unauthenticated visitors must be redirected to auth portal."""
        for url in ["/accounts/buyer/", "/accounts/seller/", "/accounts/admin-portal/", "/accounts/dashboard/"]:
            response = self.client.get(url)
            self.assertEqual(response.status_code, 302)
            self.assertTrue(
                response.url.startswith("/accounts/login/")
                or response.url.startswith("/accounts/auth/")
                or response.url.startswith("/login/")
            )

    def test_buyer_access_buyer_dashboard(self):
        """Buyer should have clean access to Buyer Sanctuary."""
        self.client.login(username="buyer_priya", password="password123")
        response = self.client.get("/accounts/buyer/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Buyer / Patron Workspace")

    def test_buyer_redirected_to_become_artisan_when_accessing_seller_studio(self):
        """A buyer attempting to access the seller studio is guided to the atelier creation form."""
        self.client.login(username="buyer_priya", password="password123")
        response = self.client.get("/accounts/seller/")
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, "/accounts/become-artisan/")

    def test_buyer_denied_admin_portal(self):
        """Regular buyers cannot access the moderation/curation portal."""
        self.client.login(username="buyer_priya", password="password123")
        response = self.client.get("/accounts/admin-portal/")
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, "/accounts/buyer/")

    def test_seller_access_seller_dashboard(self):
        """Artisans should have clean access to their dedicated Studio."""
        self.client.login(username="artisan_devraj", password="password123")
        response = self.client.get("/accounts/seller/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Seller / Artisan Studio Workspace")
        self.assertContains(response, "Kutch Clay Works")

    def test_staff_access_admin_portal(self):
        """Staff members should have full access to Guild Moderation Portal."""
        self.client.login(username="staff_curator", password="password123")
        response = self.client.get("/accounts/admin-portal/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Admin &amp; Staff Curator Portal")

    def test_central_dashboard_routing(self):
        """Central /accounts/dashboard/ dispatches users to their appropriate role home."""
        # Staff -> Admin Portal
        self.client.login(username="staff_curator", password="password123")
        response = self.client.get("/accounts/dashboard/")
        self.assertRedirects(response, "/accounts/admin-portal/")
        self.client.logout()

        # Seller -> Seller Studio
        self.client.login(username="artisan_devraj", password="password123")
        response = self.client.get("/accounts/dashboard/")
        self.assertRedirects(response, "/accounts/seller/")
        self.client.logout()

        # Buyer -> Buyer Sanctuary
        self.client.login(username="buyer_priya", password="password123")
        response = self.client.get("/accounts/dashboard/")
        self.assertRedirects(response, "/accounts/buyer/")

    def test_buyer_can_become_artisan(self):
        """A conscious buyer can submit the Become Artisan form and immediately unlock the studio."""
        self.client.login(username="buyer_priya", password="password123")
        get_resp = self.client.get("/accounts/become-artisan/")
        self.assertEqual(get_resp.status_code, 200)
        self.assertContains(get_resp, "Open Your Artisan Atelier")

        post_data = {
            "display_name": "Priya Handlooms",
            "craft_speciality": "Chanderi Weaving",
            "location": "Chanderi, Madhya Pradesh",
            "bio": "Handspun organic cotton and silk saris with traditional zari work."
        }
        post_resp = self.client.post("/accounts/become-artisan/", data=post_data)
        self.assertEqual(post_resp.status_code, 302)
        self.assertRedirects(post_resp, "/accounts/seller/")

        # Verify profile was created
        self.buyer_user.refresh_from_db()
        self.assertTrue(hasattr(self.buyer_user, "artisan_profile"))
        self.assertEqual(self.buyer_user.artisan_profile.display_name, "Priya Handlooms")

