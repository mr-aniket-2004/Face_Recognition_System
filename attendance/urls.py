from django.urls import path
from . import views

urlpatterns = [
    path('', views.login_view, name='home'),
    path('login/', views.login_view, name='login'),
    path('verify-otp/', views.verify_otp, name='verify_otp'),
    path('resend-otp/', views.resend_otp, name='resend_otp'),
    path('forgot-password/', views.forgot_password, name='forgot_password'),
    path('set-password/<uidb64>/<token>/', views.set_password, name='set_password'),
    path('logout/', views.logout_view, name='logout'),
    
    # Admin
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('add-employee/', views.add_employee, name='add_employee'),
    path('edit-employee/<str:employee_id>/', views.edit_employee, name='edit_employee'),
    path('delete-employee/<str:employee_id>/', views.delete_employee, name='delete_employee'),
    path('employees/', views.employee_list, name='employee_list'),
    path('export-employee-csv/', views.export_employee_csv, name='export_employee_csv'),
    path('export-employee-pdf/', views.export_employee_pdf, name='export_employee_pdf'),
    path('attendance-records/', views.attendance_records, name='attendance_records'),
    path('export-attendance-csv/', views.export_attendance_csv, name='export_attendance_csv'),
    path('export-attendance-pdf/', views.export_attendance_pdf, name='export_attendance_pdf'),
    path('start-recognition/', views.start_recognition, name='start_recognition'),
    path('live-monitor/', views.live_monitor, name='live_monitor'),
    path('api/process-frame/', views.process_frame, name='process_frame'),
    
    # Employee
    path('employee-dashboard/', views.employee_dashboard, name='employee_dashboard'),
    path('employee-profile/', views.employee_profile, name='employee_profile'),
    path('change-password/', views.change_password, name='change_password'),
    path('employee-checkout/', views.employee_checkout, name='employee_checkout'),
    path('manual-checkout/', views.manual_checkout, name='manual_checkout'),
]
