import datetime
from datetime import timedelta

from django import forms
from django.contrib.auth.models import User
from django.utils import timezone
from .models import Employee


class EmployeeForm(forms.ModelForm):
    first_name = forms.CharField(max_length=30, widget=forms.TextInput(attrs={
        'placeholder': 'First Name', 'class': 'form-input'
    }))
    last_name = forms.CharField(max_length=30, widget=forms.TextInput(attrs={
        'placeholder': 'Last Name', 'class': 'form-input'
    }))
    email = forms.EmailField(widget=forms.EmailInput(attrs={
        'placeholder': 'Email Address', 'class': 'form-input'
    }))
   
    captured_photo = forms.CharField(widget=forms.HiddenInput(attrs={
        'id': 'id_captured_photo'
    }), required=False)

    class Meta:
        model = Employee
        fields = ['employee_id', 'department', 'designation', 'phone', 'photo']
        widgets = {
            'employee_id': forms.TextInput(attrs={'placeholder': 'e.g. EMP001', 'class': 'form-input'}),
            'department': forms.Select(attrs={'class': 'form-input'}),
            'designation': forms.TextInput(attrs={'placeholder': 'e.g. Software Engineer', 'class': 'form-input'}),
            'phone': forms.TextInput(attrs={'placeholder': 'Phone Number', 'class': 'form-input'}),
        }

    def generate_username(self):
        """Generate username using department first letter + first name + employee ID"""
        department = self.cleaned_data.get('department')
        first_name = self.cleaned_data.get('first_name', '').strip()
        employee_id = self.cleaned_data.get('employee_id', '').strip()

        if not department or not first_name or not employee_id:
            return None

        # Get department first letter (lowercase)
        dept_letter = department[0].upper()

        # Clean first name (remove spaces, special chars, lowercase)
        clean_first_name = ''.join(c for c in first_name.lower() if c.isalnum())

        # Clean employee ID (remove spaces, special chars)
        clean_emp_id = ''.join(c for c in employee_id if c.isalnum())

        # Base username: dept_letter + first_name + emp_id
        base_username = f"{dept_letter}_{clean_first_name}_{clean_emp_id}"

        # Ensure username is not too long (max 150 chars)
        if len(base_username) > 150:
            base_username = base_username[:150]

        # Check for uniqueness and add number suffix if needed
        username = base_username
        counter = 1
        while User.objects.filter(username__iexact=username).exists():
            suffix = str(counter)
            # Truncate base_username if needed to fit suffix
            max_base_length = 150 - len(suffix)
            truncated_base = base_username[:max_base_length]
            username = f"{truncated_base}{suffix}"
            counter += 1

        return username

    def clean(self):
        cleaned_data = super().clean()

        # Auto-generate username
        username = self.generate_username()
        if username:
            cleaned_data['username'] = username
        else:
            raise forms.ValidationError('Unable to generate username. Please check department, first name, and employee ID.')

        return cleaned_data

    # def clean_username(self):
    #     username = self.cleaned_data.get('username')
    #     if User.objects.filter(username__iexact=username).exists():
    #         raise forms.ValidationError('This username is already in use.')
    #     return username

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('This email address is already registered.')
        return email

    def clean_employee_id(self):
        employee_id = self.cleaned_data.get('employee_id')
        if Employee.objects.filter(employee_id__iexact=employee_id).exists():
            raise forms.ValidationError('This employee ID is already in use.')
        return employee_id

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if phone and Employee.objects.filter(phone=phone).exists():
            raise forms.ValidationError('This phone number is already in use.')
        return phone


class EmployeeEditForm(forms.ModelForm):
    first_name = forms.CharField(max_length=30, widget=forms.TextInput(attrs={'class': 'form-input'}))
    last_name = forms.CharField(max_length=30, widget=forms.TextInput(attrs={'class': 'form-input'}))
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-input'}))

    class Meta:
        model = Employee
        fields = ['department', 'designation', 'phone', 'photo']
        widgets = {
            'department': forms.Select(attrs={'class': 'form-input'}),
            'designation': forms.TextInput(attrs={'class': 'form-input'}),
            'phone': forms.TextInput(attrs={'class': 'form-input'}),
        }


class ChangePasswordForm(forms.Form):
    current_password = forms.CharField(widget=forms.PasswordInput(attrs={
        'placeholder': 'Current Password', 'class': 'form-input'
    }))
    new_password = forms.CharField(widget=forms.PasswordInput(attrs={
        'placeholder': 'New Password', 'class': 'form-input'
    }))
    confirm_password = forms.CharField(widget=forms.PasswordInput(attrs={
        'placeholder': 'Confirm New Password', 'class': 'form-input'
    }))

    def clean(self):
        cleaned_data = super().clean()
        new_pw = cleaned_data.get('new_password')
        confirm_pw = cleaned_data.get('confirm_password')
        if new_pw and confirm_pw and new_pw != confirm_pw:
            raise forms.ValidationError("Passwords don't match.")
        return cleaned_data


class SetPasswordForm(forms.Form):
    otp_code = forms.CharField(widget=forms.TextInput(attrs={
        'placeholder': 'OTP Code', 'class': 'form-input'
    }))
    new_password = forms.CharField(widget=forms.PasswordInput(attrs={
        'placeholder': 'New Password', 'class': 'form-input'
    }))
    confirm_password = forms.CharField(widget=forms.PasswordInput(attrs={
        'placeholder': 'Confirm New Password', 'class': 'form-input'
    }))

    def clean(self):
        cleaned_data = super().clean()
        new_pw = cleaned_data.get('new_password')
        confirm_pw = cleaned_data.get('confirm_password')
        if new_pw and confirm_pw and new_pw != confirm_pw:
            raise forms.ValidationError("Passwords don't match.")
        return cleaned_data


class ManualCheckoutForm(forms.Form):
    checkout_time = forms.TimeField(
        widget=forms.TimeInput(attrs={
            'type': 'time',
            'class': 'form-input',
            'required': True
        }),
        help_text="Select the time you actually checked out"
    )
    checkout_date = forms.DateField(
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-input',
            'required': True
        }),
        help_text="Select the date you checked out (usually today)"
    )

    def __init__(self, *args, **kwargs):
        self.check_in_datetime = kwargs.pop('check_in_datetime', None)
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        checkout_time = cleaned_data.get('checkout_time')
        checkout_date = cleaned_data.get('checkout_date')

        if checkout_time and checkout_date and self.check_in_datetime:
            checkout_datetime = datetime.datetime.combine(checkout_date, checkout_time)
            checkout_datetime = timezone.make_aware(checkout_datetime)

            # Check if checkout is after check-in
            if checkout_datetime <= self.check_in_datetime:
                raise forms.ValidationError("Checkout time must be after check-in time.")

            # Check if checkout is not in the future
            now = timezone.now()
            if checkout_datetime > now:
                raise forms.ValidationError("Checkout time cannot be in the future.")

            # Check if hours worked don't exceed reasonable limit (24 hours)
            hours_worked = (checkout_datetime - self.check_in_datetime).total_seconds() / 3600
            if hours_worked > 24:
                raise forms.ValidationError("Hours worked cannot exceed 24 hours.")

        return cleaned_data
