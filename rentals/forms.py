from django import forms
from .models import Tenant,Block, Unit, Payment

class TenantForm(forms.ModelForm):
    block = forms.ModelChoiceField(
        queryset=Block.objects.all(),
        required=True,
        empty_label="Select Block",
        widget=forms.Select(attrs={'class': 'form-input','id': 'id_block'})
    )
    class Meta:
        model = Tenant
        fields = ['first_name', 'last_name', 'email', 'phone_number', 
                 'block', 'unit', 'lease_start_date', 'lease_end_date', 'security_deposit']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'First Name'}),
            'last_name': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Last Name'}),
            'email': forms.EmailInput(attrs={'class': 'form-input', 'placeholder': 'Email Address'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-input', 'placeholder': '+254 712 345 678'}),
            'unit': forms.Select(attrs={'class': 'form-input', 'id': 'id_unit'}),
            'lease_start_date': forms.DateInput(attrs={'class': 'form-input', 'type': 'date'}),
            'lease_end_date': forms.DateInput(attrs={'class': 'form-input', 'type': 'date'}),
            'security_deposit': forms.NumberInput(attrs={'class': 'form-input', 'placeholder': 'Security Deposit'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only show vacant units in the dropdown
        self.fields['unit'].queryset = Unit.objects.filter(status='vacant')

class UnitForm(forms.ModelForm):
    class Meta:
        model = Unit
        fields = ['unit_number', 'unit_type', 'rent_amount', 'description', 'block'] 
        widgets = {
            'unit_number': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g., A1, B2'}),
            'unit_type': forms.Select(attrs={'class': 'form-select'}),
            'rent_amount': forms.NumberInput(attrs={'class': 'form-input', 'placeholder': 'Monthly Rent'}),
            'description': forms.Textarea(attrs={'class': 'form-input', 'rows': 3, 'placeholder': 'Unit description...'}),
            'block': forms.Select(attrs={'class': 'form-select'}),  
        }


class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ['tenant', 'amount', 'payment_date', 'payment_method', 'reference_number', 'notes']
        widgets = {
            'tenant': forms.Select(attrs={'class': 'form-select'}),
            'amount': forms.NumberInput(attrs={'class': 'form-input', 'placeholder': 'Payment Amount'}),
            'payment_date': forms.DateInput(attrs={'class': 'form-input', 'type': 'date'}),
            'payment_method': forms.Select(attrs={'class': 'form-select'}),
            'reference_number': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Reference Number'}),
            'notes': forms.Textarea(attrs={'class': 'form-input', 'rows': 3, 'placeholder': 'Additional notes...'}),
        }

from .models import Block

class BlockForm(forms.ModelForm):
    class Meta:
        model = Block
        fields = ['name', 'location', 'total_units', 'manager', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g., Ngara Flats'}),
            'location': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g., Nairobi, CBD'}),
            'total_units': forms.NumberInput(attrs={'class': 'form-input', 'placeholder': 'e.g., 12'}),
            'manager': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Optional – Block manager name'}),
            'description': forms.Textarea(attrs={'class': 'form-input', 'placeholder': 'Optional – Description or notes', 'rows': 3}),
        }
