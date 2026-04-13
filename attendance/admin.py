from django.contrib import admin
from .models import Employee, Attendance, UserRole

@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ('employee_id', 'user', 'department', 'designation', 'is_active')
    list_filter = ('department', 'is_active')
    search_fields = ('employee_id', 'user__first_name', 'user__last_name')

@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ('employee', 'date', 'check_in_time', 'check_out_time', 'status')
    list_filter = ('date', 'status')
    search_fields = ('employee__employee_id',)

@admin.register(UserRole)
class UserRoleAdmin(admin.ModelAdmin):
    list_display = ('user', 'role')
    list_filter = ('role',)
