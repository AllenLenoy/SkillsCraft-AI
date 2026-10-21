from decimal import Decimal
from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import TemplateView, ListView, DetailView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.db.models import Q
from .models import Category, Product, SavedProduct, Enquiry, Story, Order
from .forms import ProductSearchForm, EnquiryForm, BuyOrderForm


class HomeView(TemplateView):
    """
    CraftConnect Public Homepage.
    Features the editorial hero section, Smart Craft Discovery search bar,
    curated craft categories, and public featured creations.
    Implements Django Session and Cookie state reading (Syllabus Unit VI).
    """
    template_name = "marketplace/home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Only publicly visible items (approved, available, in-stock, approved artisan)
        context["featured_products"] = (
            Product.objects.public()
            .select_related("artisan", "category")[:6]
        )
        context["categories"] = Category.objects.all()
        context["search_form"] = ProductSearchForm()

        # Editorial Journal featured story
        context["featured_story"] = (
            Story.objects.filter(is_published=True, is_featured=True).first()
            or Story.objects.filter(is_published=True).first()
        )

        # Syllabus Unit VI: Django Sessions - Retrieve recently viewed items from session
        recent_ids = self.request.session.get("recently_viewed_crafts", [])
        if recent_ids:
            # Preserve order from session
            recent_qs = Product.objects.public().filter(id__in=recent_ids).select_related("artisan", "category")
            recent_map = {p.id: p for p in recent_qs}
            context["recently_viewed_products"] = [recent_map[pid] for pid in recent_ids if pid in recent_map]
        else:
            context["recently_viewed_products"] = []

        # Syllabus Unit VI: Django Cookies - Retrieve client cookie for last viewed craft
        last_viewed_slug = self.request.COOKIES.get("last_viewed_craft_slug")
        if last_viewed_slug:
            context["last_viewed_craft"] = (
                Product.objects.public()
                .filter(slug=last_viewed_slug)
                .select_related("artisan")
                .first()
            )
        else:
            context["last_viewed_craft"] = None

        return context


class ProductCatalogView(ListView):
    """
    Dynamic product catalogue with search and category filtering.
    Strictly filters against the public queryset to ensure no unapproved,
    unavailable, or out-of-stock listings are ever exposed.
    """
    model = Product
    template_name = "marketplace/product_catalog.html"
    context_object_name = "products"
    paginate_by = 9

    def get_queryset(self):
        q = self.request.GET.get("q", "").strip()
        category_slug = self.request.GET.get("category", "").strip()
        material = self.request.GET.get("material", "").strip()
        ordering = self.request.GET.get("ordering", "-created_at")

        # If natural language query is provided, use Smart Craft Discovery
        if q:
            from .ai_service import smart_craft_discovery
            discovery_result = smart_craft_discovery(q)
            self.discovery_result = discovery_result
            queryset = discovery_result["products"]
            if hasattr(queryset, "all"):
                # QuerySet
                if category_slug:
                    queryset = queryset.filter(category__slug=category_slug)
                if material:
                    queryset = queryset.filter(material__icontains=material)
            return queryset

        self.discovery_result = None
        queryset = Product.objects.public().select_related("artisan", "category")

        if category_slug:
            queryset = queryset.filter(category__slug=category_slug)

        if material:
            queryset = queryset.filter(material__icontains=material)

        ordering_map = {
            "price_asc": "price",
            "price_desc": "-price",
            "title_asc": "title",
            "-created_at": "-created_at",
        }
        return queryset.order_by(ordering_map.get(ordering, "-created_at"))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["categories"] = Category.objects.all()
        context["search_form"] = ProductSearchForm(self.request.GET or None)
        context["current_q"] = self.request.GET.get("q", "")
        context["current_category"] = self.request.GET.get("category", "")
        context["current_material"] = self.request.GET.get("material", "")
        context["current_ordering"] = self.request.GET.get("ordering", "-created_at")
        context["discovery_result"] = getattr(self, "discovery_result", None)

        # Syllabus Unit VI: Sessions in Catalogue
        recent_ids = self.request.session.get("recently_viewed_crafts", [])
        if recent_ids:
            recent_qs = Product.objects.public().filter(id__in=recent_ids).select_related("artisan")[:4]
            context["recently_viewed_products"] = recent_qs
        return context


class ProductDetailView(DetailView):
    """
    Editorial product showcase page.
    Guarantees public filtering: non-approved or unapproved-artisan items return a 404.
    Implements Django Session and Cookie manipulation (Syllabus Unit VI).
    """
    model = Product
    template_name = "marketplace/product_detail.html"
    context_object_name = "product"
    slug_field = "slug"
    slug_url_kwarg = "slug"

    def get_queryset(self):
        # Strict security: detail view only resolves for publicly approved items
        return Product.objects.public().select_related("artisan", "category")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product = self.object

        # Related craft pieces from the same category
        context["related_products"] = (
            Product.objects.public()
            .filter(category=product.category)
            .exclude(pk=product.pk)
            .select_related("artisan")[:3]
        )

        # Other creations from this artisan studio
        context["artisan_creations"] = (
            Product.objects.public()
            .filter(artisan=product.artisan)
            .exclude(pk=product.pk)[:3]
        )

        # Check if saved by current buyer
        user = self.request.user
        context["is_saved"] = (
            user.is_authenticated and
            SavedProduct.objects.filter(buyer=user, product=product).exists()
        )

        context["enquiry_form"] = EnquiryForm()
        context["buy_form"] = BuyOrderForm(initial={"quantity": 1})

        # Syllabus Unit VI: Django Sessions - update recently viewed craft IDs
        recently_viewed = self.request.session.get("recently_viewed_crafts", [])
        if product.id in recently_viewed:
            recently_viewed.remove(product.id)
        recently_viewed.insert(0, product.id)
        self.request.session["recently_viewed_crafts"] = recently_viewed[:8]
        self.request.session["total_craft_views"] = self.request.session.get("total_craft_views", 0) + 1
        self.request.session.modified = True

        return context

    def render_to_response(self, context, **response_kwargs):
        """
        Syllabus Unit VI: Django Cookies - Set persistent HTTP cookie
        identifying the user's latest viewed craft item.
        """
        response = super().render_to_response(context, **response_kwargs)
        product = self.object
        response.set_cookie(
            "last_viewed_craft_slug",
            product.slug,
            max_age=60 * 60 * 24 * 7,  # 7 days
            samesite="Lax"
        )
        return response


class CategoryDetailView(DetailView):
    """
    Dedicated view for a single craft genre and its public creations.
    """
    model = Category
    template_name = "marketplace/category_detail.html"
    context_object_name = "category"
    slug_field = "slug"
    slug_url_kwarg = "slug"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["products"] = (
            Product.objects.public()
            .filter(category=self.object)
            .select_related("artisan")
        )
        return context


class CraftArchiveYearView(ListView):
    """
    Syllabus Unit II: Regular expressions in URLs.
    Handles regex-routed archival queries such as /archive/(?P<year>[12][0-9]{3})/
    """
    model = Product
    template_name = "marketplace/product_catalog.html"
    context_object_name = "products"
    paginate_by = 9

    def get_queryset(self):
        year = self.kwargs.get("year")
        return (
            Product.objects.public()
            .filter(created_at__year=year)
            .select_related("artisan", "category")
            .order_by("-created_at")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["categories"] = Category.objects.all()
        context["search_form"] = ProductSearchForm()
        context["archive_year"] = self.kwargs.get("year")
        context["archive_title"] = f"Craft Provenance Archive &bull; Year {self.kwargs.get('year')}"
        return context


class ProvenanceLookupView(DetailView):
    r"""
    Syllabus Unit II: Regular expression URL mapping with SKU/Provenance code.
    Matches /provenance/(?P<batch_code>[A-Za-z]{2,5}-\d{3,6})/
    """
    model = Product
    template_name = "marketplace/product_detail.html"
    context_object_name = "product"

    def get_object(self, queryset=None):
        batch_code = self.kwargs.get("batch_code", "")
        # Resolve by ID or partial match
        try:
            parts = batch_code.split("-")
            pid = int(parts[-1])
            return get_object_or_404(Product.objects.public(), id=pid)
        except (ValueError, IndexError):
            return get_object_or_404(Product.objects.public(), slug__icontains=batch_code)


class ProductEnquiryView(LoginRequiredMixin, View):
    """
    Handles authenticated buyer inquiry submissions directly to the artisan.
    Implements POST redirect pattern and CSRF validation (Syllabus Unit IV).
    """
    def post(self, request, slug):
        product = get_object_or_404(Product.objects.public(), slug=slug)
        form = EnquiryForm(request.POST)
        if form.is_valid():
            enquiry = form.save(commit=False)
            enquiry.product = product
            enquiry.buyer = request.user
            enquiry.save()
            messages.success(
                request,
                f"Your inquiry regarding '{product.title}' has been sent to {product.artisan.display_name}."
            )
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field.capitalize()}: {error}")
        return redirect("marketplace:product_detail", slug=product.slug)


class ProductBuyView(LoginRequiredMixin, View):
    """
    Handles direct checkout and acquisition of handcrafted artisan creations.
    Verifies studio inventory, deducts available stock, allocates 88% direct
    remittance to the maker atelier, and generates an authentic Order record.
    """
    def post(self, request, slug):
        product = get_object_or_404(Product.objects.public(), slug=slug)

        if product.stock_quantity < 1 or not product.is_available:
            messages.error(
                request,
                f"We apologize, '{product.title}' is currently out of studio stock."
            )
            return redirect("marketplace:product_detail", slug=product.slug)

        form = BuyOrderForm(request.POST)
        if form.is_valid():
            quantity = form.cleaned_data["quantity"]
            if quantity > product.stock_quantity:
                messages.error(
                    request,
                    f"Only {product.stock_quantity} piece(s) available in studio stock."
                )
                return redirect("marketplace:product_detail", slug=product.slug)

            unit_price = product.price
            total_price = unit_price * quantity
            artisan_share = (total_price * Decimal("0.88")).quantize(Decimal("0.01"))

            order = form.save(commit=False)
            order.buyer = request.user
            order.product = product
            order.artisan = product.artisan
            order.unit_price = unit_price
            order.total_price = total_price
            order.artisan_share = artisan_share
            order.save()

            # Decrement inventory
            product.stock_quantity -= quantity
            if product.stock_quantity <= 0:
                product.is_available = False
                product.stock_quantity = 0
            product.save()

            messages.success(
                request,
                f"Craft acquisition confirmed! Order #{order.order_number} for '{product.title}' has been dispatched to {product.artisan.display_name}. "
                f"Direct remittance of ₹{artisan_share} (88%) is allocated to the village maker guild."
            )
            return redirect("accounts:buyer_dashboard")
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field.capitalize()}: {error}")
            return redirect("marketplace:product_detail", slug=product.slug)


class ToggleSaveProductView(LoginRequiredMixin, View):
    """
    Toggles saved bookmarks/wishlist for authenticated buyers.
    Prevents duplicate records using the database unique constraint.
    """
    def post(self, request, slug):
        product = get_object_or_404(Product.objects.public(), slug=slug)
        saved_qs = SavedProduct.objects.filter(buyer=request.user, product=product)

        if saved_qs.exists():
            saved_qs.delete()
            messages.info(request, f"'{product.title}' removed from your saved pieces.")
        else:
            SavedProduct.objects.create(buyer=request.user, product=product)
            messages.success(request, f"'{product.title}' added to your saved pieces.")

        # Redirect back to referring page or product detail
        next_url = request.POST.get("next") or request.META.get("HTTP_REFERER")
        return redirect(next_url or "marketplace:product_detail", slug=product.slug)


class StoryListView(ListView):
    """
    Editorial Journal catalogue of artisan stories, slow craft philosophy,
    and regional heritage spotlights.
    """
    model = Story
    template_name = "marketplace/story_list.html"
    context_object_name = "stories"
    paginate_by = 6

    def get_queryset(self):
        qs = Story.objects.filter(is_published=True).select_related("artisan")
        category = self.request.GET.get("category", "").strip()
        if category:
            qs = qs.filter(category__iexact=category)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["featured_story"] = (
            Story.objects.filter(is_published=True, is_featured=True).first()
            or Story.objects.filter(is_published=True).first()
        )
        context["categories"] = (
            Story.objects.filter(is_published=True)
            .values_list("category", flat=True)
            .distinct()
        )
        context["active_category"] = self.request.GET.get("category", "")
        return context


class StoryDetailView(DetailView):
    """
    Full editorial story reading page with rich typography,
    artisan bio, pull quotes, and related craft pieces.
    """
    model = Story
    template_name = "marketplace/story_detail.html"
    context_object_name = "story"
    slug_field = "slug"
    slug_url_kwarg = "slug"

    def get_queryset(self):
        return Story.objects.filter(is_published=True).select_related("artisan").prefetch_related("related_products")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["more_stories"] = (
            Story.objects.filter(is_published=True)
            .exclude(pk=self.object.pk)[:3]
        )
        return context


# ==============================================================================
# Syllabus Unit II: Custom Error Handlers (404 and 500)
# ==============================================================================

def custom_404_view(request, exception=None):
    """
    Custom 404 handler rendering an archival CraftConnect error page.
    """
    return render(request, "404.html", status=404)


def custom_500_view(request):
    """
    Custom 500 handler rendering an archival CraftConnect error page.
    """
    return render(request, "500.html", status=500)

