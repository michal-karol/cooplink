from urllib.parse import urlsplit

from django import template

register = template.Library()


@register.filter
def display_url(value):
    if not value:
        return ""

    parsed = urlsplit(str(value))
    return parsed.netloc or str(value)
