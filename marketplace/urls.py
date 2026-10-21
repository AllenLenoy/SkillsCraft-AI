from django.urls import path, re_path
from . import views

app_name = "marketplace"

urlpatterns = [
    # Standard URL mapping with parameters (Syllabus Unit II)
    path("", views.HomeView.as_view(), name="home"),
    path("catalogue/", views.ProductCatalogView.as_view(), name="product_catalog"),
    path("crafts/<slug:slug>/", views.ProductDetailView.as_view(), name="product_detail"),
    path("crafts/<slug:slug>/buy/", views.ProductBuyView.as_view(), name="product_buy"),
    path("crafts/<slug:slug>/enquire/", views.ProductEnquiryView.as_view(), name="product_enquiry"),
    path("crafts/<slug:slug>/save/", views.ToggleSaveProductView.as_view(), name="toggle_save"),
    path("genres/<slug:slug>/", views.CategoryDetailView.as_view(), name="category_detail"),

    # Editorial Journal & Stories (Syllabus Unit II)
    path("journal/", views.StoryListView.as_view(), name="story_list"),
    path("stories/", views.StoryListView.as_view(), name="story_list_alias"),
    path("journal/<slug:slug>/", views.StoryDetailView.as_view(), name="story_detail"),
    path("stories/<slug:slug>/", views.StoryDetailView.as_view(), name="story_detail_alias"),

    # Regular Expressions in URLs (Syllabus Unit II)
    re_path(r"^archive/(?P<year>[12][0-9]{3})/$", views.CraftArchiveYearView.as_view(), name="craft_archive_year"),
    re_path(r"^provenance/(?P<batch_code>[A-Za-z]{2,5}-\d{1,6})/$", views.ProvenanceLookupView.as_view(), name="provenance_lookup"),
]

