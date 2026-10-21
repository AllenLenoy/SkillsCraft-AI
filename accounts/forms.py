from django import forms
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
    """
    ROLE_CHOICES = (
        ("buyer", "Patron / Collector"),
        ("artisan", "Master Artisan"),
    )

    role = forms.ChoiceField(
        choices=ROLE_CHOICES,
        initial="buyer",
        widget=forms.HiddenInput()
    )
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            "class": "w-full px-3 py-2.5 bg-surface-bright border border-outline-variant rounded font-body-md text-body-md text-on-surface focus:outline-none focus:border-primary focus:ring-2 focus:ring-primary/20 transition-all",
            "placeholder": "Choose a username",
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
    full_name = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            "class": "w-full px-3 py-2.5 bg-surface-bright border border-outline-variant rounded font-body-md text-body-md text-on-surface focus:outline-none focus:border-primary focus:ring-2 focus:ring-primary/20 transition-all",
            "placeholder": "e.g. Priyamvada Rao or Devraj Kumhar",
            "required": "required"
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            "class": "w-full px-3 pr-10 py-2.5 bg-surface-bright border border-outline-variant rounded font-body-md text-body-md text-on-surface focus:outline-none focus:border-primary focus:ring-2 focus:ring-primary/20 transition-all",
            "placeholder": "Minimum 8 characters",
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

    def clean_username(self):
        username = self.cleaned_data.get("username", "").strip()
        if User.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError("This username is already taken. Please choose another.")
        return username

    def clean_email(self):
        email = self.cleaned_data.get("email", "").strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("An account with this email address already exists.")
        return email

    def clean(self):
        cleaned_data = super().clean()
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

