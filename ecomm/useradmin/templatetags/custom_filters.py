from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Template filter to get dictionary item by key"""
    if isinstance(dictionary, dict):
        return dictionary.get(key, '')
    return ''

@register.filter(name='dict_get')
def dict_get(value, arg):
    """Alternative name for get_item filter"""
    if isinstance(value, dict):
        return value.get(arg, '')
    return ''