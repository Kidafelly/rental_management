from django.contrib import admin
from .models import Unit, Tenant, Payment

@admin.register(Unit)
class UnitAdmin(admin.ModelAdmin):
    list_display = ['unit_number', 'unit_type', 'rent_amount', 'status', 'created_at']
    list_filter = ['unit_type', 'status']
    search_fields = ['unit_number']

@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'unit', 'email', 'phone_number', 'payment_status', 'created_at']
    list_filter = ['payment_status', 'unit__unit_type']
    search_fields = ['first_name', 'last_name', 'email', 'unit__unit_number']

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['tenant', 'amount', 'payment_date', 'payment_method']
    list_filter = ['payment_method', 'payment_date']
    search_fields = ['tenant__first_name', 'tenant__last_name', 'reference_number']

from .models import Block
admin.site.register(Block)
