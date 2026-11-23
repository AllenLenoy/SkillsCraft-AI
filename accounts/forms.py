import re
from django import forms
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from .models import ArtisanProfile
from marketplace.models import Product, Category


class LoginForm(forms.Form):
    """
    Minimalist authentication form matching the CraftConnect Stitch auth screen.
    Supports login via username or email address.
    """
    username = forms.CharField(
        label="Username or Email",
        widget=forms.TextInput(attrs={
            "class": "w-full px-3 py-2.5 bg-surface-bright border border-outline-variant rounded font-body-md text-body-md text-on-surface focus:outline-none focus:border-primary focus:ring-2 focus:ring-primary/20 transition-all",
            "placeholder": "name@domain.com or username",
            "id": "email-input",
            "required": "required"
        })
    )
    password = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={
            "class": "w-full px-3 pr-10 py-2.5 bg-surface-bright border border-outline-variant rounded font-body-md text-body-md text-on-surface focus:outline-none focus:border-primary focus:ring-2 focus:ring-primary/20 transition-all",
            "placeholder": "••••••••••••",
            "id": "password-input",
            "required": "required"
        })
    )
    remember_me = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={
            "class": "rounded-xs border-outline-variant text-secondary focus:ring-secondary focus:ring-offset-background h-4 w-4 bg-surface"
        })
    )

    def clean(self):
        cleaned_data = super().clean()
        username_or_email = cleaned_data.get("username", "").strip()
        password = cleaned_data.get("password", "")

        # If user entered an email address, validate its format first
        if username_or_email and "@" in username_or_email:
            email_regex = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]{2,}$"
            if not re.match(email_regex, username_or_email) or ".." in username_or_email:
                raise forms.ValidationError("Please enter a valid email address.")

        if username_or_email and password:
            # Check if user passed an email instead of username
            user = authenticate(username=username_or_email, password=password)
            if user is None and "@" in username_or_email:
                try:
                    user_obj = User.objects.get(email__iexact=username_or_email)
                    user = authenticate(username=user_obj.username, password=password)
                except (User.DoesNotExist, User.MultipleObjectsReturned):
                    user = None

            if user is None:
                raise forms.ValidationError("Invalid credentials. Please verify your email/username and password.")
            self.user = user
        return cleaned_data


class RegisterForm(forms.Form):
    """
    Role-aware registration form supporting Conscious Patron and Master Artisan paths.
    Enforces strict input validation for names, emails, phone numbers, and credentials.
    """
    ROLE_CHOICES = (
        ("buyer", "Patron / Collector"),
        ("artisan", "Master Artisan"),
    )

    COUNTRY_CODE_CHOICES = (
        ("+91", "🇮🇳 +91 (India)"),
        ("+1", "🇺🇸 +1 (USA/Canada)"),
        ("+44", "🇬🇧 +44 (UK)"),
        ("+971", "🇦🇪 +971 (UAE)"),
        ("+61", "🇦🇺 +61 (Australia)"),
        ("+65", "🇸🇬 +65 (Singapore)"),
        ("+49", "🇩🇪 +49 (Germany)"),
        ("+33", "🇫🇷 +33 (France)"),
        ("+81", "🇯🇵 +81 (Japan)"),
    )

    role = forms.ChoiceField(
        choices=ROLE_CHOICES,
        initial="buyer",
        widget=forms.HiddenInput()
    )
    full_name = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            "class": "w-full px-3 py-2.5 bg-surface-bright border border-outline-variant rounded font-body-md text-body-md text-on-surface focus:outline-none focus:border-primary focus:ring-2 focus:ring-primary/20 transition-all",
            "placeholder": "e.g. Priyamvada Rao or Devraj Kumhar",
            "pattern": "[A-Za-z\\s'\\-]+",
            "title": "Full name can only contain letters, spaces, hyphens, and apostrophes.",
            "required": "required"
        })
    )
    username = forms.CharField(
        max_length=30,
        min_length=3,
        widget=forms.TextInput(attrs={
            "class": "w-full px-3 py-2.5 bg-surface-bright border border-outline-variant rounded font-body-md text-body-md text-on-surface focus:outline-none focus:border-primary focus:ring-2 focus:ring-primary/20 transition-all",
            "placeholder": "Choose a username (3-30 letters/numbers)",
            "required": "required"
        })
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            "class": "w-full px-3 py-2.5 bg-surface-bright border border-outline-variant rounded font-body-md text-body-md text-on-surface focus:outline-none focus:border-primary focus:ring-2 focus:ring-primary/20 transition-all",
            "placeholder": "name@domain.com",
            "required": "required"
        })
    )
    country_code = forms.ChoiceField(
        choices=COUNTRY_CODE_CHOICES,
        initial="+91",
        required=False,
        widget=forms.Select(attrs={
            "class": "px-3 py-2.5 bg-surface-bright border border-outline-variant rounded-l font-body-md text-body-md text-on-surface focus:outline-none focus:border-primary focus:ring-2 focus:ring-primary/20 transition-all shrink-0 cursor-pointer",
            "id": "country-code-select"
        })
    )
    phone_number = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={
            "class": "w-full px-3 py-2.5 bg-surface-bright border border-outline-variant rounded-r border-l-0 font-body-md text-body-md text-on-surface focus:outline-none focus:border-primary focus:ring-2 focus:ring-primary/20 transition-all",
            "placeholder": "9876543210 (10 digits)",
            "id": "phone-number-input",
            "type": "tel"
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            "class": "w-full px-3 pr-10 py-2.5 bg-surface-bright border border-outline-variant rounded font-body-md text-body-md text-on-surface focus:outline-none focus:border-primary focus:ring-2 focus:ring-primary/20 transition-all",
            "placeholder": "Minimum 8 characters (letters & numbers)",
            "required": "required"
        })
    )
    # Artisan-specific fields
    craft_speciality = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            "class": "w-full px-3 py-2.5 bg-surface-bright border border-outline-variant rounded font-body-md text-body-md text-on-surface focus:outline-none focus:border-primary focus:ring-2 focus:ring-primary/20 transition-all",
            "placeholder": "e.g. Terracotta Pottery, Handloom, Brass Metalcraft"
        })
    )
    location = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            "class": "w-full px-3 py-2.5 bg-surface-bright border border-outline-variant rounded font-body-md text-body-md text-on-surface focus:outline-none focus:border-primary focus:ring-2 focus:ring-primary/20 transition-all",
            "placeholder": "e.g. Bhuj, Gujarat or Varanasi, UP"
        })
    )
    bio = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            "class": "w-full px-3 py-2.5 bg-surface-bright border border-outline-variant rounded font-body-md text-body-md text-on-surface focus:outline-none focus:border-primary focus:ring-2 focus:ring-primary/20 transition-all",
            "rows": 3,
            "placeholder": "Brief story of your craft heritage, studio techniques, and materials..."
        })
    )

    def clean_full_name(self):
        full_name = self.cleaned_data.get("full_name", "").strip()
        if len(full_name) < 2:
            raise forms.ValidationError("Full name must be at least 2 characters long.")
        # Only letters, spaces, hyphens, and apostrophes allowed
        if not re.match(r"^[a-zA-Z\s'-]+$", full_name):
            raise forms.ValidationError("Full name can only contain letters, spaces, and hyphens (no numbers or special symbols).")
        return full_name

    def clean_username(self):
        username = self.cleaned_data.get("username", "").strip()
        if len(username) < 3:
            raise forms.ValidationError("Username must be at least 3 characters long.")
        if len(username) > 30:
            raise forms.ValidationError("Username cannot exceed 30 characters.")
        if not re.match(r"^[a-zA-Z][a-zA-Z0-9_-]*$", username):
            raise forms.ValidationError("Username must start with a letter and contain only letters, numbers, hyphens, or underscores.")
        if User.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError("This username is already taken. Please choose another.")
        return username

    def clean_email(self):
        email = self.cleaned_data.get("email", "").strip().lower()
        if not email:
            raise forms.ValidationError("Email address is required.")
        
        # Strict email regex: user@domain.tld with at least 2 char TLD
        email_regex = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]{2,}$"
        if not re.match(email_regex, email) or ".." in email:
            raise forms.ValidationError("Please enter a valid email address (e.g. name@domain.com).")

        try:
            validate_email(email)
        except ValidationError:
            raise forms.ValidationError("Invalid email address format.")

        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("An account with this email address already exists. Please sign in instead.")
        return email

    def clean_phone_number(self):
        phone = self.cleaned_data.get("phone_number", "").strip()
        if not phone:
            return ""
        # Strip common formatting chars (spaces, dashes, parentheses)
        digits_only = re.sub(r"[\s\-\(\)\.]", "", phone)
        if not digits_only.isdigit():
            raise forms.ValidationError("Phone number must contain only numeric digits.")
        return digits_only

    def clean(self):
        cleaned_data = super().clean()
        country_code = cleaned_data.get("country_code", "+91")
        phone = cleaned_data.get("phone_number", "")

        # Country code-aware phone validation
        if phone:
            if country_code == "+91":  # India
                if len(phone) != 10:
                    self.add_error("phone_number", "Indian mobile numbers must be exactly 10 digits.")
                elif phone[0] not in "6789":
                    self.add_error("phone_number", "Indian mobile numbers must begin with 6, 7, 8, or 9.")
            elif country_code == "+1":  # USA / Canada
                if len(phone) != 10:
                    self.add_error("phone_number", "US/Canada phone numbers must be exactly 10 digits (including area code).")
            elif country_code == "+44":  # UK
                if len(phone) not in (10, 11):
                    self.add_error("phone_number", "UK phone numbers must be 10 or 11 digits.")
            else:  # General international (E.164 standard)
                if len(phone) < 7 or len(phone) > 15:
                    self.add_error("phone_number", f"Phone numbers for {country_code} must be between 7 and 15 digits.")

        # Password complexity validation
        password = cleaned_data.get("password", "")
        if password:
            if len(password) < 8:
                self.add_error("password", "Password must be at least 8 characters long.")
            elif password.isdigit():
                self.add_error("password", "Password cannot be entirely numbers. Please include letters or symbols.")

        # Artisan requirements
        role = cleaned_data.get("role", "buyer")
        if role == "artisan":
            speciality = cleaned_data.get("craft_speciality", "").strip()
            if not speciality:
                self.add_error("craft_speciality", "Artisan registration requires a primary craft speciality.")
        return cleaned_data


class ArtisanProductForm(forms.ModelForm):
    """
    Form for artisans to create or modify craft listings in their studio dashboard.
    """
    class Meta:
        model = Product
        fields = [
            "title",
            "category",
            "description",
            "price",
            "material",
            "colour",
            "tags",
            "stock_quantity",
            "is_available",
            "image",
        ]
        widgets = {
            "title": forms.TextInput(attrs={
                "class": "w-full px-3.5 py-2.5 bg-surface-container-lowest border border-outline-variant rounded-lg font-body-md text-body-md text-on-surface focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary",
                "placeholder": "e.g. Hand-Burnished Terracotta Water Pitcher",
                "required": "required"
            }),
            "category": forms.Select(attrs={
                "class": "w-full px-3.5 py-2.5 bg-surface-container-lowest border border-outline-variant rounded-lg font-body-md text-body-md text-on-surface focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary",
                "required": "required"
            }),
            "description": forms.Textarea(attrs={
                "class": "w-full px-3.5 py-2.5 bg-surface-container-lowest border border-outline-variant rounded-lg font-body-md text-body-md text-on-surface focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary",
                "rows": 4,
                "placeholder": "Describe craft heritage, firing process, materials, care instructions...",
                "required": "required"
            }),
            "price": forms.NumberInput(attrs={
                "class": "w-full px-3.5 py-2.5 bg-surface-container-lowest border border-outline-variant rounded-lg font-body-md text-body-md text-on-surface focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary",
                "placeholder": "e.g. 1850.00",
                "step": "0.01",
                "min": "1"
            }),
            "material": forms.TextInput(attrs={
                "class": "w-full px-3.5 py-2.5 bg-surface-container-lowest border border-outline-variant rounded-lg font-body-md text-body-md text-on-surface focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary",
                "placeholder": "e.g. Kutch Terracotta Clay, River Silt Slip"
            }),
            "colour": forms.TextInput(attrs={
                "class": "w-full px-3.5 py-2.5 bg-surface-container-lowest border border-outline-variant rounded-lg font-body-md text-body-md text-on-surface focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary",
                "placeholder": "e.g. Ochre Earth, Raw Terracotta"
            }),
            "tags": forms.TextInput(attrs={
                "class": "w-full px-3.5 py-2.5 bg-surface-container-lowest border border-outline-variant rounded-lg font-body-md text-body-md text-on-surface focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary",
                "placeholder": "e.g. hand-thrown, unglazed, slow-living, tableware"
            }),
            "stock_quantity": forms.NumberInput(attrs={
                "class": "w-full px-3.5 py-2.5 bg-surface-container-lowest border border-outline-variant rounded-lg font-body-md text-body-md text-on-surface focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary",
                "min": "0"
            }),
            "is_available": forms.CheckboxInput(attrs={
                "class": "rounded-xs border-outline-variant text-secondary focus:ring-secondary h-4 w-4"
            }),
            "image": forms.FileInput(attrs={
                "class": "w-full text-xs text-on-surface-variant file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-xs file:font-semibold file:bg-surface-container file:text-primary hover:file:bg-surface-container-high cursor-pointer"
            })
        }


class BecomeArtisanForm(forms.ModelForm):
    """
    Allows an existing conscious buyer account to create an artisan profile
    and unlock the Artisan Studio Workspace without creating a separate user.
    """
    class Meta:
        model = ArtisanProfile
        fields = [
            "display_name",
            "craft_speciality",
            "location",
            "bio",
            "profile_image",
        ]
        widgets = {
            "display_name": forms.TextInput(attrs={
                "class": "w-full px-4 py-3 bg-white border border-outline-variant rounded-lg font-body text-base text-on-surface focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary shadow-xs",
                "placeholder": "e.g. Alwar Terracotta Atelier or Kutch Weavers",
                "required": "required"
            }),
            "craft_speciality": forms.TextInput(attrs={
                "class": "w-full px-4 py-3 bg-white border border-outline-variant rounded-lg font-body text-base text-on-surface focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary shadow-xs",
                "placeholder": "e.g. Terracotta Pottery, Handloom Silk, Dhokra Brass",
                "required": "required"
            }),
            "location": forms.TextInput(attrs={
                "class": "w-full px-4 py-3 bg-white border border-outline-variant rounded-lg font-body text-base text-on-surface focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary shadow-xs",
                "placeholder": "e.g. Jaipur, Rajasthan or Bhuj, Gujarat",
                "required": "required"
            }),
            "bio": forms.Textarea(attrs={
                "class": "w-full px-4 py-3 bg-white border border-outline-variant rounded-lg font-body text-base text-on-surface focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary shadow-xs",
                "rows": 4,
                "placeholder": "Share your workshop history, traditional techniques, kiln methods, and artisan philosophy...",
                "required": "required"
            }),
            "profile_image": forms.FileInput(attrs={
                "class": "w-full text-sm text-on-surface-variant file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-xs file:font-semibold file:bg-surface-container file:text-primary hover:file:bg-surface-container-high cursor-pointer"
            })
        }

