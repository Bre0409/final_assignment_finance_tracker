from decimal import Decimal, InvalidOperation
from django import template

register = template.Library()


@register.filter
def mul(value, arg):
    """
    Multiply two numbers and return currency-friendly 2dp Decimal.
    Used for template conversion like: {{ amount|mul:rate }}
    """
    try:
        return (Decimal(str(value)) * Decimal(str(arg))).quantize(Decimal("0.01"))
    except (InvalidOperation, TypeError):
        return ""
