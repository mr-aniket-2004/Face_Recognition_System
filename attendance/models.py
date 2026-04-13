from django.db import models
from django.contrib.auth.models import User
import numpy as np
import json


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
