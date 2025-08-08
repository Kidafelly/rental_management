from django.db import models
from django.core.validators import RegexValidator
from django.utils.timezone import now
from decimal import Decimal



class Block(models.Model):
    name = models.CharField(max_length=100, unique=True)
    location = models.CharField(max_length=255)
    total_units = models.PositiveIntegerField()
    manager = models.CharField(max_length=100, blank=True, null=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.name} ({self.location})"


class Unit(models.Model):
    UNIT_TYPES = [
        ('studio', 'Studio'),
        ('1br', '1 Bedroom'),
        ('2br', '2 Bedroom'),
        ('3br', '3 Bedroom'),
        ('4br', '4 Bedroom'),
    ]
    
    STATUS_CHOICES = [
        ('vacant', 'Vacant'),
        ('occupied', 'Occupied'),
        ('maintenance', 'Under Maintenance'),
    ]
    
    unit_number = models.CharField(max_length=10, unique=True)
    unit_type = models.CharField(max_length=10, choices=UNIT_TYPES)
    rent_amount = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='vacant')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    block = models.ForeignKey(Block, on_delete=models.CASCADE, related_name='units', null=True, blank=True)
    
    def __str__(self):
        return f"Unit {self.unit_number} - {self.block.name if self.block else 'Unassigned'}"

    class Meta:
        ordering = ['unit_number']


from django.db import models
from django.core.validators import RegexValidator
from django.utils.timezone import now

class Tenant(models.Model):
    PAYMENT_STATUS = [
        ('paid', 'Paid'),
        ('unpaid', 'Unpaid'),
        ('partial', 'Partial'),
        ('overdue', 'Overdue'),
    ]

    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
    )

    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    email = models.EmailField(unique=True)
    phone_number = models.CharField(validators=[phone_regex], max_length=17)
    unit = models.OneToOneField('Unit', on_delete=models.CASCADE, related_name='tenant')
    lease_start_date = models.DateField()
    lease_end_date = models.DateField()
    security_deposit = models.DecimalField(max_digits=10, decimal_places=2)
    payment_status = models.CharField(max_length=10, choices=PAYMENT_STATUS, default='unpaid')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name} - Unit {self.unit.unit_number}"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    def save(self, *args, **kwargs):
        if self.unit:
            self.unit.status = 'occupied'
            self.unit.save()
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        if self.unit:
            self.unit.status = 'vacant'
            self.unit.save()
        super().delete(*args, **kwargs)

    def get_monthly_balance(self, month=None, year=None):
        today = now().date()
        month = month or today.month
        year = year or today.year
        return self.monthly_balances.filter(month=month, year=year).first()

    def get_payment_status(self, month=None, year=None):
        balance = self.get_monthly_balance(month, year)
        if not balance:
            return 'unpaid'
        if balance.balance >= 0:
            return 'paid'
        elif -self.unit.rent_amount < balance.balance < 0:
            return 'partial'
        else:
            return 'unpaid'

    def calculate_balance(self):
        today = now().date()
        current_month_start = today.replace(day=1)

        # Count total months from lease start to today
        months_rented = (today.year - self.lease_start_date.year) * 12 + (today.month - self.lease_start_date.month) + 1
        total_expected_rent = months_rented * self.unit.rent_amount

        total_paid = self.payments.aggregate(total=models.Sum('amount'))['total'] or 0

        paid_this_month = self.payments.filter(
            payment_date__gte=current_month_start
        ).aggregate(total=models.Sum('amount'))['total'] or 0

        balance = total_expected_rent - total_paid
        status = "Fully Paid" if balance <= 0 else ("Partially Paid" if paid_this_month > 0 else "Unpaid")

        return {
            "monthly_rent": self.unit.rent_amount,
            "paid": paid_this_month,
            "balance": balance,
            "status": status
        }

    class Meta:
        ordering = ['first_name', 'last_name']


class TenantBalance(models.Model):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='monthly_balances')
    month = models.PositiveSmallIntegerField()  # 1 - 12
    year = models.PositiveSmallIntegerField()
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))

    class Meta:
        unique_together = ('tenant', 'month', 'year')
        ordering = ['-year', '-month']

    def __str__(self):
        return f"{self.tenant.full_name} - {self.month}/{self.year} Balance: {self.balance}"


class Payment(models.Model):
    PAYMENT_METHODS = [
        ('cash', 'Cash'),
        ('mpesa', 'M-Pesa'),
        ('bank_transfer', 'Bank Transfer'),
        ('cheque', 'Cheque'),
    ]
    
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateField()
    payment_method = models.CharField(max_length=15, choices=PAYMENT_METHODS)
    reference_number = models.CharField(max_length=50, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.update_balance()

    def update_balance(self):
        tenant = self.tenant
        payment_date = self.payment_date
        rent = Decimal(tenant.unit.rent_amount)
        month = payment_date.month
        year = payment_date.year

        balance_entry, created = TenantBalance.objects.get_or_create(
            tenant=tenant, month=month, year=year,
            defaults={'balance': 0.00}
        )

        balance_entry.balance = Decimal(str(balance_entry.balance)) + Decimal(str(self.amount)) - rent
        balance_entry.save()

        tenant.payment_status = tenant.get_payment_status(month, year)
        tenant.save()

    def __str__(self):
        return f"{self.tenant.full_name} - KES {self.amount} - {self.payment_date}"

    class Meta:
        ordering = ['-payment_date']
