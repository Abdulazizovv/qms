from django.conf import settings
from .translations import LANGUAGE_CHOICES, TRANSLATIONS


def language_context(request):
    language = settings.LANGUAGE_CODE
    if request.user.is_authenticated:
        language = getattr(request.user, 'preferred_language', language)
    else:
        language = request.session.get('preferred_language', language)

    if language not in TRANSLATIONS:
        language = settings.LANGUAGE_CODE

    request.session['preferred_language'] = language

    return {
        'LANGUAGE_CODE': language,
        'LANGUAGES': LANGUAGE_CHOICES,
        'translations': TRANSLATIONS[language],
    }
