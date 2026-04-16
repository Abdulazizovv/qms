import threading
from django.conf import settings
from .translations import TRANSLATIONS

_thread_locals = threading.local()


def get_current_translations():
    return getattr(_thread_locals, 'translations', TRANSLATIONS.get(settings.LANGUAGE_CODE, {}))


def set_current_language(lang_code):
    if lang_code not in TRANSLATIONS:
        lang_code = settings.LANGUAGE_CODE
    _thread_locals.translations = TRANSLATIONS.get(lang_code, TRANSLATIONS.get(settings.LANGUAGE_CODE, {}))


class TranslationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        language = settings.LANGUAGE_CODE
        if request.user.is_authenticated:
            language = getattr(request.user, 'preferred_language', language)
        else:
            language = request.session.get('preferred_language', language)

        set_current_language(language)
        response = self.get_response(request)
        return response
