# core/templatetags/url_replace.py
from django import template
from urllib.parse import urlencode

register = template.Library()

@register.simple_tag
def url_replace(request, **kwargs):
    """
    Replace or add parameters to the current URL
    Usage: {% url_replace request page=2 %}
    """
    query = request.GET.copy()
    
    for key, value in kwargs.items():
        if value:
            query[key] = value
        else:
            # Remove parameter if value is None or empty
            query.pop(key, None)
    
    return query.urlencode()