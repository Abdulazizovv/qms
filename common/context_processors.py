from django.conf import settings


def site_settings(request):
    return {
        'TELEGRAM_BOT_USERNAME': getattr(settings, 'TELEGRAM_BOT_USERNAME', 'tartibli_bot'),
    }
