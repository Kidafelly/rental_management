from django.urls import path
from . import views

urlpatterns = [
    # Dashboard
    path('', views.dashboard, name='dashboard'),
    path('api/dashboard-stats/', views.dashboard_stats_api, name='dashboard_stats_api'),
    
    # Tenants URLs
    path('tenants/', views.tenants_list, name='tenants_list'),
    path('tenants/add/', views.add_tenant, name='add_tenant'),
    path('tenants/<int:tenant_id>/', views.view_tenant, name='view_tenant'),
    path('tenants/<int:tenant_id>/edit/', views.edit_tenant, name='edit_tenant'),
    path('tenants/<int:tenant_id>/delete/', views.delete_tenant, name='delete_tenant'),
    
    # Units URLs
    path('units/', views.units_list, name='units_list'),
    path('units/add/', views.add_unit, name='add_unit'),
    path('units/<int:unit_id>/', views.view_unit, name='view_unit'),
    path('units/<int:unit_id>/edit/', views.edit_unit, name='edit_unit'),
    path('units/<int:unit_id>/delete/', views.delete_unit, name='delete_unit'),
    
    # Payments URLs
    path('payments/', views.payments_list, name='payments_list'),
    path('payments/add/', views.add_payment, name='add_payment'),
    path('payments/<int:payment_id>/', views.view_payment, name='view_payment'),
    path('payments/<int:payment_id>/edit/', views.edit_payment, name='edit_payment'),
    path('payments/<int:payment_id>/delete/', views.delete_payment, name='delete_payment'),
    
    # AJAX endpoints
    path('api/unit/<int:unit_id>/', views.get_unit_details, name='get_unit_details'),
    path('api/tenant/<int:tenant_id>/', views.get_tenant_details, name='get_tenant_details'),

    # Blocks URLs
    path('blocks/', views.blocks_list, name='blocks_list'),
    path('blocks/add/', views.add_block, name='add_block'),
    path('blocks/<int:block_id>/edit/', views.edit_block, name='edit_block'),
    path('ajax/get-units/', views.get_units_by_block, name='get_units_by_block'),

]