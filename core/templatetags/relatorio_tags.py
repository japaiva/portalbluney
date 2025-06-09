from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Template filter para acessar itens de dicionário"""
    if dictionary and hasattr(dictionary, 'get'):
        return dictionary.get(key, 0)
    elif dictionary and isinstance(dictionary, dict):
        return dictionary.get(key, 0)
    return 0

@register.filter
def div(value, arg):
    """Template filter para divisão"""
    try:
        return float(value) / float(arg)
    except (ValueError, ZeroDivisionError):
        return 0

@register.filter
def add(value, arg):
    """Template filter para adição"""
    try:
        return float(value) + float(arg)
    except (ValueError, TypeError):
        return value