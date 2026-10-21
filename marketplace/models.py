import uuid
from decimal import Decimal
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from django.utils.text import slugify


class Category(models.Model):
    """
    Craft categories (e.g., Ceramics & Pottery, Textiles & Handloom, Woodwork, Metalcraft).
    """
    name = models.CharField(max_length=80, unique=True)
    slug = models.SlugField(max_length=100, unique=True, blank=True)
    description = models.TextField(blank=True, help_text="Short editorial description of this craft genre.")
    image = models.ImageField(upload_to="categories/", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Category"
        verbose_name_plural = "Categories"
        ordering = ["name"]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class ProductQuerySet(models.QuerySet):
    def public(self):
        """
        Returns only products that are approved by platform moderation,
        flagged as active/available, and belonging to an approved artisan.
        """
        return self.filter(
            is_approved=True,
            is_available=True,
            stock_quantity__gt=0,
            artisan__is_approved=True
        )


class Product(models.Model):
    """
    Handmade artisan products listing with craft specifications and provenance.
    """
    artisan = models.ForeignKey(
        "accounts.ArtisanProfile",
        on_delete=models.CASCADE,
        related_name="products",
        help_text="The artisan creator responsible for this piece."
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name="products",
        help_text="The craft classification."
    )
    title = models.CharField(max_length=200, help_text="Product name or piece title.")
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    description = models.TextField(help_text="Detailed story, dimensions, and craft technique description.")
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
        help_text="Price in INR / local currency (must be positive)."
    )
    material = models.CharField(
        max_length=120,
        blank=True,
        help_text="Authentic materials (e.g. 'Terracotta Clay', 'Natural Indigo Dye', 'Mulberry Silk')."
    )
    colour = models.CharField(
        max_length=80,
        blank=True,
        help_text="Primary aesthetic colour (e.g. 'Ochre Earth', 'Deep Indigo', 'Raw Linen')."
    )
    tags = models.CharField(
        max_length=255,
        blank=True,
        help_text="Comma-separated search tags (e.g. 'hand-thrown, organic, rustic, tableware')."
    )
    image = models.ImageField(
        upload_to="products/%Y/%m/",
        blank=True,
        null=True,
        help_text="Primary product photography."
    )
    stock_quantity = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(0)],
        help_text="Available inventory units."
    )
    is_available = models.BooleanField(
        default=True,
        help_text="Designates whether the artisan is currently offering this item."
    )
    is_approved = models.BooleanField(
        default=False,
        help_text="Administrative moderation approval for public catalog discovery."
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = ProductQuerySet.as_manager()

    class Meta:
        verbose_name = "Product"
        verbose_name_plural = "Products"
        ordering = ["-created_at"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(price__gt=0),
                name="check_product_price_positive"
            ),
            models.CheckConstraint(
                condition=models.Q(stock_quantity__gte=0),
                name="check_product_stock_non_negative"
            ),
        ]
        indexes = [
            models.Index(fields=["is_approved", "is_available"]),
            models.Index(fields=["category", "is_approved"]),
        ]

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title) or "craft-item"
            slug = base_slug
            counter = 1
            while Product.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.title} by {self.artisan.display_name}"


class Enquiry(models.Model):
    """
    Inquiries from buyers to artisans regarding specific products or custom commissions.
    """
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="enquiries"
    )
    buyer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="sent_enquiries"
    )
    subject = models.CharField(max_length=160)
    message = models.TextField()
    is_resolved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Enquiry"
        verbose_name_plural = "Enquiries"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Enquiry from {self.buyer.username} on '{self.product.title}'"


class SavedProduct(models.Model):
    """
    Buyer favorites / saved items for provenance tracking and later purchase.
    Enforces uniqueness to prevent duplicate records.
    """
    buyer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="saved_products"
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="saved_by_buyers"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Saved Product"
        verbose_name_plural = "Saved Products"
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["buyer", "product"],
                name="unique_buyer_saved_product"
            )
        ]

    def __str__(self):
        return f"{self.buyer.username} saved '{self.product.title}'"


class Order(models.Model):
    """
    Direct patronage purchase order connecting conscious buyers with rural artisan ateliers.
    88% of purchase price is allocated directly to the artisan.
    """
    ORDER_STATUS_CHOICES = [
        ("confirmed", "Order Confirmed & Atelier Notified"),
        ("in_crafting", "Crafting / Preparing in Studio"),
        ("dispatched", "Dispatched from Guild"),
        ("delivered", "Delivered to Patron"),
    ]

    order_number = models.CharField(max_length=32, unique=True, blank=True)
    buyer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="orders"
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="orders"
    )
    artisan = models.ForeignKey(
        "accounts.ArtisanProfile",
        on_delete=models.CASCADE,
        related_name="orders"
    )
    quantity = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    artisan_share = models.DecimalField(max_digits=10, decimal_places=2, help_text="88% direct artisan remittance")
    shipping_address = models.TextField(help_text="Patron delivery address.")
    shipping_city = models.CharField(max_length=100, default="New Delhi")
    shipping_postal_code = models.CharField(max_length=20, default="110001")
    contact_phone = models.CharField(max_length=20, default="+91 98765 43210")
    payment_method = models.CharField(max_length=60, default="UPI / Direct Bank Remittance")
    payment_status = models.CharField(max_length=20, default="Paid")
    status = models.CharField(max_length=30, choices=ORDER_STATUS_CHOICES, default="confirmed")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Order"
        verbose_name_plural = "Orders"
        ordering = ["-created_at"]

    def save(self, *args, **kwargs):
        if not self.order_number:
            self.order_number = f"CC-ORD-{uuid.uuid4().hex[:8].upper()}"
        if not self.unit_price and self.product:
            self.unit_price = self.product.price
        if not self.total_price and self.unit_price:
            self.total_price = self.unit_price * self.quantity
        if not self.artisan_share and self.total_price:
            self.artisan_share = (self.total_price * Decimal("0.88")).quantize(Decimal("0.01"))
        if not hasattr(self, "artisan") or not self.artisan:
            if self.product and self.product.artisan:
                self.artisan = self.product.artisan
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Order #{self.order_number} by {self.buyer.username} ({self.product.title})"


class Story(models.Model):
    """
    Editorial Journal stories celebrating traditional artisan guilds,
    craft heritage preservation, and mindful slow living.
    """
    title = models.CharField(max_length=240, help_text="Editorial story headline.")
    slug = models.SlugField(max_length=260, unique=True, blank=True)
    volume_tag = models.CharField(
        max_length=80,
        default="Editorial Journal • Vol. 04",
        help_text="Volume / edition badge, e.g. 'Editorial Journal • Vol. 04'."
    )
    pull_quote = models.TextField(
        help_text="Featured quote, e.g. 'In an era dominated by rapid synthetic production...'"
    )
    artisan = models.ForeignKey(
        "accounts.ArtisanProfile",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="stories",
        help_text="Associated master artisan or studio."
    )
    author_name = models.CharField(max_length=120, default="Devraj Kumhar")
    author_role = models.CharField(max_length=140, default="Master Potter, Kutch Guild")
    reading_time = models.CharField(max_length=40, default="5 min read")
    craft_region = models.CharField(max_length=140, blank=True, help_text="e.g. 'Kutch, Gujarat'")
    category = models.CharField(max_length=100, default="Heritage Preservation")
    hero_image = models.ImageField(upload_to="stories/%Y/%m/", blank=True, null=True)
    lead_paragraph = models.TextField(help_text="Opening introductory text.")
    body_content = models.TextField(help_text="Full editorial story article text.")
    related_products = models.ManyToManyField(
        Product,
        blank=True,
        related_name="featured_in_stories",
        help_text="Craft pieces made by this artisan/guild featured in this story."
    )
    is_featured = models.BooleanField(default=False, help_text="Pin as spotlight on homepage and top of journal.")
    is_published = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Editorial Story"
        verbose_name_plural = "Editorial Stories"
        ordering = ["-is_featured", "-created_at"]

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title) or "journal-story"
            slug = base_slug
            counter = 1
            while Story.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.title} ({self.volume_tag})"
