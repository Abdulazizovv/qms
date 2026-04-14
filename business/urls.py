from django.urls import path
from business import views

urlpatterns = [
    path('', views.overview, name='overview'),
    path("business/<int:pk>/", views.business_detail, name="business_detail" )
    
]
