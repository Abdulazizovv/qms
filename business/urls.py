from django.urls import path
from business import views

app_name = 'business'

urlpatterns = [
    # Business CRUD
    path('',                             views.business_list,   name='list'),
    path('create/',                      views.business_create, name='create'),
    path('<int:pk>/',                    views.business_detail, name='detail'),
    path('<int:pk>/edit/',               views.business_edit,   name='edit'),
    path('<int:pk>/delete/',             views.business_delete, name='delete'),

    # Branch
    path('<int:biz_pk>/branch/create/',          views.branch_create, name='branch_create'),
    path('<int:biz_pk>/branch/<int:pk>/edit/',    views.branch_edit,   name='branch_edit'),
    path('<int:biz_pk>/branch/<int:pk>/delete/',  views.branch_delete, name='branch_delete'),

    # Service
    path('<int:biz_pk>/branch/<int:branch_pk>/service/create/', views.service_create, name='service_create'),
    path('<int:biz_pk>/service/<int:pk>/edit/',                  views.service_edit,   name='service_edit'),
    path('<int:biz_pk>/service/<int:pk>/delete/',                views.service_delete, name='service_delete'),

    # Operator
    path('<int:biz_pk>/operators/',              views.operator_list,   name='operator_list'),
    path('<int:biz_pk>/operators/create/',        views.operator_create, name='operator_create'),
    path('<int:biz_pk>/operators/<int:pk>/edit/', views.operator_edit,   name='operator_edit'),
    path('<int:biz_pk>/operators/<int:pk>/delete/', views.operator_delete, name='operator_delete'),
]
