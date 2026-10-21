from decimal import Decimal
from django.test import TestCase, SimpleTestCase
from django.urls import reverse, resolve
from django.contrib.auth.models import User
from django.db.utils import IntegrityError
from accounts.models import ArtisanProfile
from .models import Category, Product, Enquiry, SavedProduct, Story, Order
from .forms import ProductSearchForm, EnquiryForm, BuyOrderForm
from .views import HomeView, ProductCatalogView, ProductDetailView, ProductBuyView


class MarketplaceRoutingAndFormTests(SimpleTestCase):
    """
    Tests for URL routing and Form validation that do not require database transactions.
    """
    def test_url_reverse_and_resolution(self):
        """Verify URL names reverse and resolve to correct view classes."""
        self.assertEqual(reverse("marketplace:home"), "/")
        self.assertEqual(reverse("marketplace:product_catalog"), "/catalogue/")
        self.assertEqual(
            reverse("marketplace:product_detail", kwargs={"slug": "terracotta-vase"}),
            "/crafts/terracotta-vase/"
        )
        self.assertEqual(
            reverse("marketplace:category_detail", kwargs={"slug": "ceramics"}),
            "/genres/ceramics/"
        )

        # Resolve checks
        self.assertEqual(resolve("/").func.view_class, HomeView)
        self.assertEqual(resolve("/catalogue/").func.view_class, ProductCatalogView)
        self.assertEqual(resolve("/crafts/sample-piece/").func.view_class, ProductDetailView)

    def test_product_search_form_valid(self):
        """Test search form accepting queries and valid sort orders."""
        form = ProductSearchForm(data={"q": "terracotta", "ordering": "price_asc"})
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data["q"], "terracotta")
        self.assertEqual(form.cleaned_data["ordering"], "price_asc")

    def test_enquiry_form_validation(self):
        """EnquiryForm must enforce min-length validation on subject and message."""
        # Invalid short message
        invalid_form = EnquiryForm(data={"subject": "Hi", "message": "Short"})
        self.assertFalse(invalid_form.is_valid())
        self.assertIn("subject", invalid_form.errors)
        self.assertIn("message", invalid_form.errors)

        # Valid form
        valid_form = EnquiryForm(data={
            "subject": "Custom Order Inquiry",
            "message": "Can this handmade stole be woven in indigo shade?"
        })
        self.assertTrue(valid_form.is_valid())


class MarketplaceModelTests(TestCase):
    def setUp(self):
        # Create an artisan user & profile
        self.artisan_user = User.objects.create_user(
            username="ramesh_artisan",
            email="ramesh@example.com",
            password="artisanpass123"
        )
        self.artisan = ArtisanProfile.objects.create(
            user=self.artisan_user,
            display_name="Rameshwar Handlooms",
            craft_speciality="Handloom Weaving",
            is_approved=True
        )

        # Create a buyer user
        self.buyer = User.objects.create_user(
            username="ananya_buyer",
            email="ananya@example.com",
            password="buyerpass123"
        )

        # Create category
        self.category = Category.objects.create(
            name="Handloom & Textiles",
            description="Traditional hand-spun and shuttle-loomed artisan fabrics."
        )

        # Create standard product
        self.product = Product.objects.create(
            artisan=self.artisan,
            category=self.category,
            title="Indigo Cotton Stole",
            description="Organic handloom cotton dyed with fermented wild indigo.",
            price=Decimal("1250.00"),
            material="Organic Cotton",
            colour="Deep Indigo",
            tags="handloom, organic, natural dye",
            stock_quantity=5,
            is_available=True,
            is_approved=True
        )

    def test_category_slug_generation(self):
        """Category should automatically generate a slug from its name."""
        self.assertEqual(self.category.slug, "handloom-textiles")

    def test_product_creation_and_defaults(self):
        """Product should be linked to Category and ArtisanProfile with valid slug."""
        self.assertEqual(self.product.artisan, self.artisan)
        self.assertEqual(self.product.category, self.category)
        self.assertTrue(self.product.slug.startswith("indigo-cotton-stole"))
        self.assertEqual(self.product.price, Decimal("1250.00"))

    def test_public_queryset_only_returns_approved_available_products(self):
        """
        Product.objects.public() must only return products that are approved,
        available, in stock, and belong to an approved artisan.
        """
        public_products = Product.objects.public()
        self.assertIn(self.product, public_products)

        # Unapproved product
        unapproved = Product.objects.create(
            artisan=self.artisan,
            category=self.category,
            title="Unapproved Raw Silk Shawl",
            description="Pending curation.",
            price=Decimal("2500.00"),
            stock_quantity=3,
            is_available=True,
            is_approved=False
        )
        self.assertNotIn(unapproved, Product.objects.public())

        # Out-of-stock product
        out_of_stock = Product.objects.create(
            artisan=self.artisan,
            category=self.category,
            title="Sold Out Linen Scarf",
            description="Archived piece.",
            price=Decimal("800.00"),
            stock_quantity=0,
            is_available=True,
            is_approved=True
        )
        self.assertNotIn(out_of_stock, Product.objects.public())

        # Product by unapproved artisan
        unapproved_artisan_user = User.objects.create_user(username="pending_artisan")
        unapproved_artisan = ArtisanProfile.objects.create(
            user=unapproved_artisan_user,
            display_name="Pending Studio",
            craft_speciality="Woodwork",
            is_approved=False
        )
        pending_product = Product.objects.create(
            artisan=unapproved_artisan,
            category=self.category,
            title="Carved Teak Coaster",
            description="Wood craft.",
            price=Decimal("450.00"),
            stock_quantity=10,
            is_available=True,
            is_approved=True
        )
        self.assertNotIn(pending_product, Product.objects.public())

    def test_saved_product_uniqueness_constraint(self):
        """
        Ensure a buyer cannot save the same product more than once.
        Duplicate saves must raise an IntegrityError.
        """
        SavedProduct.objects.create(
            buyer=self.buyer,
            product=self.product
        )
        self.assertEqual(SavedProduct.objects.count(), 1)

        with self.assertRaises(IntegrityError):
            SavedProduct.objects.create(
                buyer=self.buyer,
                product=self.product
            )

    def test_enquiry_creation(self):
        """Buyer should be able to submit an inquiry regarding a product."""
        enquiry = Enquiry.objects.create(
            product=self.product,
            buyer=self.buyer,
            subject="Custom Dimensions Inquiry",
            message="Can this stole be woven in 2.5m length?"
        )
        self.assertEqual(enquiry.product, self.product)
        self.assertEqual(enquiry.buyer, self.buyer)
        self.assertFalse(enquiry.is_resolved)

    def test_home_view_response(self):
        """HomeView should return 200 and render marketplace/home.html."""
        response = self.client.get(reverse("marketplace:home"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "marketplace/home.html")
        self.assertTemplateUsed(response, "base.html")
        self.assertIn("featured_products", response.context)

    def test_product_catalog_view_response(self):
        """ProductCatalogView should return 200 and render marketplace/product_catalog.html."""
        response = self.client.get(reverse("marketplace:product_catalog"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "marketplace/product_catalog.html")

    def test_product_detail_view_public_vs_unapproved(self):
        """Approved product should return 200; unapproved product must return 404."""
        # Approved piece
        response = self.client.get(reverse("marketplace:product_detail", kwargs={"slug": self.product.slug}))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "marketplace/product_detail.html")

        # Unapproved piece
        unapproved = Product.objects.create(
            artisan=self.artisan,
            category=self.category,
            title="Private Draft Ceramic",
            description="Hidden draft.",
            price=Decimal("999.00"),
            stock_quantity=2,
            is_available=True,
            is_approved=False
        )
        response_404 = self.client.get(reverse("marketplace:product_detail", kwargs={"slug": unapproved.slug}))
        self.assertEqual(response_404.status_code, 404)


class SyllabusFeatureTests(TestCase):
    """
    Direct verification of Syllabus Unit II, III, V, and VI requirements:
    - Unit II: Regular expression URL routing & Custom Error Handling
    - Unit III: Django Template Language (DTL) custom tags & filters
    - Unit V: Django Groups and Model Permissions
    - Unit VI: Django Sessions and Cookies management
    """
    def setUp(self):
        self.artisan_user = User.objects.create_user(
            username="suresh_weaver",
            email="suresh@example.com",
            password="password123"
        )
        self.artisan = ArtisanProfile.objects.create(
            user=self.artisan_user,
            display_name="Suresh Silk Looms",
            bio="Pochampally Ikat master weaver.",
            location="Pochampally, Telangana",
            craft_speciality="Ikat Weaving",
            is_approved=True,
            is_verified=True
        )
        self.category = Category.objects.create(
            name="Handloom Textiles",
            slug="handloom-textiles",
            description="Handwoven natural fabric."
        )
        self.product = Product.objects.create(
            artisan=self.artisan,
            category=self.category,
            title="Double Ikat Silk Dupatta",
            slug="double-ikat-silk-dupatta",
            description="Handwoven geometric ikat silk.",
            price=Decimal("4200.00"),
            stock_quantity=3,
            is_available=True,
            is_approved=True
        )

    def test_session_tracks_recently_viewed_crafts(self):
        """Syllabus Unit VI: Verify Django Session stores recently viewed items."""
        response = self.client.get(reverse("marketplace:product_detail", kwargs={"slug": self.product.slug}))
        self.assertEqual(response.status_code, 200)

        # Check session
        session = self.client.session
        self.assertIn("recently_viewed_crafts", session)
        self.assertIn(self.product.id, session["recently_viewed_crafts"])

    def test_cookie_set_on_product_view(self):
        """Syllabus Unit VI: Verify Django Cookie is set on response."""
        response = self.client.get(reverse("marketplace:product_detail", kwargs={"slug": self.product.slug}))
        self.assertEqual(response.status_code, 200)

        # Check client cookie
        self.assertIn("last_viewed_craft_slug", response.cookies)
        self.assertEqual(response.cookies["last_viewed_craft_slug"].value, self.product.slug)

    def test_regex_url_archive_year_routing(self):
        """Syllabus Unit II: Verify re_path regex archive matching 4-digit years."""
        year = str(self.product.created_at.year)
        url = reverse("marketplace:craft_archive_year", kwargs={"year": year})
        self.assertEqual(url, f"/archive/{year}/")

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.product.title)

    def test_regex_url_provenance_lookup(self):
        """Syllabus Unit II: Verify re_path regex provenance code matching."""
        batch_code = f"CC-{self.product.id}"
        url = reverse("marketplace:provenance_lookup", kwargs={"batch_code": batch_code})
        self.assertEqual(url, f"/provenance/{batch_code}/")

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.product.title)

    def test_custom_template_filters(self):
        """Syllabus Unit III: Verify custom template filters (craft_extras)."""
        from marketplace.templatetags.craft_extras import inr_format, artisan_initials, verified_maker_badge

        # Test currency filter
        self.assertEqual(inr_format(4200), "₹4,200")
        self.assertEqual(inr_format(1850.50), "₹1,850.50")

        # Test initials filter
        self.assertEqual(artisan_initials("Suresh Silk Looms"), "SS")
        self.assertEqual(artisan_initials("Terracotta"), "TE")

        # Test badge tag
        badge_html = verified_maker_badge(True)
        self.assertIn("Verified Atelier", badge_html)

    def test_groups_and_permissions(self):
        """Syllabus Unit V: Verify Django Groups and Permissions provisioning."""
        from django.contrib.auth.models import Group
        from django.core.management import call_command

        call_command("setup_groups_and_permissions")
        self.assertTrue(Group.objects.filter(name="Artisans").exists())
        self.assertTrue(Group.objects.filter(name="Patrons").exists())
        self.assertTrue(Group.objects.filter(name="Guild_Curators").exists())

        artisan_group = Group.objects.get(name="Artisans")
        self.assertTrue(artisan_group.permissions.filter(codename="add_product").exists())


class EditorialJournalStoryTests(TestCase):
    """
    Unit tests for Editorial Journal stories, routing, and views.
    """
    def setUp(self):
        self.artisan_user = User.objects.create_user(
            username="test_artisan_writer",
            password="testpassword123"
        )
        self.artisan_profile = ArtisanProfile.objects.create(
            user=self.artisan_user,
            display_name="Kutch Terracotta Atelier",
            is_approved=True
        )
        self.category = Category.objects.create(name="Ceramics & Fire", slug="ceramics-fire")
        self.product = Product.objects.create(
            artisan=self.artisan_profile,
            category=self.category,
            title="Hand-Thrown Earthen Teacup",
            slug="hand-thrown-earthen-teacup",
            description="Clay teacup",
            price=Decimal("450.00"),
            stock_quantity=10,
            is_available=True,
            is_approved=True,
        )
        self.story = Story.objects.create(
            title="The Earth remembers the hand that turns it.",
            volume_tag="Editorial Journal • Vol. 04",
            pull_quote="In an era of rapid production, slow craft is cultural preservation.",
            author_name="Devraj Kumhar",
            author_role="Master Potter, Kutch Guild",
            reading_time="5 min read",
            craft_region="Kutch, Gujarat",
            category="Ceramics & Terracotta",
            lead_paragraph="Devraj Kumhar's family has worked the Kutch salt-clay for two hundred years.",
            body_content="Full story body content about clay and pottery.",
            is_featured=True,
            is_published=True,
            artisan=self.artisan_profile,
        )
        self.story.related_products.add(self.product)

    def test_story_creation_and_slug(self):
        """Story automatically generates a slug and string representation."""
        self.assertEqual(self.story.slug, "the-earth-remembers-the-hand-that-turns-it")
        self.assertIn("The Earth remembers the hand that turns it.", str(self.story))

    def test_story_urls_reverse_and_resolve(self):
        """Journal URLs reverse and resolve correctly."""
        self.assertEqual(reverse("marketplace:story_list"), "/journal/")
        self.assertEqual(
            reverse("marketplace:story_detail", kwargs={"slug": self.story.slug}),
            f"/journal/{self.story.slug}/"
        )

    def test_story_list_view(self):
        """StoryListView returns 200 and displays stories and categories."""
        response = self.client.get(reverse("marketplace:story_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.story.title)
        self.assertContains(response, "Editorial Journal • Vol. 04")
        self.assertContains(response, "Devraj Kumhar")

    def test_story_list_category_filter(self):
        """Category query parameter filters stories."""
        response = self.client.get(reverse("marketplace:story_list") + "?category=Ceramics & Terracotta")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.story.title)

        # Empty grid result for non-matching category
        empty_response = self.client.get(reverse("marketplace:story_list") + "?category=NonExistentCategory")
        self.assertEqual(empty_response.status_code, 200)
        self.assertContains(empty_response, "0 Selected Stories")
        self.assertContains(empty_response, "No stories found in this section")

    def test_story_detail_view(self):
        """StoryDetailView renders full story content and related craft pieces."""
        url = reverse("marketplace:story_detail", kwargs={"slug": self.story.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.story.title)
        self.assertContains(response, "In an era of rapid production")
        self.assertContains(response, "worked the Kutch salt-clay")
        self.assertContains(response, self.product.title)

    def test_home_view_spotlight_links_to_story(self):
        """Homepage spotlights featured story with link to its detail page."""
        response = self.client.get(reverse("marketplace:home"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.story.title)
        self.assertContains(response, reverse("marketplace:story_detail", kwargs={"slug": self.story.slug}))


class ProductBuyAndOrderTests(TestCase):
    def setUp(self):
        self.artisan_user = User.objects.create_user(
            username="test_artisan",
            email="artisan@test.com",
            password="password123"
        )
        self.artisan = ArtisanProfile.objects.create(
            user=self.artisan_user,
            display_name="Kutch Handloom Guild",
            location="Kutch, Gujarat",
            craft_speciality="Ajrakh Block Printing",
            is_approved=True
        )

        self.buyer_user = User.objects.create_user(
            username="test_buyer",
            email="buyer@test.com",
            password="password123"
        )

        self.category = Category.objects.create(
            name="Textiles & Handloom",
            description="Traditional handlooms."
        )

        self.product = Product.objects.create(
            artisan=self.artisan,
            category=self.category,
            title="Ajrakh Silk Dupatta",
            description="Pure silk naturally dyed.",
            price=Decimal("3000.00"),
            stock_quantity=3,
            is_available=True,
            is_approved=True
        )

    def test_buy_order_form_valid(self):
        """BuyOrderForm accepts valid quantity, shipping details and payment method."""
        form = BuyOrderForm(data={
            "quantity": 2,
            "shipping_address": "Flat 101, Green Meadows",
            "shipping_city": "Mumbai",
            "shipping_postal_code": "400001",
            "contact_phone": "+91 99887 76655",
            "payment_method": "upi",
        })
        self.assertTrue(form.is_valid())

    def test_buy_order_form_invalid_quantity(self):
        """BuyOrderForm rejects quantity less than 1."""
        form = BuyOrderForm(data={
            "quantity": 0,
            "shipping_address": "Flat 101, Green Meadows",
            "shipping_city": "Mumbai",
            "shipping_postal_code": "400001",
            "contact_phone": "+91 99887 76655",
            "payment_method": "upi",
        })
        self.assertFalse(form.is_valid())
        self.assertIn("quantity", form.errors)

    def test_product_buy_unauthenticated_redirect(self):
        """Unauthenticated user attempting to buy is redirected to login."""
        url = reverse("marketplace:product_buy", kwargs={"slug": self.product.slug})
        response = self.client.post(url, {
            "quantity": 1,
            "shipping_address": "Flat 101, Green Meadows",
            "shipping_city": "Mumbai",
            "shipping_postal_code": "400001",
            "contact_phone": "+91 99887 76655",
            "payment_method": "upi",
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith(reverse("accounts:auth")))

    def test_product_buy_successful(self):
        """Authenticated buyer successfully buys a piece: stock decreases and Order is created with 88% artisan share."""
        self.client.login(username="test_buyer", password="password123")
        url = reverse("marketplace:product_buy", kwargs={"slug": self.product.slug})

        response = self.client.post(url, {
            "quantity": 2,
            "shipping_address": "Flat 101, Green Meadows",
            "shipping_city": "Mumbai",
            "shipping_postal_code": "400001",
            "contact_phone": "+91 99887 76655",
            "payment_method": "upi",
        })

        self.assertRedirects(response, reverse("accounts:buyer_dashboard"))

        # Check Order was created
        order = Order.objects.get(buyer=self.buyer_user, product=self.product)
        self.assertEqual(order.quantity, 2)
        self.assertEqual(order.unit_price, Decimal("3000.00"))
        self.assertEqual(order.total_price, Decimal("6000.00"))
        # 88% of 6000 is 5280
        self.assertEqual(order.artisan_share, Decimal("5280.00"))
        self.assertEqual(order.payment_method, "upi")
        self.assertEqual(order.shipping_city, "Mumbai")

        # Check stock was decremented from 3 to 1
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock_quantity, 1)
        self.assertTrue(self.product.is_available)

    def test_product_buy_depletes_stock_marks_unavailable(self):
        """Purchasing entire stock decrements to 0 and marks is_available=False."""
        self.client.login(username="test_buyer", password="password123")
        url = reverse("marketplace:product_buy", kwargs={"slug": self.product.slug})

        response = self.client.post(url, {
            "quantity": 3,
            "shipping_address": "Flat 101, Green Meadows",
            "shipping_city": "Mumbai",
            "shipping_postal_code": "400001",
            "contact_phone": "+91 99887 76655",
            "payment_method": "cod",
        })

        self.assertRedirects(response, reverse("accounts:buyer_dashboard"))
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock_quantity, 0)
        self.assertFalse(self.product.is_available)

    def test_product_buy_insufficient_stock(self):
        """Attempting to buy more than available stock is rejected."""
        self.client.login(username="test_buyer", password="password123")
        url = reverse("marketplace:product_buy", kwargs={"slug": self.product.slug})

        response = self.client.post(url, {
            "quantity": 5,  # only 3 available
            "shipping_address": "Flat 101, Green Meadows",
            "shipping_city": "Mumbai",
            "shipping_postal_code": "400001",
            "contact_phone": "+91 99887 76655",
            "payment_method": "card",
        })

        self.assertRedirects(response, reverse("marketplace:product_detail", kwargs={"slug": self.product.slug}))
        self.assertEqual(Order.objects.filter(buyer=self.buyer_user).count(), 0)
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock_quantity, 3)



