from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Sum, Count, Q, F
from django.utils import timezone
from django.http import JsonResponse
from datetime import datetime, timedelta
from .models import Tenant, Unit, Payment
from .forms import TenantForm, UnitForm, PaymentForm
from decimal import Decimal
from .models import Tenant, Unit, Block, Payment

from django.shortcuts import render
from django.db.models import Count, Sum, Q, F
from django.utils import timezone
from .models import Tenant, Unit, Block, Payment, TenantBalance

def dashboard(request):
    now = timezone.now()
    current_month = now.month
    current_year = now.year

    # General stats
    total_tenants = Tenant.objects.count()
    total_units = Unit.objects.count()
    occupied_units = Unit.objects.filter(status='occupied').count()
    vacant_units = Unit.objects.filter(status='vacant').count()

    # Rent stats
    total_expected_rent = Unit.objects.filter(status='occupied').aggregate(
        total=Sum('rent_amount')
    )['total'] or 0

    payments_this_month = Payment.objects.filter(
        payment_date__month=current_month,
        payment_date__year=current_year
    ).aggregate(total=Sum('amount'))['total'] or 0

    unpaid_rent = total_expected_rent - payments_this_month
    collection_percentage = int((payments_this_month / total_expected_rent) * 100) if total_expected_rent else 0

    # Recent payments
    recent_payments = Payment.objects.select_related('tenant', 'tenant__unit').order_by('-payment_date')[:5]

    # Unpaid tenants this month
    paid_ids = Payment.objects.filter(
        payment_date__month=current_month,
        payment_date__year=current_year
    ).values_list('tenant_id', flat=True)

    unpaid_tenants = Tenant.objects.exclude(id__in=paid_ids).count()

    # Per-block stats
    blocks = Block.objects.annotate(
        annotated_total_units=Count('units', distinct=True),
        occupied_units=Count('units', filter=Q(units__status='occupied'), distinct=True),
        tenants_count=Count('units__tenant', distinct=True),
        total_rent=Sum(
            'units__tenant__payments__amount',
            filter=Q(units__tenant__payments__payment_date__month=current_month,
                     units__tenant__payments__payment_date__year=current_year)
        ),
        expected_rent=Sum(
            'units__rent_amount',
            filter=Q(units__status='occupied')
        )
    )
	# Post-process blocks for occupancy %
    for block in blocks:
        block_tenants = Tenant.objects.filter(unit__block=block)
        block.tenants_count_display = block_tenants.count()
        block.vacant_units = block.annotated_total_units - block.tenants_count_display

        # Count fully paid tenants
        fully_paid_count = 0
        for tenant in block_tenants:
            balance = tenant.monthly_balances.filter(month=current_month, year=current_year).first()
            if balance and balance.balance <= 0:
                fully_paid_count += 1

        block.occupancy_percent = round(
            (block.occupied_units / block.annotated_total_units) * 100
        ) if block.annotated_total_units else 0

        block.fully_paid_count = fully_paid_count

    context = {
        'total_tenants': total_tenants,
        'total_units': total_units,
        'occupied_units': occupied_units,
        'vacant_units': vacant_units,
        'total_expected_rent': total_expected_rent,
        'payments_this_month': payments_this_month,
        'unpaid_rent': unpaid_rent,
        'collection_percentage': collection_percentage,
        'recent_payments': recent_payments,
        'unpaid_tenants': unpaid_tenants,
        'blocks': blocks,
    }

    return render(request, 'rentals/dashboard.html', context)




# TENANTS VIEWS
def add_tenant(request):
    if request.method == 'POST':
        form = TenantForm(request.POST)
        if form.is_valid():
            tenant = form.save()
            messages.success(request, f'Tenant {tenant.full_name} added successfully!')
            return redirect('tenants_list')
    else:
        form = TenantForm()
    
    return render(request, 'rentals/add_tenant.html', {'form': form})

def edit_tenant(request, tenant_id):
    tenant = get_object_or_404(Tenant, id=tenant_id)
    if request.method == 'POST':
        form = TenantForm(request.POST, instance=tenant)
        if form.is_valid():
            tenant = form.save()
            messages.success(request, f'Tenant {tenant.full_name} updated successfully!')
            return redirect('tenants_list')
    else:
        form = TenantForm(instance=tenant)
    
    return render(request, 'rentals/edit_tenant.html', {
        'form': form,
        'tenant': tenant
    })

from datetime import date
from django.db.models import Sum
from django.utils.timezone import now

from django.shortcuts import render, get_object_or_404
from django.db.models import Sum
from django.utils.timezone import now
from .models import Tenant, Payment

def view_tenant(request, tenant_id):
    tenant = get_object_or_404(Tenant, id=tenant_id)
    payments = Payment.objects.filter(tenant=tenant).order_by('-payment_date')[:10]

    # Use wallet dict from tenant.calculate_balance()
    wallet = tenant.calculate_balance()

    # Extract payment status and CSS class
    payment_status = wallet['status']
    status_class = payment_status.lower().replace(" ", "-")

    context = {
        'tenant': tenant,
        'payments': payments,
        'total_paid': payments.aggregate(total=Sum('amount'))['total'] or 0,
        'last_payment': payments.first(),
        'wallet': wallet,  # ✅ Add wallet to context
        'payment_status': payment_status,
        'status_class': status_class,
    }

    return render(request, 'rentals/view_tenant.html', context)



def delete_tenant(request, tenant_id):
    tenant = get_object_or_404(Tenant, id=tenant_id)
    if request.method == 'POST':
        tenant_name = tenant.full_name
        tenant.delete()
        messages.success(request, f'Tenant {tenant_name} deleted successfully!')
        return redirect('tenants_list')
    
    return render(request, 'rentals/delete_tenant.html', {'tenant': tenant})

from django.shortcuts import render
from datetime import date
from .models import Tenant, Block  

def tenants_list(request):
    today = date.today()

    # Get optional search and block filters
    search_query = request.GET.get('search', '')
    block_id = request.GET.get('block')

    tenants = Tenant.objects.select_related('unit', 'unit__block').all()

    if search_query:
        tenants = tenants.filter(full_name__icontains=search_query)

    if block_id:
        tenants = tenants.filter(unit__block__id=block_id)

    # Calculate balances and statuses for each tenant
    for tenant in tenants:
        balance_summary = tenant.calculate_balance()
        tenant.monthly_rent = balance_summary['monthly_rent']
        tenant.paid_this_month = balance_summary['paid']
        tenant.balance_due = balance_summary['balance']
        tenant.wallet_status = balance_summary['status']

    blocks = Block.objects.all()  # For filter dropdown

    return render(request, 'rentals/tenants_list.html', {
        'search_query': search_query,
        'tenants': tenants,
        'blocks': blocks,
    })



# UNITS VIEWS
def units_list(request):
    block_filter = request.GET.get('block')
    units = Unit.objects.all()

    if block_filter:
        units = units.filter(block__id=block_filter)

    blocks = Block.objects.all()
    vacant_count = units.filter(status='vacant').count()  # ✅ Count vacant here

    return render(request, 'rentals/units_list.html', {
        'units': units,
        'blocks': blocks,
        'vacant_count': vacant_count,  # ✅ Pass it to the template
    })



def add_unit(request):
    if request.method == 'POST':
        form = UnitForm(request.POST)
        if form.is_valid():
            unit = form.save()
            messages.success(request, f'Unit {unit.unit_number} added successfully!')
            return redirect('units_list')
    else:
        form = UnitForm()
    
    return render(request, 'rentals/add_unit.html', {'form': form})

def edit_unit(request, unit_id):
    unit = get_object_or_404(Unit, id=unit_id)
    if request.method == 'POST':
        form = UnitForm(request.POST, instance=unit)
        if form.is_valid():
            unit = form.save()
            messages.success(request, f'Unit {unit.unit_number} updated successfully!')
            return redirect('units_list')
    else:
        form = UnitForm(instance=unit)
    
    return render(request, 'rentals/edit_unit.html', {
        'form': form,
        'unit': unit
    })

def view_unit(request, unit_id):
    unit = get_object_or_404(Unit, id=unit_id)
    context = {
        'unit': unit,
    }
    
    return render(request, 'rentals/view_unit.html', context)

def delete_unit(request, unit_id):
    unit = get_object_or_404(Unit, id=unit_id)
    if request.method == 'POST':
        unit_number = unit.unit_number
        unit.delete()
        messages.success(request, f'Unit {unit_number} deleted successfully!')
        return redirect('units_list')
    
    return render(request, 'rentals/delete_unit.html', {'unit': unit})

# PAYMENTS VIEWS
def payments_list(request):
    payments = Payment.objects.select_related('tenant', 'tenant__unit').all()
    
    # Sorting
    sort_by = request.GET.get('sort', '-payment_date')
    payments = payments.order_by(sort_by)
    
    return render(request, 'rentals/payments_list.html', {
        'payments': payments
    })

def add_payment(request):
    if request.method == 'POST':
        form = PaymentForm(request.POST)
        if form.is_valid():
            payment = form.save()
            tenant = payment.tenant

            # Recalculate balance after payment
            balance = tenant.calculate_balance()
            tenant.balance = balance if isinstance(balance, (int, float)) else balance.get('balance', 0)
            tenant.payment_status = 'paid' if tenant.balance <= 0 else 'partial'


            messages.success(request, f'Payment of KES {payment.amount} recorded successfully!')
            return redirect('payments_list')
    else:
        form = PaymentForm()
    
    return render(request, 'rentals/add_payment.html', {'form': form})


def edit_payment(request, payment_id):
    payment = get_object_or_404(Payment, id=payment_id)
    if request.method == 'POST':
        form = PaymentForm(request.POST, instance=payment)
        if form.is_valid():
            payment = form.save()
            tenant = payment.tenant
            tenant.balance = tenant.calculate_balance()
            tenant.payment_status = 'paid' if tenant.balance <= 0 else 'partial'
            tenant.save()
            messages.success(request, f'Payment updated successfully!')
            return redirect('payments_list')
    else:
        form = PaymentForm(instance=payment)
    
    return render(request, 'rentals/edit_payment.html', {'form': form, 'payment': payment})


def view_payment(request, payment_id):
    payment = get_object_or_404(Payment, id=payment_id)
    context = {
        'payment': payment,
    }
    
    return render(request, 'rentals/view_payment.html', context)

def delete_payment(request, payment_id):
    payment = get_object_or_404(Payment, id=payment_id)
    if request.method == 'POST':
        amount = payment.amount
        tenant_name = payment.tenant.full_name
        payment.delete()
        messages.success(request, f'Payment of KES {amount} from {tenant_name} deleted successfully!')
        return redirect('payments_list')
    
    return render(request, 'rentals/delete_payment.html', {'payment': payment})

# AJAX VIEWS for dynamic functionality
def get_unit_details(request, unit_id):
    """Get unit details for AJAX requests"""
    unit = get_object_or_404(Unit, id=unit_id)
    data = {
        'unit_number': unit.unit_number,
        'unit_type': unit.get_unit_type_display(),
        'rent_amount': float(unit.rent_amount),
        'status': unit.status,
        'tenant': unit.tenant.full_name if unit.tenant else None,
    }
    return JsonResponse(data)

def get_tenant_details(request, tenant_id):
    """Get tenant details for AJAX requests"""
    tenant = get_object_or_404(Tenant, id=tenant_id)
    data = {
        'full_name': tenant.full_name,
        'email': tenant.email,
        'phone_number': tenant.phone_number,
        'unit': tenant.unit.unit_number,
        'rent_amount': float(tenant.unit.rent_amount),
        'payment_status': tenant.payment_status,
    }
    return JsonResponse(data)

def dashboard_stats_api(request):
    """API endpoint for dashboard statistics"""
    current_month = timezone.now().month
    current_year = timezone.now().year
    
    # Calculate stats
    total_tenants = Tenant.objects.count()
    total_units = Unit.objects.count()
    occupied_units = Unit.objects.filter(status='occupied').count()
    vacant_units = Unit.objects.filter(status='vacant').count()
    
    total_expected_rent = Unit.objects.filter(status='occupied').aggregate(
        total=Sum('rent_amount')
    )['total'] or 0
    
    payments_this_month = Payment.objects.filter(
        payment_date__month=current_month,
        payment_date__year=current_year
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    collection_percentage = 0
    if total_expected_rent > 0:
        collection_percentage = int((payments_this_month / total_expected_rent) * 100)
    
    data = {
        'total_tenants': total_tenants,
        'total_units': total_units,
        'occupied_units': occupied_units,
        'vacant_units': vacant_units,
        'total_expected_rent': float(total_expected_rent),
        'payments_this_month': float(payments_this_month),
        'collection_percentage': collection_percentage,
    }
    
    return JsonResponse(data)

from django.shortcuts import render, redirect, get_object_or_404
from .models import Block
from .forms import BlockForm

from django.db.models import Q

def blocks_list(request):
    search_query = request.GET.get('search', '')
    if search_query:
        blocks = Block.objects.filter(
            Q(name__icontains=search_query) |
            Q(location__icontains=search_query)
        )
    else:
        blocks = Block.objects.all()
    
    return render(request, 'rentals/blocks_list.html', {
        'blocks': blocks,
        'search_query': search_query
    })


def add_block(request):
    if request.method == 'POST':
        form = BlockForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Block added successfully.")
            return redirect('blocks_list')
    else:
        form = BlockForm()
    return render(request, 'rentals/add_block.html', {'form': form})


def edit_block(request, block_id):
    block = get_object_or_404(Block, id=block_id)
    if request.method == 'POST':
        form = BlockForm(request.POST, instance=block)
        if form.is_valid():
            form.save()
            messages.success(request, f"Block '{block.name}' updated successfully.")
            return redirect('blocks_list')
    else:
        form = BlockForm(instance=block)
    
    return render(request, 'rentals/edit_block.html', {'form': form, 'block': block})

from django.http import JsonResponse
from .models import Unit

def get_units_by_block(request):
    block_id = request.GET.get('block_id')
    units = Unit.objects.filter(block_id=block_id).values('id', 'unit_number')
    return JsonResponse(list(units), safe=False)


