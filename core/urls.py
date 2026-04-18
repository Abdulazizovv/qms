from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

from common.views import queue_display, team_page

urlpatterns = [
    path('admin/',     admin.site.urls),
    path('auth/',      include('user.urls')),
    path('dashboard/', include('common.urls')),
    path('business/',  include('business.urls')),
    path('operator/',  include('ticket.urls')),
    path('display/<int:branch_pk>/', queue_display, name='queue_display'),
    path('about/team/', team_page, name='team'),
    path('',           include('botapp.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += staticfiles_urlpatterns()
