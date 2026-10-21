from django import forms
from .models import Enquiry, Order


class ProductSearchForm(forms.Form):
    """
    Search and filter form for the public craft catalog.
    """
    ORDERING_CHOICES = (
        ("-created_at", "Newest Arrivals"),
        ("price_asc", "Price: Low to High"),
        ("price_desc", "Price: High to Low"),
        ("title_asc", "Name: A to Z"),
    )

    q = forms.CharField(
        required=False,
        label="Search Crafts",
        widget=forms.TextInput(attrs={
            "placeholder": "Search by craft technique, material, keyword (e.g. 'wheel-thrown', 'terracotta')...",
            "class": "w-full pl-10 pr-4 py-2.5 bg-surface rounded-md border border-outline-variant text-sm focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary"
        })
    )
    category = forms.CharField(
        required=False,
        widget=forms.HiddenInput()
    )
    material = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            "placeholder": "Filter material (e.g. Silk, Clay, Teak)...",
            "class": "w-full px-3 py-2 bg-surface rounded-md border border-outline-variant text-xs focus:outline-none focus:border-primary"
        })
    )
    ordering = forms.ChoiceField(
        choices=ORDERING_CHOICES,
        required=False,
        initial="-created_at",
        widget=forms.Select(attrs={
            "class": "px-3 py-2 bg-surface rounded-md border border-outline-variant text-xs focus:outline-none focus:border-primary"
        })
    )


class EnquiryForm(forms.ModelForm):
    """
    Server-validated inquiry form for buyers to contact artisans about a piece.
    """
    class Meta:
        model = Enquiry
        fields = ["subject", "message"]
        widgets = {
            "subject": forms.TextInput(attrs={
                "class": "w-full px-3 py-2 bg-surface rounded-md border border-outline-variant text-sm focus:outline-none focus:border-primary",
                "placeholder": "e.g. Question about dimensions, custom glazing, or lead time"
            }),
            "message": forms.Textarea(attrs={
                "class": "w-full px-3 py-2 bg-surface rounded-md border border-outline-variant text-sm focus:outline-none focus:border-primary",
                "rows": 4,
                "placeholder": "Describe your question or custom commission request in detail..."
            })
        }

    def clean_subject(self):
        subject = self.cleaned_data.get("subject", "").strip()
        if len(subject) < 3:
            raise forms.ValidationError("Subject must be at least 3 characters long.")
        return subject

    def clean_message(self):
        message = self.cleaned_data.get("message", "").strip()
        if len(message) < 10:
            raise forms.ValidationError("Please provide a detailed inquiry message (at least 10 characters).")
        return message


class BuyOrderForm(forms.ModelForm):
    """
    Direct craft acquisition checkout form for conscious buyers.
    """
    class Meta:
        model = Order
        fields = [
            "quantity",
            "shipping_address",
            "shipping_city",
            "shipping_postal_code",
            "contact_phone",
            "payment_method",
        ]
        widgets = {
            "quantity": forms.NumberInput(attrs={
                "class": "w-24 px-3 py-2 bg-surface rounded-lg border border-outline-variant text-sm font-bold text-center focus:border-primary focus:ring-1 focus:ring-primary",
                "min": "1",
                "value": "1",
            }),
            "shipping_address": forms.Textarea(attrs={
                "class": "w-full px-3.5 py-2.5 bg-surface rounded-lg border border-outline-variant text-sm focus:border-primary focus:ring-1 focus:ring-primary",
                "rows": 2,
                "placeholder": "Street address, flat / house number, landmark...",
            }),
            "shipping_city": forms.TextInput(attrs={
                "class": "w-full px-3.5 py-2.5 bg-surface rounded-lg border border-outline-variant text-sm focus:border-primary focus:ring-1 focus:ring-primary",
                "placeholder": "City / Town (e.g. Mumbai, New Delhi, Jaipur)",
            }),
            "shipping_postal_code": forms.TextInput(attrs={
                "class": "w-full px-3.5 py-2.5 bg-surface rounded-lg border border-outline-variant text-sm focus:border-primary focus:ring-1 focus:ring-primary",
                "placeholder": "PIN / Postal Code",
            }),
            "contact_phone": forms.TextInput(attrs={
                "class": "w-full px-3.5 py-2.5 bg-surface rounded-lg border border-outline-variant text-sm focus:border-primary focus:ring-1 focus:ring-primary",
                "placeholder": "+91 98765 43210",
            }),
            "payment_method": forms.Select(
                choices=[
                    ("UPI / Direct Bank Remittance", "UPI Instant Remittance (GooglePay, PhonePe, Paytm)"),
                    ("Credit / Debit Card", "Credit or Debit Card (Visa, MasterCard, RuPay)"),
                    ("NetBanking Direct Atelier", "NetBanking (Direct Artisan Guild Escrow)"),
                    ("Cash on Delivery", "Ethical Cash on Guild Delivery"),
                ],
                attrs={
                    "class": "w-full px-3.5 py-2.5 bg-surface rounded-lg border border-outline-variant text-sm focus:border-primary focus:ring-1 focus:ring-primary",
                }
            ),
        }

    def clean_quantity(self):
        qty = self.cleaned_data.get("quantity")
        if not qty or qty < 1:
            raise forms.ValidationError("Quantity must be at least 1.")
        return qty

    def clean_shipping_address(self):
        addr = self.cleaned_data.get("shipping_address", "").strip()
        if len(addr) < 5:
            raise forms.ValidationError("Please provide a valid shipping address.")
        return addr
