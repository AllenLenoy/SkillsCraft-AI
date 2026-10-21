from django.contrib import admin
from .models import Category, Product, Enquiry, SavedProduct, Story, Order


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "created_at")
    search_fields = ("name", "description")
    prepopulated_fields = {"slug": ("name",)}
    ordering = ("name",)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "artisan",
        "category",
        "price",
        "stock_quantity",
        "is_available",
        "is_approved",
        "created_at",
    )
    list_filter = (
        "is_approved",
        "is_available",
        "category",
        "artisan",
        "created_at",
    )
    search_fields = (
        "title",
        "description",
        "material",
        "tags",
        "artisan__display_name",
    )
    list_editable = ("price", "stock_quantity", "is_available", "is_approved")
    prepopulated_fields = {"slug": ("title",)}
    ordering = ("-created_at",)
    actions = ["approve_selected_products", "mark_out_of_stock"]

    @admin.action(description="Approve selected craft listings for public catalog")
    def approve_selected_products(self, request, queryset):
        updated_count = queryset.update(is_approved=True)
        self.message_user(request, f"{updated_count} craft listing(s) successfully approved.")

    @admin.action(description="Mark selected craft listings as out of stock")
    def mark_out_of_stock(self, request, queryset):
        updated_count = queryset.update(is_available=False, stock_quantity=0)
        self.message_user(request, f"{updated_count} craft listing(s) marked out of stock.")



@admin.register(Enquiry)
class EnquiryAdmin(admin.ModelAdmin):
    list_display = ("subject", "product", "buyer", "is_resolved", "created_at")
    list_filter = ("is_resolved", "created_at")
    search_fields = ("subject", "message", "buyer__username", "product__title")
    list_editable = ("is_resolved",)
    ordering = ("-created_at",)


@admin.register(SavedProduct)
class SavedProductAdmin(admin.ModelAdmin):
    list_display = ("buyer", "product", "created_at")
    list_filter = ("created_at",)
    search_fields = ("buyer__username", "product__title")
    ordering = ("-created_at",)


@admin.register(Story)
class StoryAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "volume_tag",
        "category",
        "author_name",
        "craft_region",
        "is_featured",
        "is_published",
        "created_at",
    )
    list_filter = ("is_featured", "is_published", "category", "created_at")
    search_fields = ("title", "pull_quote", "lead_paragraph", "body_content", "author_name", "craft_region")
    list_editable = ("is_featured", "is_published")
    prepopulated_fields = {"slug": ("title",)}
    filter_horizontal = ("related_products",)
    ordering = ("-is_featured", "-created_at")


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "order_number",
        "product",
        "buyer",
        "artisan",
        "quantity",
        "total_price",
        "artisan_share",
        "status",
        "payment_status",
        "created_at",
    )
    list_filter = ("status", "payment_status", "created_at")
    search_fields = (
        "order_number",
        "buyer__username",
        "product__title",
        "artisan__display_name",
        "shipping_city",
    )
    list_editable = ("status",)
    ordering = ("-created_at",)
