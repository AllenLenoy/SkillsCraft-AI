from django import template
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter(name="inr_format")
def inr_format(value):
    """
    Custom DTL filter: Formats a numerical value into Indian Rupee currency notation.
    Example: {{ 12500|inr_format }} -> '₹12,500'
    """
    try:
        val = float(value)
        # Format with comma separators and no decimal if whole number
        if val.is_integer():
            return f"₹{int(val):,}"
        return f"₹{val:,.2f}"
    except (ValueError, TypeError):
        return value


@register.filter(name="artisan_initials")
def artisan_initials(name):
    """
    Custom DTL filter: Generates clean 1-2 letter monogram initials from a studio or person name.
    Example: 'Kutch Clay Works' -> 'KC'
    """
    if not name:
        return "CC"
    words = str(name).strip().split()
    if len(words) == 1:
        return words[0][:2].upper()
    return f"{words[0][0]}{words[1][0]}".upper()


@register.simple_tag(name="verified_maker_badge")
def verified_maker_badge(is_verified=False):
    """
    Custom DTL simple_tag: Generates a verified guild maker badge markup.
    """
    if is_verified:
        return mark_safe(
            '<span class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-bold bg-secondary/10 text-secondary border border-secondary/20" title="Guild Verified Studio">'
            '<span class="material-symbols-outlined text-[13px]">verified</span>'
            'Verified Atelier'
            '</span>'
        )
    return mark_safe(
        '<span class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-surface-container text-on-surface-variant">'
        '<span class="material-symbols-outlined text-[13px]">schedule</span>'
        'Under Review'
        '</span>'
    )


@register.simple_tag(name="stock_status")
def stock_status(stock_quantity):
    """
    Custom DTL simple_tag: Renders appropriate craft inventory status.
    """
    try:
        qty = int(stock_quantity)
        if qty <= 0:
            return mark_safe('<span class="text-xs font-bold text-error">Out of Stock</span>')
        elif qty <= 3:
            return mark_safe(f'<span class="text-xs font-bold text-amber-600">Only {qty} left in atelier</span>')
        return mark_safe('<span class="text-xs font-semibold text-emerald-700">In Studio Stock</span>')
    except (ValueError, TypeError):
        return ""
