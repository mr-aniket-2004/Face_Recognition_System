from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
import numpy as np
import json
import secrets
from django_otp.models import Device
from django_otp.plugins.otp_totp.models import TOTPDevice


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


class AdminTOTPDevice(TOTPDevice):
    """TOTP device for admin users with enhanced security."""
    
    class Meta:
        verbose_name = "Admin TOTP Device"
        verbose_name_plural = "Admin TOTP Devices"
    
    def __str__(self):
        return f"TOTP Device for {self.user.username}"


class AdminBackupCode(models.Model):
    """Backup codes for admin password reset when TOTP device is unavailable."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='admin_backup_codes')
    code = models.CharField(max_length=10, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    used_at = models.DateTimeField(null=True, blank=True)
    is_used = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Admin Backup Code"
        verbose_name_plural = "Admin Backup Codes"
    
    def __str__(self):
        return f"Backup Code for {self.user.username}"
    
    @staticmethod
    def generate_backup_codes(count=10):
        """Generate a list of backup codes."""
        codes = []
        for _ in range(count):
            code = ''.join(secrets.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789') for _ in range(8))
            codes.append(code.upper())
        return codes
    
    @classmethod
    def create_backup_codes_for_user(cls, user, count=10):
        """Create backup codes for a user, replacing existing unused ones."""
        # Delete existing unused codes
        cls.objects.filter(user=user, is_used=False).delete()
        
        codes = cls.generate_backup_codes(count)
        backup_codes = []
        
        for code in codes:
            backup_codes.append(cls.objects.create(user=user, code=code))
        
        return backup_codes
    
    def mark_as_used(self):
        """Mark backup code as used."""
        self.is_used = True
        self.used_at = timezone.now()
        self.save()


class AdminSecurityQuestion(models.Model):
    """Security questions for additional admin verification."""
    QUESTION_CHOICES = [
        ('mother_maiden', "What is your mother's maiden name?"),
        ('first_pet', "What was the name of your first pet?"),
        ('birth_city', "In what city were you born?"),
        ('first_school', "What was the name of your first school?"),
        ('favorite_teacher', "Who was your favorite teacher?"),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='security_questions')
    question = models.CharField(max_length=50, choices=QUESTION_CHOICES)
    answer = models.CharField(max_length=255)  # Will be hashed
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('user', 'question')
        verbose_name = "Admin Security Question"
        verbose_name_plural = "Admin Security Questions"
    
    def __str__(self):
        return f"{self.user.username} - {self.get_question_display()}"
    
    def set_answer(self, raw_answer):
        """Hash the answer before saving."""
        import hashlib
        self.answer = hashlib.sha256(raw_answer.lower().strip().encode()).hexdigest()
    
    def check_answer(self, raw_answer):
        """Check if the provided answer matches."""
        import hashlib
        return self.answer == hashlib.sha256(raw_answer.lower().strip().encode()).hexdigest()
