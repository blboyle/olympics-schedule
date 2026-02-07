from django import template
from django.utils.http import urlencode

register = template.Library()


@register.simple_tag(takes_context=True)
def query_string(context, **kwargs):
    """Build query string preserving existing params."""
    request = context.get("request")
    if not request:
        return urlencode(kwargs)

    params = request.GET.copy()
    for key, value in kwargs.items():
        if value:
            params[key] = value
        elif key in params:
            del params[key]
    return params.urlencode()


@register.filter
def toggle_dir(current_dir):
    """Toggle sort direction."""
    return "desc" if current_dir == "asc" else "asc"
