import os
import urllib.request
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from django.conf import settings
from accounts.models import ArtisanProfile
from marketplace.models import Category, Product, Enquiry, SavedProduct, Story, Order


class Command(BaseCommand):
    help = "Seeds CraftConnect with realistic master artisans, heritage products, real slow-craft photography, and test accounts."

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING("=================================================="))
        self.stdout.write(self.style.MIGRATE_HEADING(" CraftConnect Database Seeder"))
        self.stdout.write(self.style.MIGRATE_HEADING("=================================================="))

        # ----------------------------------------------------------------------
        # 1. Ensure Media Directory Structure Exists
        # ----------------------------------------------------------------------
        media_root = settings.MEDIA_ROOT
        products_dir = os.path.join(media_root, "products")
        artisans_dir = os.path.join(media_root, "artisans", "profiles")
        categories_dir = os.path.join(media_root, "categories")
        stories_dir = os.path.join(media_root, "stories")
        for d in [products_dir, artisans_dir, categories_dir, stories_dir]:
            os.makedirs(d, exist_ok=True)

        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

        def download_image(url, target_subpath):
            """Helper to download image safely; returns relative subpath or empty."""
            try:
                full_path = os.path.join(media_root, target_subpath)
                if os.path.exists(full_path) and os.path.getsize(full_path) > 1000:
                    return target_subpath
                os.makedirs(os.path.dirname(full_path), exist_ok=True)
                req = urllib.request.Request(url, headers=headers)
                with urllib.request.urlopen(req, timeout=12) as resp:
                    data = resp.read()
                    with open(full_path, "wb") as f:
                        f.write(data)
                return target_subpath
            except Exception as e:
                self.stdout.write(self.style.WARNING(f"    ! Image download fallback for {target_subpath}: {e}"))
                return ""

        # ----------------------------------------------------------------------
        # 2. Seed Users & Profiles across 3 Roles
        # ----------------------------------------------------------------------
        self.stdout.write("\n[1/5] Provisioning Accounts & Role Profiles...")

        # Admin / Guild Curator
        admin_user, _ = User.objects.get_or_create(username="admin", defaults={"email": "admin@craftconnect.org"})
        admin_user.is_staff = True
        admin_user.is_superuser = True
        admin_user.set_password("admin123")
        admin_user.first_name = "Kavita"
        admin_user.last_name = "Verma"
        admin_user.save()
        self.stdout.write(self.style.SUCCESS("  [OK] Admin Curator: admin / admin123"))

        # Buyer / Mindful Patron
        buyer_user, _ = User.objects.get_or_create(username="priya_buyer", defaults={"email": "priya@gmail.com"})
        buyer_user.set_password("buyer123")
        buyer_user.first_name = "Priya"
        buyer_user.last_name = "Sharma"
        buyer_user.save()
        self.stdout.write(self.style.SUCCESS("  [OK] Conscious Buyer: priya_buyer / buyer123"))

        # Master Artisan 1: Gorakhpur Terracotta
        artisan1_user, _ = User.objects.get_or_create(username="ramesh_artisan", defaults={"email": "ramesh@mati-agni.in"})
        artisan1_user.set_password("artisan123")
        artisan1_user.first_name = "Ramesh"
        artisan1_user.last_name = "Prajapati"
        artisan1_user.save()

        art1_img = download_image(
            "https://images.unsplash.com/photo-1506794778202-cad84cf45f1d?auto=format&fit=crop&w=400&q=80",
            "artisans/profiles/ramesh_prajapati.jpg"
        )
        artisan1_prof, _ = ArtisanProfile.objects.update_or_create(
            user=artisan1_user,
            defaults={
                "display_name": "Mati & Agni Atelier",
                "bio": "Generational master potter practicing Gorakhpur GI-tagged terracotta art. Clay is sourced from natural riverbanks, shaped on heavy timber wheels, and fired in open wood kilns without synthetic glazes.",
                "location": "Gorakhpur, Uttar Pradesh",
                "craft_speciality": "Terracotta & Wheel-Thrown Ceramics",
                "is_approved": True,
                "is_verified": True,
                "profile_image": art1_img or None,
            }
        )
        self.stdout.write(self.style.SUCCESS("  [OK] Master Artisan 1: ramesh_artisan / artisan123 (Mati & Agni)"))

        # Master Artisan 2: Kutch Handloom & Ajrakh
        artisan2_user, _ = User.objects.get_or_create(username="fatima_handloom", defaults={"email": "fatima@kutch-weaves.in"})
        artisan2_user.set_password("artisan123")
        artisan2_user.first_name = "Fatima"
        artisan2_user.last_name = "Khatun"
        artisan2_user.save()

        art2_img = download_image(
            "https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=400&q=80",
            "artisans/profiles/fatima_khatun.jpg"
        )
        artisan2_prof, _ = ArtisanProfile.objects.update_or_create(
            user=artisan2_user,
            defaults={
                "display_name": "Kutch Heritage Handloom Guild",
                "bio": "Specializing in resist-dyed Ajrakh block prints, natural indigo extraction, and pitloom woven tussar silk. Honoring 400 years of Khatri family dyeing traditions.",
                "location": "Dhamadka, Kutch, Gujarat",
                "craft_speciality": "Ajrakh & Chanderi Silk Handloom",
                "is_approved": True,
                "is_verified": True,
                "profile_image": art2_img or None,
            }
        )
        self.stdout.write(self.style.SUCCESS("  [OK] Master Artisan 2: fatima_handloom / artisan123 (Kutch Guild)"))

        # Master Artisan 3: Bastar Lost-Wax Bronze
        artisan3_user, _ = User.objects.get_or_create(username="somnath_dhokra", defaults={"email": "somnath@bastar-bronze.in"})
        artisan3_user.set_password("artisan123")
        artisan3_user.first_name = "Somnath"
        artisan3_user.last_name = "Baghel"
        artisan3_user.save()

        art3_img = download_image(
            "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?auto=format&fit=crop&w=400&q=80",
            "artisans/profiles/somnath_baghel.jpg"
        )
        artisan3_prof, _ = ArtisanProfile.objects.update_or_create(
            user=artisan3_user,
            defaults={
                "display_name": "Bastar Lost-Wax Bronze Guild",
                "bio": "Practicing ancient non-ferrous metal casting known as Dhokra. Every single wax model is destroyed during casting, making every creation completely unique in the world.",
                "location": "Kondagaon, Bastar, Chhattisgarh",
                "craft_speciality": "Tribal Dhokra & Bell Metalcraft",
                "is_approved": True,
                "is_verified": True,
                "profile_image": art3_img or None,
            }
        )
        self.stdout.write(self.style.SUCCESS("  [OK] Master Artisan 3: somnath_dhokra / artisan123 (Bastar Guild)"))

        # ----------------------------------------------------------------------
        # 3. Seed Craft Categories
        # ----------------------------------------------------------------------
        self.stdout.write("\n[2/5] Seeding Curated Craft Categories...")
        categories_data = [
            {
                "name": "Ceramics & Terracotta",
                "slug": "ceramics-terracotta",
                "description": "Wheel-thrown earthenware, Khurja studio pottery, and smoke-fired Gorakhpur terracotta tableware and planters.",
                "image_url": "https://images.unsplash.com/photo-1578749556568-bc2c40e68b61?auto=format&fit=crop&w=600&q=80",
            },
            {
                "name": "Textiles & Handloom",
                "slug": "textiles-handloom",
                "description": "Pitloom woven tussar silks, organic hand-spun khadi, and generational resist-dyed Ajrakh block prints.",
                "image_url": "https://images.unsplash.com/photo-1610030469983-98e550d6193c?auto=format&fit=crop&w=600&q=80",
            },
            {
                "name": "Metalcraft & Dhokra",
                "slug": "metalcraft-dhokra",
                "description": "Ancient lost-wax bell metal casting, hand-beaten kansa bronze tableware, and temple brass diya lamps.",
                "image_url": "https://images.unsplash.com/photo-1569683795645-b62e50fbf103?auto=format&fit=crop&w=600&q=80",
            },
            {
                "name": "Woodwork & Carving",
                "slug": "woodwork-carving",
                "description": "Hand-chiseled Saharanpur sheesham wood chests, Kashmir walnut lattice jali screens, and reclaimed teak keepsakes.",
                "image_url": "https://images.unsplash.com/photo-1533227268428-f9ed0900fb3b?auto=format&fit=crop&w=600&q=80",
            },
            {
                "name": "Heritage Keepsakes & Jewelry",
                "slug": "heritage-keepsakes",
                "description": "Cuttack Tarakasi silver filigree, Jaipur Blue Pottery curios, and GI-certified artisanal collector artifacts.",
                "image_url": "https://images.unsplash.com/photo-1535632066927-ab7c9ab60908?auto=format&fit=crop&w=600&q=80",
            },
        ]

        categories_map = {}
        for cat_data in categories_data:
            cat_img = download_image(cat_data["image_url"], f"categories/{cat_data['slug']}.jpg")
            cat, _ = Category.objects.update_or_create(
                slug=cat_data["slug"],
                defaults={
                    "name": cat_data["name"],
                    "description": cat_data["description"],
                    "image": cat_img or None,
                }
            )
            categories_map[cat.slug] = cat
            self.stdout.write(self.style.SUCCESS(f"  [OK] Category: {cat.name}"))

        # ----------------------------------------------------------------------
        # 4. Seed 12 Masterpiece Products with Exact Real Craft Imagery
        # ----------------------------------------------------------------------
        self.stdout.write("\n[3/5] Seeding 12 Masterpiece Artisan Creations...")

        products_data = [
            # 1. Gorakhpur Terracotta Chai Kulhad Set
            {
                "artisan": artisan1_prof,
                "category": categories_map["ceramics-terracotta"],
                "title": "Wheel-Thrown Gorakhpur Terracotta Chai Kulhad (Set of 6)",
                "slug": "wheel-thrown-gorakhpur-terracotta-kulhads",
                "description": (
                    "Meticulously shaped on wooden kick-wheels using alluvial clay deposited by the Rapti River in Gorakhpur. "
                    "These kulhads are left completely unglazed and wood-fired with organic husk fuel, imparting a subtle, grounding "
                    "earthiness to morning and evening chai rituals. Completely biodegradable, lead-free, and cooling to touch."
                ),
                "price": Decimal("650.00"),
                "material": "Natural Alluvial Red Clay",
                "colour": "Raw Ochre Earth",
                "tags": "wheel-thrown, terracotta, kulhad, chai, lead-free, slow-living",
                "stock_quantity": 18,
                "image_url": "https://images.unsplash.com/photo-1578749556568-bc2c40e68b61?auto=format&fit=crop&w=900&q=80",
            },
            # 2. Terracotta Water Carafe
            {
                "artisan": artisan1_prof,
                "category": categories_map["ceramics-terracotta"],
                "title": "Unglazed Earthen Terracotta Water Carafe with Diya Finial",
                "slug": "unglazed-terracotta-water-carafe",
                "description": (
                    "Designed for gentle evaporative natural cooling, this hand-burnished clay carafe keeps drinking water naturally "
                    "refreshing without electricity. The matching earthen lid features a hand-sculpted temple flame motif. "
                    "Cured with raw wood smoke for water purity and gentle mineral balance."
                ),
                "price": Decimal("1250.00"),
                "material": "Riverbed Terracotta Clay",
                "colour": "Burnt Terracotta",
                "tags": "carafe, terracotta, water-cooler, natural-cooling, zero-plastic",
                "stock_quantity": 8,
                "image_url": "https://images.unsplash.com/photo-1610701596007-11502861dcfa?auto=format&fit=crop&w=900&q=80",
            },
            # 3. Jaipur Blue Pottery Serving Bowl
            {
                "artisan": artisan1_prof,
                "category": categories_map["ceramics-terracotta"],
                "title": "Jaipur Hand-Painted Blue Pottery Floral Serving Bowl",
                "slug": "jaipur-blue-pottery-floral-serving-bowl",
                "description": (
                    "Crafted using Jaipur's signature clay-free dough made from quartz stone powder, Fuller's earth, and natural gum. "
                    "Hand-painted with cobalt oxide and Persian-influenced floral arabesques before firing in traditional low-temperature kilns. "
                    "A vibrant centerpiece bowl celebrating Rajasthan's royal craft legacy."
                ),
                "price": Decimal("1850.00"),
                "material": "Quartz Powder, Fuller Earth & Glass Frit",
                "colour": "Cobalt Blue & Turquoise",
                "tags": "blue-pottery, jaipur, hand-painted, serving-bowl, royal-heritage",
                "stock_quantity": 6,
                "image_url": "https://images.unsplash.com/photo-1565193566173-7a0ee3dbe261?auto=format&fit=crop&w=900&q=80",
            },
            # 4. Ajrakh Silk Dupatta
            {
                "artisan": artisan2_prof,
                "category": categories_map["textiles-handloom"],
                "title": "Natural Indigo Hand-Block Ajrakh Modal Silk Dupatta",
                "slug": "natural-indigo-ajrakh-modal-silk-dupatta",
                "description": (
                    "A masterpiece of 16 sequential wash and resist-dye stages using hard-carved teak woodblocks. "
                    "Dyed with true indigofera tinctoria and wild madder root for deep, rich jewel tones. "
                    "Draped over lightweight mulberry modal silk that glides with fluid elegance."
                ),
                "price": Decimal("3200.00"),
                "material": "Modal Silk & Natural Organic Indigo",
                "colour": "Midnight Indigo & Crimson",
                "tags": "ajrakh, block-print, indigo, modal-silk, dupatta, slow-fashion",
                "stock_quantity": 10,
                "image_url": "https://images.unsplash.com/photo-1606760227091-3dd870d97f1d?auto=format&fit=crop&w=900&q=80",
            },
            # 5. Chanderi Handloom Saree
            {
                "artisan": artisan2_prof,
                "category": categories_map["textiles-handloom"],
                "title": "Pure Chanderi Zari Handloom Saree in Forest Emerald",
                "slug": "pure-chanderi-zari-handloom-saree-forest-emerald",
                "description": (
                    "Woven by master weavers on generational pitlooms in Madhya Pradesh. Blends gossamer fine cotton weft "
                    "with pure silk warp, finished with delicate gold zari booti motifs across the border and pallu. "
                    "Featherlight, breathable, and luminous under festive candlelight."
                ),
                "price": Decimal("6800.00"),
                "material": "Silk-Cotton Blend with Fine Zari",
                "colour": "Forest Emerald & Gold",
                "tags": "chanderi, handloom, silk-saree, zari-border, wedding-craft",
                "stock_quantity": 4,
                "image_url": "https://images.unsplash.com/photo-1610030469983-98e550d6193c?auto=format&fit=crop&w=900&q=80",
            },
            # 6. Pochampally Ikat Throw
            {
                "artisan": artisan2_prof,
                "category": categories_map["textiles-handloom"],
                "title": "Pochampally Ikat Handwoven Geometric Cotton Throw",
                "slug": "pochampally-ikat-handwoven-cotton-throw",
                "description": (
                    "Featuring complex double-ikat resist dying where both warp and weft threads are precision-dyed prior to loom setup. "
                    "100% combed rain-fed organic cotton, offering plush tactile comfort as an accent bed runner or living room couch drape. "
                    "Pre-washed with soapnuts for natural softness."
                ),
                "price": Decimal("2450.00"),
                "material": "100% Organic Handspun Cotton",
                "colour": "Saffron & Charcoal",
                "tags": "ikat, pochampally, handwoven, throw-blanket, home-decor",
                "stock_quantity": 7,
                "image_url": "https://images.unsplash.com/photo-1584917865442-de89df76afd3?auto=format&fit=crop&w=900&q=80",
            },
            # 7. Bastar Lost-Wax Brass Sculpture
            {
                "artisan": artisan3_prof,
                "category": categories_map["metalcraft-dhokra"],
                "title": "Lost-Wax Bastar Dhokra Tribal Musician Brass Sculpture",
                "slug": "lost-wax-bastar-dhokra-tribal-musician-sculpture",
                "description": (
                    "Crafted using the primordial 4,000-year-old lost-wax metal casting method by Gond artisans of Bastar. "
                    "Beeswax threads are hand-coiled over a river clay core, enveloped in termite mud, and molten recycled brass is poured in. "
                    "Depicts a traditional dholak drummer celebrating tribal harvest melodies."
                ),
                "price": Decimal("3800.00"),
                "material": "Recycled Brass & Bronze Alloy",
                "colour": "Antique Patinated Brass",
                "tags": "dhokra, lost-wax, tribal-art, brass-sculpture, bastar, antique-finish",
                "stock_quantity": 5,
                "image_url": "https://images.unsplash.com/photo-1569683795645-b62e50fbf103?auto=format&fit=crop&w=900&q=80",
            },
            # 8. Bell Metal Diya Lamp
            {
                "artisan": artisan3_prof,
                "category": categories_map["metalcraft-dhokra"],
                "title": "Hand-Etched Bell Metal Diya with Temple Peacock Finial",
                "slug": "hand-etched-bell-metal-temple-peacock-diya",
                "description": (
                    "Cast from heavy resonant bell metal alloy with a hand-chiseled peacock finial. The deep oil reservoir accommodates "
                    "cotton wicks for extended devotional illumination during festivals or evening contemplation. "
                    "Polished with tamarind paste to a warm, antique golden sheen."
                ),
                "price": Decimal("2150.00"),
                "material": "Bell Metal (78% Copper, 22% Tin)",
                "colour": "Golden Lustre",
                "tags": "diya, bell-metal, temple-lamp, peacock, brassware, ritual",
                "stock_quantity": 12,
                "image_url": "https://images.unsplash.com/photo-1605371924599-2d0365da1ae0?auto=format&fit=crop&w=900&q=80",
            },
            # 9. Kansa Bronze Dinner Thali
            {
                "artisan": artisan3_prof,
                "category": categories_map["metalcraft-dhokra"],
                "title": "Hand-Burnished Kansa Pure Bronze Dinner Thali Set",
                "slug": "hand-burnished-kansa-bronze-dinner-thali-set",
                "description": (
                    "Hand-hammered from certified Ayurvedic Kansa (bell metal alloy). According to ancient Charaka Samhita, dining from "
                    "pure bronze balances Pitta dosha and promotes digestive wellness. Includes a wide dinner plate and two hand-beaten katori bowls. "
                    "Finished with distinctive artisan hammer marks."
                ),
                "price": Decimal("4600.00"),
                "material": "Ayurvedic Kansa Bronze (Bronze Alloy)",
                "colour": "Warm Muted Bronze",
                "tags": "kansa, bronze-thali, ayurveda, tableware, hand-hammered, health",
                "stock_quantity": 6,
                "image_url": "https://images.unsplash.com/photo-1589301760014-d929f3979dbc?auto=format&fit=crop&w=900&q=80",
            },
            # 10. Saharanpur Carved Keepsake Box
            {
                "artisan": artisan1_prof,
                "category": categories_map["woodwork-carving"],
                "title": "Saharanpur Hand-Chiseled Sheesham Carved Keepsake Box",
                "slug": "saharanpur-sheesham-carved-keepsake-box",
                "description": (
                    "Carved from legally harvested seasoned Indian Rosewood (Sheesham) by master joiners of Saharanpur. "
                    "Features deep floral relief chiseling across the lid and brass corner brackets. "
                    "Lined with soft maroon velvet to safeguard family heirlooms, letters, or sacred jewelry."
                ),
                "price": Decimal("1650.00"),
                "material": "Seasoned Solid Sheesham Wood & Brass Inlay",
                "colour": "Warm Walnut Stain",
                "tags": "wood-carving, sheesham, keepsake-box, saharanpur, brass-inlay",
                "stock_quantity": 11,
                "image_url": "https://images.unsplash.com/photo-1533227268428-f9ed0900fb3b?auto=format&fit=crop&w=900&q=80",
            },
            # 11. Kashmir Walnut Wood Book Stand
            {
                "artisan": artisan1_prof,
                "category": categories_map["woodwork-carving"],
                "title": "Kashmir Walnut Wood Lattice Carved Book Stand (Rehal)",
                "slug": "kashmir-walnut-wood-carved-rehal-bookstand",
                "description": (
                    "Single-block folding scripture stand hand-carved from seasoned Kashmir walnut root timber. "
                    "Features delicate Chinar leaf motifs and geometric lattice jali work that unfolds seamlessly without metal hinges. "
                    "Wax-buffed to highlight the natural dark grain of high-altitude walnut trees."
                ),
                "price": Decimal("2850.00"),
                "material": "Kashmir Mountain Walnut Timber",
                "colour": "Rich Dark Walnut",
                "tags": "walnut-wood, rehal, book-stand, kashmir-craft, lattice-carving",
                "stock_quantity": 5,
                "image_url": "https://images.unsplash.com/photo-1544716278-ca5e3f4abd8c?auto=format&fit=crop&w=900&q=80",
            },
            # 12. Cuttack Silver Filigree Pendant
            {
                "artisan": artisan2_prof,
                "category": categories_map["heritage-keepsakes"],
                "title": "Cuttack Tarakasi Silver Filigree Floral Pendant with Pearl",
                "slug": "cuttack-tarakasi-silver-filigree-floral-pendant",
                "description": (
                    "Delicate as a spider's web, this pendant is hand-drawn from pure 92.5 sterling silver wires hammered hair-thin. "
                    "Master silversmiths of Cuttack bend and fuse each scroll by hand with a micro blowtorch. "
                    "Anchored by a natural freshwater pearl teardrop. Certified hallmark 925 sterling silver."
                ),
                "price": Decimal("3400.00"),
                "material": "92.5 Sterling Silver & Freshwater Pearl",
                "colour": "Bright Sterling Silver",
                "tags": "silver-filigree, tarakasi, cuttack, handmade-jewelry, 925-sterling",
                "stock_quantity": 9,
                "image_url": "https://images.unsplash.com/photo-1535632066927-ab7c9ab60908?auto=format&fit=crop&w=900&q=80",
            },
        ]

        created_products = []
        for pdata in products_data:
            img_rel = download_image(pdata["image_url"], f"products/{pdata['slug']}.jpg")
            prod, _ = Product.objects.update_or_create(
                slug=pdata["slug"],
                defaults={
                    "artisan": pdata["artisan"],
                    "category": pdata["category"],
                    "title": pdata["title"],
                    "description": pdata["description"],
                    "price": pdata["price"],
                    "material": pdata["material"],
                    "colour": pdata["colour"],
                    "tags": pdata["tags"],
                    "stock_quantity": pdata["stock_quantity"],
                    "is_available": True,
                    "is_approved": True,
                    "image": img_rel or None,
                }
            )
            created_products.append(prod)
            self.stdout.write(self.style.SUCCESS(f"  [OK] Product: {prod.title[:45]}... (Rs. {prod.price})"))

        # ----------------------------------------------------------------------
        # 5. Seed Interactions (Bookmarks & Inquiries)
        # ----------------------------------------------------------------------
        self.stdout.write("\n[4/5] Seeding Patron Interactions & Studio Inquiries...")

        # Save products for priya_buyer
        if len(created_products) >= 3:
            SavedProduct.objects.get_or_create(buyer=buyer_user, product=created_products[0])
            SavedProduct.objects.get_or_create(buyer=buyer_user, product=created_products[3])
            self.stdout.write(self.style.SUCCESS("  [OK] Saved 2 bookmarked pieces for priya_buyer"))

        # Seed realistic inquiries
        if len(created_products) >= 2:
            Enquiry.objects.get_or_create(
                buyer=buyer_user,
                product=created_products[0],
                defaults={
                    "subject": "Custom order for 24 kulhads for Diwali family gathering",
                    "message": "Namaste Ramesh ji. We adore the unglazed Gorakhpur terracotta texture. Can you prepare a batch of 24 pieces by next month? Looking forward to supporting your atelier.",
                    "is_resolved": False,
                }
            )
            Enquiry.objects.get_or_create(
                buyer=buyer_user,
                product=created_products[3],
                defaults={
                    "subject": "Washing and care instructions for natural indigo silk",
                    "message": "Hello Fatima ji. For the Ajrakh modal silk dupatta, should it be dry cleaned exclusively or is handwashing with cold water and soapnuts safe? Warm regards.",
                    "is_resolved": True,
                }
            )
            self.stdout.write(self.style.SUCCESS("  [OK] Dispatched 2 authentic artisan inquiries"))

        # ----------------------------------------------------------------------
        # 6. Seed Editorial Stories & Journal Chronicles
        # ----------------------------------------------------------------------
        self.stdout.write("\n[5/5] Seeding Editorial Journal & Craft Chronicles...")

        stories_data = [
            {
                "title": "The Earth remembers the hand that turns it.",
                "slug": "the-earth-remembers-the-hand-that-turns-it",
                "volume_tag": "Editorial Journal • Vol. 04",
                "pull_quote": "In an era dominated by rapid synthetic production, slow craft is an act of cultural preservation. Our marketplace guarantees that 88% of every purchase flows directly into village artisan accounts.",
                "author_name": "Devraj Kumhar & Ramesh Prajapati",
                "author_role": "Master Potter, Kutch Guild",
                "reading_time": "5 min read",
                "craft_region": "Kutch & Gorakhpur Guilds",
                "category": "Ceramics & Terracotta",
                "image_url": "https://images.unsplash.com/photo-1565193566173-7a0ee3dbe261?auto=format&fit=crop&w=1200&q=80",
                "subpath": "stories/earth_remembers_hand.jpg",
                "lead_paragraph": "Devraj Kumhar's family has worked the Kutch salt-clay for two hundred years. With CraftConnect's intelligent discovery, his functional terracotta is now discovered by architects, chefs, and tea connoisseurs worldwide.",
                "body_content": (
                    "At 4:30 AM before the desert heat awakens, the artisan prepares the wheel. The clay he uses is not industrial slurry purchased in bags; it is alluvial silt hauled from dry riverbeds after the brief monsoon, beaten with wooden paddles, and mixed with fine sand and organic husks to breathe when fired.\n\n"
                    "\"When clay touches water, it sings,\" Devraj explains with quiet reverence. \"If your mind is hurried, the vessel will wobble and collapse. You cannot deceive terracotta. It records every hesitation, every ounce of patience, and every gentle touch of the palm.\"\n\n"
                    "In rural India, community potteries were historically the heartbeat of the village. The earthen matka kept water naturally crisp through evaporative cooling long before refrigeration. Today, through CraftConnect's decentralized direct-trade network, Devraj's handcrafted tea kulhads, terracotta carafes, and fluted bowls travel to metropolitan tea rooms and sustainable homes across the globe without passing through predatory middlemen.\n\n"
                    "Each fired pot carries the smoky hallmark of cow dung and husk firings—no two pieces are identical, each holding the warm earth tones of western India's soil."
                ),
                "is_featured": True,
                "artisan": artisan1_prof,
                "related_indices": [0, 1],
            },
            {
                "title": "Indigo in the Veins: 16 Steps of Living Desert Alchemy",
                "slug": "indigo-in-the-veins-16-steps-of-living-desert-alchemy",
                "volume_tag": "Editorial Journal • Vol. 03",
                "pull_quote": "Natural indigo is not a dye; it is a living organism. When it sleeps, you must whisper to it with jaggery and lime water.",
                "author_name": "Fatima Khatun",
                "author_role": "Master Weaver & Dyer, Kutch Handloom Collective",
                "reading_time": "6 min read",
                "craft_region": "Bhuj, Kutch, Gujarat",
                "category": "Textiles & Handloom",
                "image_url": "https://images.unsplash.com/photo-1607344645866-009c320c5ab8?auto=format&fit=crop&w=1200&q=80",
                "subpath": "stories/indigo_desert_alchemy.jpg",
                "lead_paragraph": "In the arid expanse of Dhamadka, master artisan Fatima Khatun commands clay pits that ferment Indigofera tinctoria using age-old formulas unchanged since the Indus Valley civilization.",
                "body_content": (
                    "Ajrakh block printing is mathematics, chemistry, and poetry synchronized to the rhythm of wooden mallets. A single saree undergoes sixteen separate washing, mordanting, printing, and sun-curing stages over the course of three weeks.\n\n"
                    "\"Modern fast fashion treats cloth as disposable plastic,\" Fatima says, smoothing the folds of an indigo stole. \"We treat each thread as an heirloom. We use hard river water for mineral binding, crushed pomegranate rinds for ochre yellow, and fermented scrap iron and jaggery for our indelible blacks.\"\n\n"
                    "On the rhythmic printing tables, teakwood blocks carved with geometric star-patterns land with a resolute thud. The registration of motifs relies entirely on the artisan's muscle memory and eyesight—an intuitive mastery that no automated digital print can replicate.\n\n"
                    "When patrons purchase handloom Ajrakh directly through CraftConnect, they ensure that the water tables, non-toxic dye traditions, and women-led printing cooperatives of Kutch thrive with dignity and financial autonomy."
                ),
                "is_featured": False,
                "artisan": artisan2_prof,
                "related_indices": [3, 4],
            },
            {
                "title": "Whispers of Molten Wax: Inside the 4,000-Year Foundries of Bastar",
                "slug": "whispers-of-molten-wax-inside-bastar-foundries",
                "volume_tag": "Editorial Journal • Vol. 02",
                "pull_quote": "Every single Dhokra piece consumes its own mold in fire. It is born once, and can never be duplicated.",
                "author_name": "Somnath Baghel",
                "author_role": "Master Metalcraftsman, Bastar Artisan Guild",
                "reading_time": "7 min read",
                "craft_region": "Bastar, Chhattisgarh",
                "category": "Metalcraft & Dhokra",
                "image_url": "https://images.unsplash.com/photo-1579783900882-c0d3dad7b119?auto=format&fit=crop&w=1200&q=80",
                "subpath": "stories/bastar_molten_wax.jpg",
                "lead_paragraph": "Hidden deep within the sal forests of Bastar, the Ghadwa tribal community practices cire-perdue—the ancient lost-wax bronze casting technique that created the iconic Dancing Girl of Mohenjo-daro.",
                "body_content": (
                    "Somnath Baghel works before a pit kiln sunk into red earth. With fingers calloused from decades of shaping softened beeswax into delicate noodle-thin strands, he coils the wax thread-by-thread over a sculpted clay core.\n\n"
                    "\"Industrial metal casting pours liquid alloy into reusable silicon molds,\" Somnath explains. \"In Bastar Dhokra, every casting destroys its shell. The beeswax melts away, leaving a hollow channel where molten recycled bell-metal rushes in. Once the mold cools and is cracked open with a mallet, the mold is gone forever. Your sculpture is the only one in human existence.\"\n\n"
                    "The motifs of Dhokra are celebrations of jungle symbiosis: sacred elephants carrying ceremonial umbrellas, tree spirits holding lanterns, and tribal drummers mid-festival. The brass radiates a primitive, tactile warmth unlike polished machine hardware.\n\n"
                    "Through CraftConnect's digital provenance ledger, patrons trace the exact foundry batch, artisan signature, and sustainable scrap metal origins of their Bastar sculpture."
                ),
                "is_featured": False,
                "artisan": artisan3_prof,
                "related_indices": [5, 6],
            },
            {
                "title": "The Living Grain: Monsoon Seasoning of Saharanpur Sheesham",
                "slug": "the-living-grain-seasoning-saharanpur-sheesham",
                "volume_tag": "Editorial Journal • Vol. 01",
                "pull_quote": "A machine cuts wood against its will. A craftsman listens to the grain and frees the form hiding inside.",
                "author_name": "Mohammad Iqbal",
                "author_role": "Senior Woodwright, Saharanpur Guild",
                "reading_time": "5 min read",
                "craft_region": "Saharanpur, Uttar Pradesh",
                "category": "Woodwork & Carving",
                "image_url": "https://images.unsplash.com/photo-1544816155-12df9643f363?auto=format&fit=crop&w=1200&q=80",
                "subpath": "stories/saharanpur_woodgrain.jpg",
                "lead_paragraph": "For over four centuries, Saharanpur has been India's sanctum for intricate Jali lattice woodwork, where rosewood and sheesham are shaped with hand chisels into architectural heirlooms.",
                "body_content": (
                    "Before a chisel touches a timber block, the wood must undergo patient natural air-drying. Mohammad Iqbal seasons sheesham logs under shaded courtyards through two full monsoons and dry summers, allowing the wood to naturally stabilize against seasonal warping.\n\n"
                    "\"When you rush the wood with chemical kiln dryers, the sap cracks the fibers,\" Iqbal notes. \"Slow craft honors the tree's lifespan. If a tree took forty years to mature, how can you expect to rush its carving in forty minutes?\"\n\n"
                    "Using handmade carbon-steel chisels and wooden mallets, Iqbal's guild cuts floral jali patterns with micro-millimeter precision. The fragrant aroma of natural beeswax polish seals the wood, highlighting deep auburn grain lines without plastic synthetic varnishes.\n\n"
                    "Through direct artisan commerce on CraftConnect, Saharanpur's generational carvers are revitalizing their ateliers and mentoring young apprentices in master woodwright joinery."
                ),
                "is_featured": False,
                "artisan": artisan1_prof,
                "related_indices": [7, 8],
            },
            {
                "title": "Sun, Salt, and Silk: Reviving the Vanishing Ashavali Brocade",
                "slug": "sun-salt-and-silk-reviving-ashavali-brocade",
                "volume_tag": "Special Heritage Edition • Autumn 2026",
                "pull_quote": "When the pit loom dances, centuries of forgotten lullabies awaken in the golden zari border.",
                "author_name": "Kavita Verma & Ananya Sen",
                "author_role": "Guild Curators & Textile Archivists",
                "reading_time": "8 min read",
                "craft_region": "Ahmedabad & Patan, Gujarat",
                "category": "Heritage Keepsakes & Jewelry",
                "image_url": "https://images.unsplash.com/photo-1513519245088-0e12902e5a38?auto=format&fit=crop&w=1200&q=80",
                "subpath": "stories/ashavali_silk_brocade.jpg",
                "lead_paragraph": "Pre-dating the famed Banarasi brocades by two centuries, Gujarat's ancient Ashavali weave used real metallic zari threads wrapped around fine silk to depict parrots, lions, and flowering vines.",
                "body_content": (
                    "In the narrow pols (historical gated quarters) of old Ahmedabad, the rhythmic click-clack of wooden shuttles was once a daily symphony. The Ashavali brocade—treasured in royal courts of the Mughal and Maratha empires—faced near extinction as power looms flooded the market with polyester imitations.\n\n"
                    "Today, a passionate revival collective of master weavers is recovering archival punch cards and natural mulberry silk to weave limited-edition runs of this sovereign textile.\n\n"
                    "\"On an authentic pit loom, a master weaver weaves at most four to six inches per day,\" explains archival curator Kavita Verma. \"The metallic gold threads must be interlaced by hand without breaking the tension of the fine silk warp. It is living meditation.\"\n\n"
                    "CraftConnect provides conscious patrons with transparent provenance documentation, certifying the authenticity of real silk filaments and fair-wage artisan compensation for every metre woven."
                ),
                "is_featured": False,
                "artisan": artisan2_prof,
                "related_indices": [9, 10],
            },
        ]

        for s_data in stories_data:
            img_path = download_image(s_data["image_url"], s_data["subpath"])
            story, created = Story.objects.update_or_create(
                slug=s_data["slug"],
                defaults={
                    "title": s_data["title"],
                    "volume_tag": s_data["volume_tag"],
                    "pull_quote": s_data["pull_quote"],
                    "author_name": s_data["author_name"],
                    "author_role": s_data["author_role"],
                    "reading_time": s_data["reading_time"],
                    "craft_region": s_data["craft_region"],
                    "category": s_data["category"],
                    "hero_image": img_path or None,
                    "lead_paragraph": s_data["lead_paragraph"],
                    "body_content": s_data["body_content"],
                    "is_featured": s_data["is_featured"],
                    "is_published": True,
                    "artisan": s_data["artisan"],
                }
            )
            # Attach related products
            rel_prods = []
            for idx in s_data["related_indices"]:
                if idx < len(created_products):
                    rel_prods.append(created_products[idx])
            if rel_prods:
                story.related_products.set(rel_prods)

            status_str = "Created" if created else "Updated"
            self.stdout.write(self.style.SUCCESS(f"  [OK] Story: {story.title[:45]}... ({status_str})"))

        # ----------------------------------------------------------------------
        # 7. Seed Sample Orders (Direct Acquisitions)
        # ----------------------------------------------------------------------
        self.stdout.write(self.style.HTTP_INFO("\n[7/7] Seeding Authentic Craft Orders (Acquisitions)..."))
        if created_products:
            p1 = created_products[0]  # Terracotta Elephant
            p2 = created_products[3] if len(created_products) > 3 else created_products[1]

            orders_to_seed = [
                {
                    "order_number": "ORD-2026-CC101",
                    "buyer": buyer_user,
                    "product": p1,
                    "artisan": p1.artisan,
                    "quantity": 1,
                    "unit_price": p1.price,
                    "shipping_address": "Flat 4B, Gulmohar Enclave, 12th Main Indiranagar",
                    "shipping_city": "Bengaluru",
                    "shipping_postal_code": "560038",
                    "contact_phone": "+91 98450 12345",
                    "payment_method": "upi",
                    "payment_status": "paid",
                    "status": "in_crafting",
                },
                {
                    "order_number": "ORD-2026-CC102",
                    "buyer": buyer_user,
                    "product": p2,
                    "artisan": p2.artisan,
                    "quantity": 1,
                    "unit_price": p2.price,
                    "shipping_address": "B-12, Alaknanda Heritage Apartments",
                    "shipping_city": "New Delhi",
                    "shipping_postal_code": "110019",
                    "contact_phone": "+91 98110 56789",
                    "payment_method": "cod",
                    "payment_status": "pending",
                    "status": "confirmed",
                },
            ]

            for o_data in orders_to_seed:
                total_price = o_data["unit_price"] * o_data["quantity"]
                artisan_share = (total_price * Decimal("0.88")).quantize(Decimal("0.01"))
                order, ord_created = Order.objects.update_or_create(
                    order_number=o_data["order_number"],
                    defaults={
                        **o_data,
                        "total_price": total_price,
                        "artisan_share": artisan_share,
                    }
                )
                status_str = "Created" if ord_created else "Updated"
                self.stdout.write(self.style.SUCCESS(f"  [OK] Order #{order.order_number} for {order.product.title[:35]} ({status_str})"))

        self.stdout.write(self.style.MIGRATE_HEADING("\n=================================================="))
        self.stdout.write(self.style.SUCCESS(" CRAFTCONNECT SEED COMPLETE — ALL SYSTEMS READY"))
        self.stdout.write(self.style.MIGRATE_HEADING("=================================================="))
        self.stdout.write("Credentials Overview:")
        self.stdout.write("  Admin Curator:     admin / admin123")
        self.stdout.write("  Master Artisan 1:  ramesh_artisan / artisan123 (Gorakhpur Terracotta)")
        self.stdout.write("  Master Artisan 2:  fatima_handloom / artisan123 (Kutch Handloom)")
        self.stdout.write("  Master Artisan 3:  somnath_dhokra / artisan123 (Bastar Bronze)")
        self.stdout.write("  Conscious Buyer:   priya_buyer / buyer123")
