from django import forms
from django.contrib.auth.models import User
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
    username = forms.CharField(max_length=150, widget=forms.TextInput(attrs={
        'placeholder': 'Username', 'class': 'form-input'
    }))
    # password = forms.CharField(widget=forms.PasswordInput(attrs={
    #     'placeholder': 'Password', 'class': 'form-input'
    # }))
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

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError('This username is already in use.')
        return username

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
