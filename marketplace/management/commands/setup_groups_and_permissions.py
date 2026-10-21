from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from marketplace.models import Product, Enquiry, SavedProduct
from accounts.models import ArtisanProfile


class Command(BaseCommand):
    help = "Sets up standard CraftConnect role groups (Artisans, Patrons, Curators) with explicit model permissions (Syllabus Unit V)."

    def handle(self, *args, **options):
        # Content types
        product_ct = ContentType.objects.get_for_model(Product)
        enquiry_ct = ContentType.objects.get_for_model(Enquiry)
        saved_ct = ContentType.objects.get_for_model(SavedProduct)
        artisan_ct = ContentType.objects.get_for_model(ArtisanProfile)

        # 1. ARTISANS GROUP
        artisan_group, created = Group.objects.get_or_create(name="Artisans")
        artisan_perms = Permission.objects.filter(
            content_type=product_ct,
            codename__in=["add_product", "change_product", "view_product"]
        ) | Permission.objects.filter(
            content_type=enquiry_ct,
            codename__in=["view_enquiry"]
        )
        artisan_group.permissions.set(artisan_perms)
        self.stdout.write(self.style.SUCCESS(f"Artisans group permissions configured ({artisan_perms.count()} perms)."))

        # 2. PATRONS / BUYERS GROUP
        patron_group, created = Group.objects.get_or_create(name="Patrons")
        patron_perms = Permission.objects.filter(
            content_type=product_ct,
            codename__in=["view_product"]
        ) | Permission.objects.filter(
            content_type=enquiry_ct,
            codename__in=["add_enquiry", "view_enquiry"]
        ) | Permission.objects.filter(
            content_type=saved_ct,
            codename__in=["add_savedproduct", "delete_savedproduct", "view_savedproduct"]
        )
        patron_group.permissions.set(patron_perms)
        self.stdout.write(self.style.SUCCESS(f"Patrons group permissions configured ({patron_perms.count()} perms)."))

        # 3. CURATORS / GUILD ADMINS GROUP
        curator_group, created = Group.objects.get_or_create(name="Guild_Curators")
        curator_perms = Permission.objects.filter(
            content_type__in=[product_ct, enquiry_ct, saved_ct, artisan_ct]
        )
        curator_group.permissions.set(curator_perms)
        self.stdout.write(self.style.SUCCESS(f"Guild_Curators group permissions configured ({curator_perms.count()} perms)."))

        self.stdout.write(self.style.SUCCESS("All role groups and permissions successfully provisioned."))
