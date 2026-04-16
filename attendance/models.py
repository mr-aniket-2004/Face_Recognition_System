from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
import numpy as np
import json
import secrets


class Employee(models.Model):
    DEPARTMENT_CHOICES = [
        ('engineering', 'Engineering'),
        ('marketing', 'Marketing'),
        ('hr', 'Human Resources'),
        ('finance', 'Finance'),
        ('operations', 'Operations'),
        ('sales', 'Sales'),
        ('design', 'Design'),
        ('management', 'Management'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='employee')
    employee_id = models.CharField(max_length=20, unique=True)
    department = models.CharField(max_length=50, choices=DEPARTMENT_CHOICES)
    designation = models.CharField(max_length=100, blank=True, default='')
    phone = models.CharField(max_length=20, blank=True, default='')
    photo = models.ImageField(upload_to='employee_photos/', blank=True, null=True)
    face_encoding = models.TextField(blank=True, null=True, help_text='JSON-encoded face encoding array')
    date_joined = models.DateField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    def set_face_encoding(self, encoding):
        """Store numpy array as JSON string."""
        if encoding is not None:
            self.face_encoding = json.dumps(encoding.tolist())

    def get_face_encoding(self):
        """Return numpy array from stored JSON string."""
        if self.face_encoding:
            return np.array(json.loads(self.face_encoding))
        return None

    def __str__(self):
        return f"{self.employee_id} - {self.user.get_full_name()}"

    class Meta:
        ordering = ['-date_joined']


class Attendance(models.Model):
    STATUS_CHOICES = [
        ('present', 'Present'),
        ('late', 'Late'),
    ]

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='attendances')
    date = models.DateField()
    check_in_time = models.TimeField()
    check_out_time = models.TimeField(blank=True, null=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='present')
    marked_by = models.CharField(max_length=20, default='face_recognition')

    class Meta:
        unique_together = ('employee', 'date')
        ordering = ['-date', '-check_in_time']

    def __str__(self):
        return f"{self.employee.employee_id} - {self.date} - {self.status}"


class UserRole(models.Model):
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('employee', 'Employee'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='role')
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='employee')

    def __str__(self):
        return f"{self.user.username} - {self.role}"


class UserOTP(models.Model):
    """Model to store OTP for user authentication."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='otp_codes')
    otp_code = models.CharField(max_length=6, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    used_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - OTP"
    
    @staticmethod
    def generate_otp():
        """Generate a random 6-digit OTP."""
        return ''.join([str(secrets.randbelow(10)) for _ in range(6)])
    
    def is_valid(self):
        """Check if OTP is valid (not expired and not used)."""
        return not self.is_used and timezone.now() <= self.expires_at
    
    def mark_as_used(self):
        """Mark OTP as used."""
        self.is_used = True
        self.used_at = timezone.now()
        self.save()
    
    @classmethod
    def create_otp_for_user(cls, user, expiry_minutes=2):
        """Create a new OTP for a user."""
        # Delete previous unused OTPs for this user
        cls.objects.filter(user=user, is_used=False).delete()
        
        otp_code = cls.generate_otp()
        expires_at = timezone.now() + timedelta(minutes=expiry_minutes)
        
        otp_obj = cls.objects.create(
            user=user,
            otp_code=otp_code,
            expires_at=expires_at
        )
        return otp_obj
