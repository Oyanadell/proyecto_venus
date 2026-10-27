from django import template

register = template.Library()


@register.filter
def clp(valor):
    """Formatea un monto como peso chileno: 25000 -> $25.000"""
    try:
        return "$" + f"{int(valor):,}".replace(",", ".")
    except (TypeError, ValueError):
        return valor
