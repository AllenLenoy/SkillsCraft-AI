"""
Comprehensive Test Suite — marketplace app
===========================================
Covers:
  • Category model (slug generation, __str__, Meta)
  • Product model (creation, slug generation, public() queryset, __str__, constraints)
  • Enquiry model (creation, defaults, __str__)
  • SavedProduct model (creation, uniqueness constraint, __str__)
  • Order model (creation, auto-fields, 88% artisan share, order_number, __str__)
  • Story model (slug generation, ManyToMany, __str__, Meta)
  • ProductSearchForm (valid, empty, ordering)
  • EnquiryForm (valid, min-length validation)
  • BuyOrderForm (valid, invalid quantity, short address)
  • HomeView (200, context, session/cookie reading)
  • ProductCatalogView (200, search, category filter, ordering, pagination)
  • ProductDetailView (200, 404 for unapproved, sessions, cookies)
  • CategoryDetailView (200, product listing)
  • CraftArchiveYearView (regex routing, 200)
  • ProvenanceLookupView (regex routing, 200)
  • ProductEnquiryView (POST, auth required)
  • ProductBuyView (full purchase flow, stock, depleted, insufficient stock, auth)
  • ToggleSaveProductView (save/unsave toggle, auth required)
  • StoryListView (200, category filter, empty results)
  • StoryDetailView (200, related stories)
  • Custom template tags/filters (inr_format, artisan_initials, verified_maker_badge,
    stock_status)
  • Django Groups & Permissions (setup_groups_and_permissions command)
  • AI Service (heuristic fallback, smart_craft_discovery, safe_extract_json)
  • Custom error handlers (404, 500 config)
"""

from decimal import Decimal
from unittest.mock import patch

from django.test import TestCase, SimpleTestCase
from django.urls import reverse, resolve
from django.contrib.auth.models import User, Group
from django.db.utils import IntegrityError
from django.core.management import call_command

from accounts.models import ArtisanProfile
from .models import Category, Product, Enquiry, SavedProduct, Story, Order
from .forms import ProductSearchForm, EnquiryForm, BuyOrderForm
from .views import (
    HomeView, ProductCatalogView, ProductDetailView, ProductBuyView,
    StoryListView, StoryDetailView, CraftArchiveYearView,
    CategoryDetailView, ProvenanceLookupView,
)


# =============================================================================
# URL ROUTING & FORM TESTS (No DB)
# =============================================================================

class MarketplaceRoutingAndFormTests(SimpleTestCase):
    """Tests for URL routing and Form validation that do not require database."""

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

    def test_story_url_reverse(self):
        """Story URLs should reverse correctly."""
        self.assertEqual(reverse("marketplace:story_list"), "/journal/")
        self.assertEqual(
            reverse("marketplace:story_detail", kwargs={"slug": "test-story"}),
            "/journal/test-story/"
        )

    def test_story_alias_url_reverse(self):
        """Story alias URLs should resolve."""
        self.assertEqual(reverse("marketplace:story_list_alias"), "/stories/")

    def test_buy_url_reverse(self):
        """Buy URL should reverse correctly."""
        self.assertEqual(
            reverse("marketplace:product_buy", kwargs={"slug": "item"}),
            "/crafts/item/buy/"
        )

    def test_enquiry_url_reverse(self):
        """Enquiry URL should reverse."""
        self.assertEqual(
            reverse("marketplace:product_enquiry", kwargs={"slug": "item"}),
            "/crafts/item/enquire/"
        )

    def test_save_toggle_url_reverse(self):
        """Toggle save URL should reverse."""
        self.assertEqual(
            reverse("marketplace:toggle_save", kwargs={"slug": "item"}),
            "/crafts/item/save/"
        )

    def test_archive_year_url_reverse(self):
        """Archive year regex URL should reverse."""
        self.assertEqual(
            reverse("marketplace:craft_archive_year", kwargs={"year": "2026"}),
            "/archive/2026/"
        )

    def test_provenance_lookup_url_reverse(self):
        """Provenance lookup regex URL should reverse."""
        self.assertEqual(
            reverse("marketplace:provenance_lookup", kwargs={"batch_code": "CC-123"}),
            "/provenance/CC-123/"
        )

    def test_product_search_form_valid(self):
        """Search form accepting queries and valid sort orders."""
        form = ProductSearchForm(data={"q": "terracotta", "ordering": "price_asc"})
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data["q"], "terracotta")
        self.assertEqual(form.cleaned_data["ordering"], "price_asc")

    def test_product_search_form_empty(self):
        """Empty search form should be valid (all optional)."""
        form = ProductSearchForm(data={})
        self.assertTrue(form.is_valid())

    def test_product_search_form_ordering_choices(self):
        """All ordering choices should be accepted."""
        for ordering in ["-created_at", "price_asc", "price_desc", "title_asc"]:
            form = ProductSearchForm(data={"ordering": ordering})
            self.assertTrue(form.is_valid(), f"Ordering {ordering} should be valid")

    def test_enquiry_form_validation_invalid(self):
        """EnquiryForm must enforce min-length on subject and message."""
        invalid_form = EnquiryForm(data={"subject": "Hi", "message": "Short"})
        self.assertFalse(invalid_form.is_valid())
        self.assertIn("subject", invalid_form.errors)
        self.assertIn("message", invalid_form.errors)

    def test_enquiry_form_validation_valid(self):
        """Valid enquiry form should pass."""
        valid_form = EnquiryForm(data={
            "subject": "Custom Order Inquiry",
            "message": "Can this handmade stole be woven in indigo shade?"
        })
        self.assertTrue(valid_form.is_valid())

    def test_enquiry_form_subject_exactly_3_chars(self):
        """Subject of exactly 3 chars should be valid."""
        form = EnquiryForm(data={
            "subject": "Ask",
            "message": "Is this available for custom orders?"
        })
        self.assertTrue(form.is_valid())

    def test_enquiry_form_message_exactly_10_chars(self):
        """Message of exactly 10 chars should be valid."""
        form = EnquiryForm(data={
            "subject": "Question",
            "message": "0123456789"
        })
        self.assertTrue(form.is_valid())


# =============================================================================
# MODEL TESTS
# =============================================================================

class CategoryModelTests(TestCase):
    """Tests for the Category model."""

    def test_slug_auto_generation(self):
        """Category should auto-generate slug from name."""
        cat = Category.objects.create(name="Handloom & Textiles")
        self.assertEqual(cat.slug, "handloom-textiles")

    def test_explicit_slug_preserved(self):
        """Explicit slug should not be overwritten."""
        cat = Category.objects.create(name="Bronze Art", slug="custom-slug")
        self.assertEqual(cat.slug, "custom-slug")

    def test_category_str(self):
        """__str__ should return name."""
        cat = Category.objects.create(name="Ceramics", slug="ceramics")
        self.assertEqual(str(cat), "Ceramics")

    def test_category_ordering(self):
        """Categories should be ordered by name."""
        self.assertEqual(Category._meta.ordering, ["name"])

    def test_category_unique_name(self):
        """Duplicate category name should raise IntegrityError."""
        Category.objects.create(name="Unique Cat")
        with self.assertRaises(IntegrityError):
            Category.objects.create(name="Unique Cat")

    def test_category_verbose_names(self):
        """Check verbose names."""
        self.assertEqual(Category._meta.verbose_name, "Category")
        self.assertEqual(Category._meta.verbose_name_plural, "Categories")


class ProductModelTests(TestCase):
    """Tests for the Product model."""

    def setUp(self):
        self.artisan_user = User.objects.create_user(
            username="prod_artisan", password="pass123"
        )
        self.artisan = ArtisanProfile.objects.create(
            user=self.artisan_user, display_name="Rameshwar Handlooms",
            craft_speciality="Handloom Weaving", is_approved=True
        )
        self.category = Category.objects.create(
            name="Handloom & Textiles", slug="handloom-textiles"
        )
        self.product = Product.objects.create(
            artisan=self.artisan, category=self.category,
            title="Indigo Cotton Stole",
            description="Organic handloom cotton dyed with indigo.",
            price=Decimal("1250.00"),
            material="Organic Cotton", colour="Deep Indigo",
            tags="handloom, organic, natural dye",
            stock_quantity=5, is_available=True, is_approved=True
        )

    def test_product_creation_and_defaults(self):
        """Product should be linked to Category and ArtisanProfile."""
        self.assertEqual(self.product.artisan, self.artisan)
        self.assertEqual(self.product.category, self.category)
        self.assertTrue(self.product.slug.startswith("indigo-cotton-stole"))
        self.assertEqual(self.product.price, Decimal("1250.00"))

    def test_product_slug_uniqueness(self):
        """Duplicate titles should generate unique slugs."""
        p2 = Product.objects.create(
            artisan=self.artisan, category=self.category,
            title="Indigo Cotton Stole",
            description="Another stole.",
            price=Decimal("1300.00"), stock_quantity=3,
            is_approved=True
        )
        self.assertNotEqual(self.product.slug, p2.slug)
        self.assertTrue(p2.slug.startswith("indigo-cotton-stole"))

    def test_product_str(self):
        """__str__ should format title and artisan name."""
        self.assertEqual(
            str(self.product),
            "Indigo Cotton Stole by Rameshwar Handlooms"
        )

    def test_product_ordering(self):
        """Products should be ordered by -created_at."""
        self.assertEqual(Product._meta.ordering, ["-created_at"])

    def test_product_verbose_names(self):
        self.assertEqual(Product._meta.verbose_name, "Product")
        self.assertEqual(Product._meta.verbose_name_plural, "Products")

    def test_public_queryset_returns_approved_available(self):
        """public() returns only approved, available, in-stock, approved-artisan."""
        self.assertIn(self.product, Product.objects.public())

    def test_public_excludes_unapproved(self):
        """Unapproved product excluded from public()."""
        unapproved = Product.objects.create(
            artisan=self.artisan, category=self.category,
            title="Unapproved Shawl", description="Pending.",
            price=Decimal("2500.00"), stock_quantity=3,
            is_available=True, is_approved=False
        )
        self.assertNotIn(unapproved, Product.objects.public())

    def test_public_excludes_out_of_stock(self):
        """Out of stock product excluded from public()."""
        oos = Product.objects.create(
            artisan=self.artisan, category=self.category,
            title="OOS Scarf", description="Archived.",
            price=Decimal("800.00"), stock_quantity=0,
            is_available=True, is_approved=True
        )
        self.assertNotIn(oos, Product.objects.public())

    def test_public_excludes_unavailable(self):
        """Unavailable product excluded from public()."""
        unavail = Product.objects.create(
            artisan=self.artisan, category=self.category,
            title="Unavailable Item", description="Not listed.",
            price=Decimal("600.00"), stock_quantity=5,
            is_available=False, is_approved=True
        )
        self.assertNotIn(unavail, Product.objects.public())

    def test_public_excludes_unapproved_artisan(self):
        """Product by unapproved artisan excluded from public()."""
        unapproved_user = User.objects.create_user(username="pending_artisan")
        unapproved_artisan = ArtisanProfile.objects.create(
            user=unapproved_user, display_name="Pending Studio",
            craft_speciality="Woodwork", is_approved=False
        )
        pending_product = Product.objects.create(
            artisan=unapproved_artisan, category=self.category,
            title="Carved Coaster", description="Wood craft.",
            price=Decimal("450.00"), stock_quantity=10,
            is_available=True, is_approved=True
        )
        self.assertNotIn(pending_product, Product.objects.public())


class EnquiryModelTests(TestCase):
    """Tests for the Enquiry model."""

    def setUp(self):
        self.artisan_user = User.objects.create_user(username="enq_artisan", password="p")
        self.artisan = ArtisanProfile.objects.create(
            user=self.artisan_user, display_name="Enq Studio",
            craft_speciality="Pottery", is_approved=True
        )
        self.buyer = User.objects.create_user(username="enq_buyer", password="p")
        self.category = Category.objects.create(name="Cat1", slug="cat1")
        self.product = Product.objects.create(
            artisan=self.artisan, category=self.category,
            title="Enq Product", description="D",
            price=Decimal("500.00"), stock_quantity=5,
            is_approved=True, is_available=True
        )

    def test_enquiry_creation(self):
        """Enquiry should be created with correct relationships."""
        enq = Enquiry.objects.create(
            product=self.product, buyer=self.buyer,
            subject="Dimensions", message="Can I get this in 2.5m?"
        )
        self.assertEqual(enq.product, self.product)
        self.assertEqual(enq.buyer, self.buyer)
        self.assertFalse(enq.is_resolved)

    def test_enquiry_str(self):
        """__str__ should format buyer and product."""
        enq = Enquiry.objects.create(
            product=self.product, buyer=self.buyer,
            subject="Q", message="Question text here"
        )
        self.assertIn("enq_buyer", str(enq))
        self.assertIn("Enq Product", str(enq))

    def test_enquiry_ordering(self):
        self.assertEqual(Enquiry._meta.ordering, ["-created_at"])


class SavedProductModelTests(TestCase):
    """Tests for the SavedProduct model."""

    def setUp(self):
        self.artisan_user = User.objects.create_user(username="sp_artisan", password="p")
        self.artisan = ArtisanProfile.objects.create(
            user=self.artisan_user, display_name="SP Studio",
            craft_speciality="Pottery", is_approved=True
        )
        self.buyer = User.objects.create_user(username="sp_buyer", password="p")
        self.category = Category.objects.create(name="SP Cat", slug="sp-cat")
        self.product = Product.objects.create(
            artisan=self.artisan, category=self.category,
            title="SP Product", description="D",
            price=Decimal("500.00"), stock_quantity=5,
            is_approved=True, is_available=True
        )

    def test_saved_product_creation(self):
        sp = SavedProduct.objects.create(buyer=self.buyer, product=self.product)
        self.assertEqual(sp.buyer, self.buyer)
        self.assertEqual(sp.product, self.product)

    def test_uniqueness_constraint(self):
        """Duplicate buyer-product pair should raise IntegrityError."""
        SavedProduct.objects.create(buyer=self.buyer, product=self.product)
        with self.assertRaises(IntegrityError):
            SavedProduct.objects.create(buyer=self.buyer, product=self.product)

    def test_saved_product_str(self):
        sp = SavedProduct.objects.create(buyer=self.buyer, product=self.product)
        self.assertIn("sp_buyer", str(sp))
        self.assertIn("SP Product", str(sp))


class OrderModelTests(TestCase):
    """Tests for the Order model."""

    def setUp(self):
        self.artisan_user = User.objects.create_user(username="ord_artisan", password="p")
        self.artisan = ArtisanProfile.objects.create(
            user=self.artisan_user, display_name="Ord Studio",
            craft_speciality="Pottery", is_approved=True
        )
        self.buyer = User.objects.create_user(username="ord_buyer", password="p")
        self.category = Category.objects.create(name="Ord Cat", slug="ord-cat")
        self.product = Product.objects.create(
            artisan=self.artisan, category=self.category,
            title="Ord Product", description="D",
            price=Decimal("1000.00"), stock_quantity=5,
            is_approved=True, is_available=True
        )

    def test_order_auto_fields(self):
        """Order should auto-compute order_number, total, artisan_share."""
        order = Order.objects.create(
            buyer=self.buyer, product=self.product, artisan=self.artisan,
            quantity=2, shipping_address="123 Street"
        )
        self.assertTrue(order.order_number.startswith("CC-ORD-"))
        self.assertEqual(order.unit_price, Decimal("1000.00"))
        self.assertEqual(order.total_price, Decimal("2000.00"))
        self.assertEqual(order.artisan_share, Decimal("1760.00"))

    def test_order_88_percent_share(self):
        """88% of 5000 = 4400."""
        order = Order.objects.create(
            buyer=self.buyer, product=self.product, artisan=self.artisan,
            quantity=5, unit_price=Decimal("1000.00"),
            total_price=Decimal("5000.00"),
            shipping_address="123 Street"
        )
        self.assertEqual(order.artisan_share, Decimal("4400.00"))

    def test_order_str(self):
        order = Order.objects.create(
            buyer=self.buyer, product=self.product, artisan=self.artisan,
            quantity=1, shipping_address="Addr"
        )
        self.assertIn("ord_buyer", str(order))
        self.assertIn("Ord Product", str(order))

    def test_order_status_default(self):
        """Default status should be 'confirmed'."""
        order = Order.objects.create(
            buyer=self.buyer, product=self.product, artisan=self.artisan,
            quantity=1, shipping_address="Addr"
        )
        self.assertEqual(order.status, "confirmed")

    def test_order_unique_order_number(self):
        """Each order should have a unique order_number."""
        o1 = Order.objects.create(
            buyer=self.buyer, product=self.product, artisan=self.artisan,
            quantity=1, shipping_address="A"
        )
        o2 = Order.objects.create(
            buyer=self.buyer, product=self.product, artisan=self.artisan,
            quantity=1, shipping_address="B"
        )
        self.assertNotEqual(o1.order_number, o2.order_number)

    def test_order_auto_assigns_artisan_from_product(self):
        """If artisan not set, it should be inferred from product."""
        order = Order(
            buyer=self.buyer, product=self.product,
            quantity=1, shipping_address="Addr"
        )
        order.save()
        self.assertEqual(order.artisan, self.artisan)


class StoryModelTests(TestCase):
    """Tests for the Story model."""

    def setUp(self):
        self.artisan_user = User.objects.create_user(username="story_artisan", password="p")
        self.artisan = ArtisanProfile.objects.create(
            user=self.artisan_user, display_name="Story Studio",
            craft_speciality="Pottery", is_approved=True
        )
        self.category = Category.objects.create(name="Story Cat", slug="story-cat")
        self.product = Product.objects.create(
            artisan=self.artisan, category=self.category,
            title="Story Product", description="D",
            price=Decimal("500.00"), stock_quantity=5,
            is_approved=True, is_available=True
        )

    def test_story_slug_auto_generation(self):
        story = Story.objects.create(
            title="The Ancient Fire of Gorakhpur",
            pull_quote="Quote.", lead_paragraph="Lead.",
            body_content="Body.", artisan=self.artisan
        )
        self.assertEqual(story.slug, "the-ancient-fire-of-gorakhpur")

    def test_story_slug_uniqueness(self):
        """Duplicate titles should generate unique slugs."""
        s1 = Story.objects.create(
            title="Duplicate Story", pull_quote="Q", lead_paragraph="L",
            body_content="B", artisan=self.artisan
        )
        s2 = Story.objects.create(
            title="Duplicate Story", pull_quote="Q", lead_paragraph="L",
            body_content="B", artisan=self.artisan
        )
        self.assertNotEqual(s1.slug, s2.slug)

    def test_story_str(self):
        story = Story.objects.create(
            title="Test Story", volume_tag="Vol. 01",
            pull_quote="Q", lead_paragraph="L", body_content="B"
        )
        self.assertEqual(str(story), "Test Story (Vol. 01)")

    def test_story_related_products(self):
        """ManyToMany related_products should work."""
        story = Story.objects.create(
            title="Related Story", pull_quote="Q",
            lead_paragraph="L", body_content="B"
        )
        story.related_products.add(self.product)
        self.assertIn(self.product, story.related_products.all())

    def test_story_ordering(self):
        self.assertEqual(Story._meta.ordering, ["-is_featured", "-created_at"])

    def test_story_defaults(self):
        story = Story.objects.create(
            title="Defaults Test", pull_quote="Q",
            lead_paragraph="L", body_content="B"
        )
        self.assertEqual(story.author_name, "Devraj Kumhar")
        self.assertEqual(story.reading_time, "5 min read")
        self.assertTrue(story.is_published)
        self.assertFalse(story.is_featured)


# =============================================================================
# VIEW TESTS — HOME, CATALOG, DETAIL
# =============================================================================

class HomeViewTests(TestCase):
    """Tests for the HomeView."""

    def setUp(self):
        self.artisan_user = User.objects.create_user(username="hv_artisan", password="p")
        self.artisan = ArtisanProfile.objects.create(
            user=self.artisan_user, display_name="HV Studio",
            craft_speciality="Pottery", is_approved=True
        )
        self.category = Category.objects.create(name="HV Cat", slug="hv-cat")
        self.product = Product.objects.create(
            artisan=self.artisan, category=self.category,
            title="Home Product", description="D",
            price=Decimal("500.00"), stock_quantity=5,
            is_approved=True, is_available=True
        )

    def test_home_view_200(self):
        response = self.client.get(reverse("marketplace:home"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "marketplace/home.html")
        self.assertTemplateUsed(response, "base.html")

    def test_home_view_context(self):
        response = self.client.get(reverse("marketplace:home"))
        for key in ["featured_products", "categories", "search_form",
                     "recently_viewed_products", "last_viewed_craft"]:
            self.assertIn(key, response.context, f"Missing key: {key}")

    def test_home_view_shows_featured_products(self):
        response = self.client.get(reverse("marketplace:home"))
        self.assertContains(response, self.product.title)


class ProductCatalogViewTests(TestCase):
    """Tests for ProductCatalogView."""

    def setUp(self):
        self.artisan_user = User.objects.create_user(username="cat_artisan", password="p")
        self.artisan = ArtisanProfile.objects.create(
            user=self.artisan_user, display_name="Cat Studio",
            craft_speciality="Pottery", is_approved=True
        )
        self.category = Category.objects.create(name="Ceramics", slug="ceramics")
        self.product = Product.objects.create(
            artisan=self.artisan, category=self.category,
            title="Catalog Vase", description="Beautiful vase.",
            price=Decimal("1500.00"), stock_quantity=5,
            is_approved=True, is_available=True
        )

    def test_catalog_200(self):
        response = self.client.get(reverse("marketplace:product_catalog"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "marketplace/product_catalog.html")

    def test_catalog_shows_product(self):
        response = self.client.get(reverse("marketplace:product_catalog"))
        self.assertContains(response, "Catalog Vase")

    def test_catalog_category_filter(self):
        """Category filter should narrow results."""
        other_cat = Category.objects.create(name="Woodwork", slug="woodwork")
        Product.objects.create(
            artisan=self.artisan, category=other_cat,
            title="Wood Box", description="Carved.",
            price=Decimal("1000.00"), stock_quantity=3,
            is_approved=True, is_available=True
        )
        response = self.client.get(reverse("marketplace:product_catalog") + "?category=ceramics")
        self.assertContains(response, "Catalog Vase")
        self.assertNotContains(response, "Wood Box")

    def test_catalog_ordering_price_asc(self):
        Product.objects.create(
            artisan=self.artisan, category=self.category,
            title="Cheap Item", description="D",
            price=Decimal("100.00"), stock_quantity=5,
            is_approved=True, is_available=True
        )
        response = self.client.get(reverse("marketplace:product_catalog") + "?ordering=price_asc")
        self.assertEqual(response.status_code, 200)

    @patch("marketplace.ai_service.call_llm_chat", return_value=None)
    def test_catalog_search(self, mock_llm):
        """Search by query term."""
        response = self.client.get(reverse("marketplace:product_catalog") + "?q=vase")
        self.assertEqual(response.status_code, 200)


class ProductDetailViewTests(TestCase):
    """Tests for ProductDetailView."""

    def setUp(self):
        self.artisan_user = User.objects.create_user(username="det_artisan", password="p")
        self.artisan = ArtisanProfile.objects.create(
            user=self.artisan_user, display_name="Detail Studio",
            craft_speciality="Pottery", is_approved=True
        )
        self.category = Category.objects.create(name="Det Cat", slug="det-cat")
        self.product = Product.objects.create(
            artisan=self.artisan, category=self.category,
            title="Detail Product", slug="detail-product",
            description="Detailed description.",
            price=Decimal("2000.00"), stock_quantity=5,
            is_approved=True, is_available=True
        )

    def test_detail_200(self):
        response = self.client.get(
            reverse("marketplace:product_detail", kwargs={"slug": "detail-product"})
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "marketplace/product_detail.html")

    def test_detail_context(self):
        response = self.client.get(
            reverse("marketplace:product_detail", kwargs={"slug": "detail-product"})
        )
        for key in ["product", "related_products", "artisan_creations",
                     "is_saved", "enquiry_form", "buy_form"]:
            self.assertIn(key, response.context, f"Missing key: {key}")

    def test_unapproved_returns_404(self):
        unapproved = Product.objects.create(
            artisan=self.artisan, category=self.category,
            title="Hidden Draft", slug="hidden-draft",
            description="Private.", price=Decimal("999.00"),
            stock_quantity=2, is_available=True, is_approved=False
        )
        response = self.client.get(
            reverse("marketplace:product_detail", kwargs={"slug": "hidden-draft"})
        )
        self.assertEqual(response.status_code, 404)

    def test_session_recently_viewed(self):
        """Session should track recently viewed crafts."""
        response = self.client.get(
            reverse("marketplace:product_detail", kwargs={"slug": "detail-product"})
        )
        session = self.client.session
        self.assertIn("recently_viewed_crafts", session)
        self.assertIn(self.product.id, session["recently_viewed_crafts"])

    def test_session_total_craft_views(self):
        """Session should track total craft views."""
        self.client.get(
            reverse("marketplace:product_detail", kwargs={"slug": "detail-product"})
        )
        self.client.get(
            reverse("marketplace:product_detail", kwargs={"slug": "detail-product"})
        )
        session = self.client.session
        self.assertEqual(session["total_craft_views"], 2)

    def test_cookie_set(self):
        """Response should set last_viewed_craft_slug cookie."""
        response = self.client.get(
            reverse("marketplace:product_detail", kwargs={"slug": "detail-product"})
        )
        self.assertIn("last_viewed_craft_slug", response.cookies)
        self.assertEqual(
            response.cookies["last_viewed_craft_slug"].value,
            "detail-product"
        )

    def test_is_saved_for_authenticated_user(self):
        """is_saved should be True when user has saved the product."""
        buyer = User.objects.create_user(username="saver", password="p")
        SavedProduct.objects.create(buyer=buyer, product=self.product)
        self.client.login(username="saver", password="p")
        response = self.client.get(
            reverse("marketplace:product_detail", kwargs={"slug": "detail-product"})
        )
        self.assertTrue(response.context["is_saved"])


class CategoryDetailViewTests(TestCase):
    """Tests for CategoryDetailView."""

    def setUp(self):
        self.artisan_user = User.objects.create_user(username="cd_artisan", password="p")
        self.artisan = ArtisanProfile.objects.create(
            user=self.artisan_user, display_name="CD Studio",
            craft_speciality="Pottery", is_approved=True
        )
        self.category = Category.objects.create(name="CD Ceramics", slug="cd-ceramics")
        self.product = Product.objects.create(
            artisan=self.artisan, category=self.category,
            title="Category Product", description="D",
            price=Decimal("500.00"), stock_quantity=5,
            is_approved=True, is_available=True
        )

    def test_category_detail_200(self):
        response = self.client.get(
            reverse("marketplace:category_detail", kwargs={"slug": "cd-ceramics"})
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Category Product")

    def test_nonexistent_category_404(self):
        response = self.client.get("/genres/nonexistent/")
        self.assertEqual(response.status_code, 404)


# =============================================================================
# REGEX URL VIEW TESTS
# =============================================================================

class CraftArchiveYearViewTests(TestCase):
    """Tests for CraftArchiveYearView (regex URL)."""

    def setUp(self):
        self.artisan_user = User.objects.create_user(username="arch_artisan", password="p")
        self.artisan = ArtisanProfile.objects.create(
            user=self.artisan_user, display_name="Arch Studio",
            craft_speciality="Pottery", is_approved=True, is_verified=True
        )
        self.category = Category.objects.create(name="Arch Cat", slug="arch-cat")
        self.product = Product.objects.create(
            artisan=self.artisan, category=self.category,
            title="Archive Product", description="D",
            price=Decimal("500.00"), stock_quantity=5,
            is_approved=True, is_available=True
        )

    def test_archive_year_200(self):
        year = str(self.product.created_at.year)
        url = reverse("marketplace:craft_archive_year", kwargs={"year": year})
        self.assertEqual(url, f"/archive/{year}/")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.product.title)

    def test_archive_year_context(self):
        year = str(self.product.created_at.year)
        response = self.client.get(f"/archive/{year}/")
        self.assertIn("archive_year", response.context)


class ProvenanceLookupViewTests(TestCase):
    """Tests for ProvenanceLookupView (regex URL)."""

    def setUp(self):
        self.artisan_user = User.objects.create_user(username="prov_artisan", password="p")
        self.artisan = ArtisanProfile.objects.create(
            user=self.artisan_user, display_name="Prov Studio",
            craft_speciality="Pottery", is_approved=True, is_verified=True
        )
        self.category = Category.objects.create(name="Prov Cat", slug="prov-cat")
        self.product = Product.objects.create(
            artisan=self.artisan, category=self.category,
            title="Provenance Product", description="D",
            price=Decimal("500.00"), stock_quantity=5,
            is_approved=True, is_available=True
        )

    def test_provenance_lookup_200(self):
        batch_code = f"CC-{self.product.id}"
        url = reverse("marketplace:provenance_lookup", kwargs={"batch_code": batch_code})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)


# =============================================================================
# ENQUIRY, BUY, SAVE VIEW TESTS
# =============================================================================

class ProductEnquiryViewTests(TestCase):
    """Tests for ProductEnquiryView."""

    def setUp(self):
        self.artisan_user = User.objects.create_user(username="pe_artisan", password="p")
        self.artisan = ArtisanProfile.objects.create(
            user=self.artisan_user, display_name="PE Studio",
            craft_speciality="Pottery", is_approved=True
        )
        self.buyer = User.objects.create_user(username="pe_buyer", password="p")
        self.category = Category.objects.create(name="PE Cat", slug="pe-cat")
        self.product = Product.objects.create(
            artisan=self.artisan, category=self.category,
            title="PE Product", slug="pe-product", description="D",
            price=Decimal("500.00"), stock_quantity=5,
            is_approved=True, is_available=True
        )

    def test_unauthenticated_redirect(self):
        response = self.client.post(
            reverse("marketplace:product_enquiry", kwargs={"slug": "pe-product"}),
            {"subject": "Question", "message": "Tell me more about this."}
        )
        self.assertEqual(response.status_code, 302)

    def test_valid_enquiry_submission(self):
        self.client.login(username="pe_buyer", password="p")
        response = self.client.post(
            reverse("marketplace:product_enquiry", kwargs={"slug": "pe-product"}),
            {"subject": "Dimensions Question", "message": "Can I get this in 2.5m length?"}
        )
        self.assertRedirects(
            response,
            reverse("marketplace:product_detail", kwargs={"slug": "pe-product"})
        )
        self.assertEqual(Enquiry.objects.count(), 1)
        self.assertEqual(Enquiry.objects.first().buyer, self.buyer)

    def test_invalid_enquiry_redirects(self):
        self.client.login(username="pe_buyer", password="p")
        response = self.client.post(
            reverse("marketplace:product_enquiry", kwargs={"slug": "pe-product"}),
            {"subject": "Hi", "message": "Short"}
        )
        self.assertRedirects(
            response,
            reverse("marketplace:product_detail", kwargs={"slug": "pe-product"})
        )
        self.assertEqual(Enquiry.objects.count(), 0)


class ProductBuyAndOrderTests(TestCase):
    """Tests for ProductBuyView — full purchase lifecycle."""

    def setUp(self):
        self.artisan_user = User.objects.create_user(
            username="buy_artisan", password="password123"
        )
        self.artisan = ArtisanProfile.objects.create(
            user=self.artisan_user, display_name="Buy Studio",
            craft_speciality="Ajrakh", is_approved=True
        )
        self.buyer = User.objects.create_user(
            username="buy_buyer", password="password123"
        )
        self.category = Category.objects.create(name="Buy Cat", slug="buy-cat")
        self.product = Product.objects.create(
            artisan=self.artisan, category=self.category,
            title="Ajrakh Silk Dupatta", slug="ajrakh-silk-dupatta",
            description="Pure silk.", price=Decimal("3000.00"),
            stock_quantity=3, is_available=True, is_approved=True
        )

    def _buy_data(self, quantity=1, payment="UPI / Direct Bank Remittance"):
        return {
            "quantity": quantity,
            "shipping_address": "Flat 101, Green Meadows",
            "shipping_city": "Mumbai",
            "shipping_postal_code": "400001",
            "contact_phone": "+91 99887 76655",
            "payment_method": payment,
        }

    def test_buy_unauthenticated_redirect(self):
        url = reverse("marketplace:product_buy", kwargs={"slug": "ajrakh-silk-dupatta"})
        response = self.client.post(url, self._buy_data())
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith(reverse("accounts:auth")))

    def test_buy_successful(self):
        """Authenticated buyer buys 2 pieces: stock decreases, order created, 88% share."""
        self.client.login(username="buy_buyer", password="password123")
        url = reverse("marketplace:product_buy", kwargs={"slug": "ajrakh-silk-dupatta"})
        response = self.client.post(url, self._buy_data(quantity=2))
        self.assertRedirects(response, reverse("accounts:buyer_dashboard"))

        order = Order.objects.get(buyer=self.buyer, product=self.product)
        self.assertEqual(order.quantity, 2)
        self.assertEqual(order.unit_price, Decimal("3000.00"))
        self.assertEqual(order.total_price, Decimal("6000.00"))
        self.assertEqual(order.artisan_share, Decimal("5280.00"))
        self.assertEqual(order.shipping_city, "Mumbai")

        self.product.refresh_from_db()
        self.assertEqual(self.product.stock_quantity, 1)
        self.assertTrue(self.product.is_available)

    def test_buy_depletes_stock_marks_unavailable(self):
        """Buying all stock sets is_available=False and stock=0."""
        self.client.login(username="buy_buyer", password="password123")
        url = reverse("marketplace:product_buy", kwargs={"slug": "ajrakh-silk-dupatta"})
        response = self.client.post(url, self._buy_data(quantity=3))
        self.assertRedirects(response, reverse("accounts:buyer_dashboard"))
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock_quantity, 0)
        self.assertFalse(self.product.is_available)

    def test_buy_insufficient_stock(self):
        """Requesting more than available stock is rejected."""
        self.client.login(username="buy_buyer", password="password123")
        url = reverse("marketplace:product_buy", kwargs={"slug": "ajrakh-silk-dupatta"})
        response = self.client.post(url, self._buy_data(quantity=5))
        self.assertRedirects(
            response,
            reverse("marketplace:product_detail", kwargs={"slug": "ajrakh-silk-dupatta"})
        )
        self.assertEqual(Order.objects.filter(buyer=self.buyer).count(), 0)
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock_quantity, 3)

    def test_buy_invalid_form(self):
        """Invalid form (missing address) should redirect without creating order."""
        self.client.login(username="buy_buyer", password="password123")
        url = reverse("marketplace:product_buy", kwargs={"slug": "ajrakh-silk-dupatta"})
        response = self.client.post(url, {
            "quantity": 1,
            "shipping_address": "Hi",  # too short
            "shipping_city": "M",
            "shipping_postal_code": "400001",
            "contact_phone": "+91",
            "payment_method": "UPI / Direct Bank Remittance",
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Order.objects.count(), 0)

    def test_buy_form_valid(self):
        """BuyOrderForm accepts valid data."""
        form = BuyOrderForm(data=self._buy_data(quantity=2))
        self.assertTrue(form.is_valid())

    def test_buy_form_invalid_quantity_zero(self):
        form = BuyOrderForm(data=self._buy_data(quantity=0))
        self.assertFalse(form.is_valid())
        self.assertIn("quantity", form.errors)

    def test_buy_form_short_address(self):
        data = self._buy_data()
        data["shipping_address"] = "Hi"
        form = BuyOrderForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn("shipping_address", form.errors)


class ToggleSaveProductViewTests(TestCase):
    """Tests for ToggleSaveProductView."""

    def setUp(self):
        self.artisan_user = User.objects.create_user(username="ts_artisan", password="p")
        self.artisan = ArtisanProfile.objects.create(
            user=self.artisan_user, display_name="TS Studio",
            craft_speciality="Pottery", is_approved=True
        )
        self.buyer = User.objects.create_user(username="ts_buyer", password="p")
        self.category = Category.objects.create(name="TS Cat", slug="ts-cat")
        self.product = Product.objects.create(
            artisan=self.artisan, category=self.category,
            title="TS Product", slug="ts-product", description="D",
            price=Decimal("500.00"), stock_quantity=5,
            is_approved=True, is_available=True
        )

    def test_unauthenticated_redirect(self):
        response = self.client.post(
            reverse("marketplace:toggle_save", kwargs={"slug": "ts-product"})
        )
        self.assertEqual(response.status_code, 302)

    def test_save_product(self):
        self.client.login(username="ts_buyer", password="p")
        response = self.client.post(
            reverse("marketplace:toggle_save", kwargs={"slug": "ts-product"})
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(SavedProduct.objects.filter(buyer=self.buyer, product=self.product).exists())

    def test_unsave_product(self):
        """Toggle again should remove the saved product."""
        SavedProduct.objects.create(buyer=self.buyer, product=self.product)
        self.client.login(username="ts_buyer", password="p")
        self.client.post(
            reverse("marketplace:toggle_save", kwargs={"slug": "ts-product"})
        )
        self.assertFalse(SavedProduct.objects.filter(buyer=self.buyer, product=self.product).exists())


# =============================================================================
# EDITORIAL JOURNAL STORY TESTS
# =============================================================================

class EditorialJournalStoryTests(TestCase):
    """Tests for Story views."""

    def setUp(self):
        self.artisan_user = User.objects.create_user(
            username="test_artisan_writer", password="testpassword123"
        )
        self.artisan_profile = ArtisanProfile.objects.create(
            user=self.artisan_user, display_name="Kutch Terracotta Atelier",
            is_approved=True, craft_speciality="Pottery"
        )
        self.category = Category.objects.create(name="Ceramics & Fire", slug="ceramics-fire")
        self.product = Product.objects.create(
            artisan=self.artisan_profile, category=self.category,
            title="Hand-Thrown Earthen Teacup", slug="hand-thrown-earthen-teacup",
            description="Clay teacup", price=Decimal("450.00"),
            stock_quantity=10, is_available=True, is_approved=True,
        )
        self.story = Story.objects.create(
            title="The Earth remembers the hand that turns it.",
            volume_tag="Editorial Journal • Vol. 04",
            pull_quote="In an era of rapid production, slow craft is cultural preservation.",
            author_name="Devraj Kumhar", author_role="Master Potter, Kutch Guild",
            reading_time="5 min read", craft_region="Kutch, Gujarat",
            category="Ceramics & Terracotta",
            lead_paragraph="Devraj Kumhar's family has worked the Kutch salt-clay for two hundred years.",
            body_content="Full story body content about clay and pottery.",
            is_featured=True, is_published=True, artisan=self.artisan_profile,
        )
        self.story.related_products.add(self.product)

    def test_story_list_view(self):
        response = self.client.get(reverse("marketplace:story_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.story.title)
        self.assertContains(response, "Editorial Journal • Vol. 04")
        self.assertContains(response, "Devraj Kumhar")

    def test_story_list_category_filter(self):
        response = self.client.get(
            reverse("marketplace:story_list") + "?category=Ceramics & Terracotta"
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.story.title)

    def test_story_list_empty_category(self):
        response = self.client.get(
            reverse("marketplace:story_list") + "?category=NonExistent"
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "0 Selected Stories")

    def test_story_detail_view(self):
        url = reverse("marketplace:story_detail", kwargs={"slug": self.story.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.story.title)
        self.assertContains(response, "In an era of rapid production")
        self.assertContains(response, self.product.title)

    def test_unpublished_story_404(self):
        self.story.is_published = False
        self.story.save()
        url = reverse("marketplace:story_detail", kwargs={"slug": self.story.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_home_view_spotlight_story(self):
        response = self.client.get(reverse("marketplace:home"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.story.title)

    def test_story_detail_more_stories(self):
        """Detail page should include other stories in more_stories."""
        other = Story.objects.create(
            title="Other Story", pull_quote="Q",
            lead_paragraph="L", body_content="B",
            is_published=True
        )
        url = reverse("marketplace:story_detail", kwargs={"slug": self.story.slug})
        response = self.client.get(url)
        self.assertIn("more_stories", response.context)


# =============================================================================
# TEMPLATE TAG TESTS
# =============================================================================

class CraftExtrasTemplateTagTests(TestCase):
    """Tests for custom template tags and filters in craft_extras.py."""

    def test_inr_format_whole_number(self):
        from marketplace.templatetags.craft_extras import inr_format
        self.assertEqual(inr_format(4200), "₹4,200")
        self.assertEqual(inr_format(0), "₹0")
        self.assertEqual(inr_format(100), "₹100")
        self.assertEqual(inr_format(12500), "₹12,500")

    def test_inr_format_decimal(self):
        from marketplace.templatetags.craft_extras import inr_format
        self.assertEqual(inr_format(1850.50), "₹1,850.50")
        self.assertEqual(inr_format(99.99), "₹99.99")

    def test_inr_format_invalid(self):
        from marketplace.templatetags.craft_extras import inr_format
        self.assertEqual(inr_format("not a number"), "not a number")
        self.assertEqual(inr_format(None), None)

    def test_artisan_initials_two_words(self):
        from marketplace.templatetags.craft_extras import artisan_initials
        self.assertEqual(artisan_initials("Suresh Silk Looms"), "SS")
        self.assertEqual(artisan_initials("Kutch Clay Works"), "KC")

    def test_artisan_initials_single_word(self):
        from marketplace.templatetags.craft_extras import artisan_initials
        self.assertEqual(artisan_initials("Terracotta"), "TE")

    def test_artisan_initials_empty(self):
        from marketplace.templatetags.craft_extras import artisan_initials
        self.assertEqual(artisan_initials(""), "CC")
        self.assertEqual(artisan_initials(None), "CC")

    def test_verified_maker_badge_true(self):
        from marketplace.templatetags.craft_extras import verified_maker_badge
        badge = verified_maker_badge(True)
        self.assertIn("Verified Atelier", badge)
        self.assertIn("verified", badge)

    def test_verified_maker_badge_false(self):
        from marketplace.templatetags.craft_extras import verified_maker_badge
        badge = verified_maker_badge(False)
        self.assertIn("Under Review", badge)

    def test_stock_status_zero(self):
        from marketplace.templatetags.craft_extras import stock_status
        result = stock_status(0)
        self.assertIn("Out of Stock", result)

    def test_stock_status_low(self):
        from marketplace.templatetags.craft_extras import stock_status
        result = stock_status(2)
        self.assertIn("Only 2 left", result)

    def test_stock_status_boundary_3(self):
        from marketplace.templatetags.craft_extras import stock_status
        result = stock_status(3)
        self.assertIn("Only 3 left", result)

    def test_stock_status_high(self):
        from marketplace.templatetags.craft_extras import stock_status
        result = stock_status(10)
        self.assertIn("In Studio Stock", result)

    def test_stock_status_invalid(self):
        from marketplace.templatetags.craft_extras import stock_status
        result = stock_status("invalid")
        self.assertEqual(result, "")


# =============================================================================
# GROUPS & PERMISSIONS TESTS
# =============================================================================

class GroupsAndPermissionsTests(TestCase):
    """Tests for Django Groups and Permissions (Syllabus Unit V)."""

    def test_setup_groups_command(self):
        """setup_groups_and_permissions command creates correct groups."""
        call_command("setup_groups_and_permissions")
        self.assertTrue(Group.objects.filter(name="Artisans").exists())
        self.assertTrue(Group.objects.filter(name="Patrons").exists())
        self.assertTrue(Group.objects.filter(name="Guild_Curators").exists())

    def test_artisan_group_has_product_permissions(self):
        call_command("setup_groups_and_permissions")
        artisan_group = Group.objects.get(name="Artisans")
        self.assertTrue(artisan_group.permissions.filter(codename="add_product").exists())
        self.assertTrue(artisan_group.permissions.filter(codename="change_product").exists())
        self.assertTrue(artisan_group.permissions.filter(codename="view_product").exists())

    def test_patron_group_has_enquiry_permissions(self):
        call_command("setup_groups_and_permissions")
        patron_group = Group.objects.get(name="Patrons")
        self.assertTrue(patron_group.permissions.filter(codename="add_enquiry").exists())
        self.assertTrue(patron_group.permissions.filter(codename="view_enquiry").exists())

    def test_patron_group_has_savedproduct_permissions(self):
        call_command("setup_groups_and_permissions")
        patron_group = Group.objects.get(name="Patrons")
        self.assertTrue(patron_group.permissions.filter(codename="add_savedproduct").exists())
        self.assertTrue(patron_group.permissions.filter(codename="delete_savedproduct").exists())

    def test_curator_group_has_all_permissions(self):
        call_command("setup_groups_and_permissions")
        curator_group = Group.objects.get(name="Guild_Curators")
        self.assertTrue(curator_group.permissions.count() > 0)

    def test_idempotent_command(self):
        """Running the command twice should not cause errors."""
        call_command("setup_groups_and_permissions")
        call_command("setup_groups_and_permissions")
        self.assertEqual(Group.objects.filter(name="Artisans").count(), 1)


# =============================================================================
# AI SERVICE TESTS
# =============================================================================

@patch("marketplace.ai_service.call_llm_chat", return_value=None)
class AIServiceTests(TestCase):
    """Tests for ai_service.py heuristic fallback and smart discovery."""

    def setUp(self):
        self.artisan_user = User.objects.create_user(username="ai_artisan", password="p")
        self.artisan = ArtisanProfile.objects.create(
            user=self.artisan_user, display_name="AI Studio",
            craft_speciality="Pottery", is_approved=True
        )
        self.category = Category.objects.create(name="Ceramics & Terracotta", slug="ceramics-terracotta")
        self.product = Product.objects.create(
            artisan=self.artisan, category=self.category,
            title="Terracotta Chai Kulhad", description="Wheel-thrown clay chai cup.",
            price=Decimal("350.00"), material="Terracotta Clay",
            stock_quantity=10, is_approved=True, is_available=True
        )

    def test_llm_success_path(self, mock_llm):
        """When LLM returns valid JSON, it should be extracted and used."""
        import json
        mock_llm.return_value = json.dumps({
            "suggested_title": "Artisanal Terracotta Vase",
            "suggested_description": "Hand-burnished earthen vase shaped by generational wisdom.",
            "suggested_category": "Ceramics & Terracotta",
            "suggested_tags": "vase, clay, handmade",
            "suggested_price": "2200.00",
        })
        from marketplace.ai_service import generate_catalogue_assistant_suggestions
        result = generate_catalogue_assistant_suggestions(
            title="Vase", raw_notes="Clay", material="Clay"
        )
        self.assertEqual(result["suggested_title"], "Artisanal Terracotta Vase")
        self.assertEqual(result["suggested_price"], "2200.00")

    def test_smart_craft_discovery_with_llm(self, mock_llm):
        """When LLM returns semantic decomposition, it should be incorporated."""
        import json
        mock_llm.return_value = json.dumps({
            "keywords": ["terracotta", "chai"],
            "suggested_category": "Ceramics & Terracotta",
            "ai_explanation": "Matching authentic earthen pieces."
        })
        from marketplace.ai_service import smart_craft_discovery
        result = smart_craft_discovery("terracotta chai cup")
        self.assertEqual(result["ai_explanation"], "Matching authentic earthen pieces.")

    def test_heuristic_fallback_ceramics(self, mock_llm):
        """Heuristic engine should detect ceramics category."""
        from marketplace.ai_service import generate_catalogue_assistant_suggestions
        result = generate_catalogue_assistant_suggestions(
            title="Clay Cup", raw_notes="terracotta",
            material="Clay", category_name="Ceramics"
        )
        self.assertEqual(result["suggested_category"], "Ceramics & Terracotta")
        self.assertIn("suggested_title", result)
        self.assertIn("suggested_tags", result)
        self.assertIn("confidence_score", result)

    def test_heuristic_fallback_textiles(self, mock_llm):
        from marketplace.ai_service import generate_catalogue_assistant_suggestions
        result = generate_catalogue_assistant_suggestions(
            title="Silk Saree", raw_notes="handloom silk",
            material="Mulberry Silk"
        )
        self.assertEqual(result["suggested_category"], "Textiles & Handloom")

    def test_heuristic_fallback_metalcraft(self, mock_llm):
        from marketplace.ai_service import generate_catalogue_assistant_suggestions
        result = generate_catalogue_assistant_suggestions(
            title="Dhokra Figure", raw_notes="lost-wax brass",
            material="Brass"
        )
        self.assertEqual(result["suggested_category"], "Metalcraft & Dhokra")

    def test_heuristic_fallback_woodwork(self, mock_llm):
        from marketplace.ai_service import generate_catalogue_assistant_suggestions
        result = generate_catalogue_assistant_suggestions(
            title="Teak Box", raw_notes="carved wood",
            material="Teak"
        )
        self.assertEqual(result["suggested_category"], "Woodwork & Carving")

    def test_heuristic_fallback_generic(self, mock_llm):
        from marketplace.ai_service import generate_catalogue_assistant_suggestions
        result = generate_catalogue_assistant_suggestions(
            title="Mystery Item", raw_notes="unique craft",
            material="Unknown"
        )
        self.assertEqual(result["suggested_category"], "Heritage Crafts")

    def test_heuristic_returns_price(self, mock_llm):
        from marketplace.ai_service import generate_catalogue_assistant_suggestions
        result = generate_catalogue_assistant_suggestions(
            title="Clay pot", raw_notes="terracotta", material="clay"
        )
        self.assertIn("suggested_price", result)
        float(result["suggested_price"])

    def test_smart_craft_discovery_empty_query(self, mock_llm):
        """Empty query should return all public products."""
        from marketplace.ai_service import smart_craft_discovery
        result = smart_craft_discovery("")
        self.assertIn("products", result)
        self.assertIn("parsed_intent", result)

    def test_smart_craft_discovery_keyword_match(self, mock_llm):
        """Keyword query should find matching products."""
        from marketplace.ai_service import smart_craft_discovery
        result = smart_craft_discovery("terracotta chai cup")
        self.assertIn("products", result)
        self.assertIn("extracted_keywords", result)
        self.assertIn("ai_explanation", result)

    def test_smart_craft_discovery_genre_match(self, mock_llm):
        """Genre keywords should match to categories."""
        from marketplace.ai_service import smart_craft_discovery
        result = smart_craft_discovery("pottery ceramic")
        self.assertEqual(result["suggested_category"], "Pottery")

    def test_safe_extract_json_valid(self, mock_llm):
        from marketplace.ai_service import safe_extract_json
        result = safe_extract_json('{"key": "value"}')
        self.assertEqual(result, {"key": "value"})

    def test_safe_extract_json_with_fences(self, mock_llm):
        from marketplace.ai_service import safe_extract_json
        text = '```json\n{"key": "value"}\n```'
        result = safe_extract_json(text)
        self.assertEqual(result, {"key": "value"})

    def test_safe_extract_json_with_surrounding_text(self, mock_llm):
        from marketplace.ai_service import safe_extract_json
        text = 'Here is the JSON: {"key": "value"} done.'
        result = safe_extract_json(text)
        self.assertEqual(result, {"key": "value"})

    def test_safe_extract_json_none(self, mock_llm):
        from marketplace.ai_service import safe_extract_json
        self.assertIsNone(safe_extract_json(None))
        self.assertIsNone(safe_extract_json(""))

    def test_safe_extract_json_invalid(self, mock_llm):
        from marketplace.ai_service import safe_extract_json
        self.assertIsNone(safe_extract_json("not json at all"))

    def test_get_ai_config(self, mock_llm):
        from marketplace.ai_service import get_ai_config
        config = get_ai_config()
        self.assertIn("provider", config)
        self.assertIn("base_url", config)
        self.assertIn("api_key", config)
        self.assertIn("model", config)


# =============================================================================
# CUSTOM ERROR HANDLER CONFIG TESTS
# =============================================================================

class ErrorHandlerTests(SimpleTestCase):
    """Verify custom error handlers are configured."""

    def test_404_handler_configured(self):
        from craftconnect.urls import handler404
        self.assertEqual(handler404, "marketplace.views.custom_404_view")

    def test_500_handler_configured(self):
        from craftconnect.urls import handler500
        self.assertEqual(handler500, "marketplace.views.custom_500_view")


# =============================================================================
# ADMIN REGISTRATION TESTS
# =============================================================================

class AdminRegistrationTests(TestCase):
    """Verify models are registered in Django admin."""

    def test_category_admin_registered(self):
        from django.contrib.admin.sites import site
        self.assertIn(Category, site._registry)

    def test_product_admin_registered(self):
        from django.contrib.admin.sites import site
        self.assertIn(Product, site._registry)

    def test_order_admin_registered(self):
        from django.contrib.admin.sites import site
        self.assertIn(Order, site._registry)

    def test_story_admin_registered(self):
        from django.contrib.admin.sites import site
        self.assertIn(Story, site._registry)

    def test_artisan_profile_admin_registered(self):
        from django.contrib.admin.sites import site
        self.assertIn(ArtisanProfile, site._registry)
