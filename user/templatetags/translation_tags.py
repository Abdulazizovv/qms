from django import template
import threading
from user.translations import LANGUAGE_CHOICES
from user.translation_middleware import get_current_translations

register = template.Library()


@register.filter
def t(key):
    translations = get_current_translations()
    return translations.get(key, key)


@register.filter
def language_name(code):
    return dict(LANGUAGE_CHOICES).get(code, code)
