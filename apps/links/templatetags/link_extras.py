from urllib.parse import quote, urlsplit

from django import template

register = template.Library()


@register.filter
def display_url(value):
    if not value:
        return ""

    parsed = urlsplit(str(value))
    return parsed.netloc or str(value)


@register.filter
def favicon_url(value):
    if not value:
        return ""

    parsed = urlsplit(str(value))
    domain = parsed.netloc

    if not domain:
        return ""

    return f"https://www.google.com/s2/favicons?domain={quote(domain)}&sz=64"
