import json
import base64
import os
from datetime import datetime, timedelta
import csv
from io import BytesIO
import random
import string


from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.urls import reverse
from django.core.files.base import ContentFile
from django.db.models import Count, Q
from django.conf import settings
from django.db import IntegrityError
from django.core.mail import send_mail
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

from .models import Employee, Attendance, UserRole, UserOTP
from .forms import EmployeeForm, EmployeeEditForm, ChangePasswordForm, SetPasswordForm, ManualCheckoutForm
from .decorators import admin_required, employee_required


import logging
from django.contrib.auth import authenticate, login

logger = logging.getLogger(__name__)


# ─── AUTH ─────────────────────────────────────────────
def login_view(request):
    if request.user.is_authenticated:
        if hasattr(request.user, 'role'):
            if request.user.role.role == 'admin':
                return redirect('admin_dashboard')
            else:
                return redirect('employee_dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        role = request.POST.get('role', 'admin')
        
        user = authenticate(request, username=username, password=password)
        if user is not None:
            if hasattr(user, 'role') and user.role.role == role:
                # Generate and send OTP
                otp = UserOTP.create_otp_for_user(user, expiry_minutes=2)
                
                try:
                    send_mail(
                        'Your OTP for FaceTrack Login',
                        f'''Hello {user.get_full_name()},

Your One-Time Password (OTP) for FaceTrack login is:

{otp.otp_code}

This OTP is valid for 2 minutes only.

If you did not request this OTP, please ignore this email.

--- FaceTrack System ---''',
                        settings.EMAIL_HOST_USER,
                        [user.email],
                        fail_silently=False,
                    )
                    
                    # Store user info in session for OTP verification
                    request.session['otp_user_id'] = user.id
                    request.session['otp_role'] = role
                    request.session['otp_username'] = username
                    
                    logger.info(f"OTP sent to user: {username}")
                    messages.success(request, 'OTP sent to your email address.')
                    return redirect('verify_otp')
                    
                except Exception as e:
                    messages.error(request, f'Failed to send OTP: {str(e)}')
                    logger.error(f"Failed to send OTP to {username}: {str(e)}")
            else:
                messages.error(request, f'You do not have {role} access.')
                logger.info(f"Role mismatch for user: {username}")
        else:
            messages.error(request, 'Invalid credentials.')
            logger.warning(f"Failed login attempt for username: {username}")
    
    return render(request, 'attendance/login.html')


def verify_otp(request):
    """Verify OTP and complete login."""
    # Check if user has initiated OTP process
    otp_user_id = request.session.get('otp_user_id')
    otp_role = request.session.get('otp_role')
    otp_username = request.session.get('otp_username')
    
    if not otp_user_id:
        messages.error(request, 'Please login first.')
        return redirect('login')
    
    try:
        user = User.objects.get(id=otp_user_id)
    except User.DoesNotExist:
        messages.error(request, 'User not found.')
        return redirect('login')
    
    if request.method == 'POST':
        otp_code = request.POST.get('otp_code', '').strip()
        
        if not otp_code:
            messages.error(request, 'Please enter OTP.')
            return render(request, 'attendance/otp_verify.html', {
                'user': user,
                'username': otp_username,
                'role': otp_role
            })
        
        # Verify OTP
        try:
            otp_obj = UserOTP.objects.get(user=user, otp_code=otp_code)
            
            if not otp_obj.is_valid():
                messages.error(request, 'OTP has expired or already used. Please login again.')
                # Clear session
                del request.session['otp_user_id']
                del request.session['otp_role']
                del request.session['otp_username']
                return redirect('login')
            
            # Mark OTP as used
            otp_obj.mark_as_used()
            
            # Complete login
            login(request, user)
            
            # Clear session
            del request.session['otp_user_id']
            del request.session['otp_role']
            del request.session['otp_username']
            
            logger.info(f"Successful login with OTP for user: {user.username}")
            messages.success(request, f'Welcome {user.get_full_name()}!')
            
            if otp_role == 'admin':
                return redirect('admin_dashboard')
            else:
                return redirect('employee_dashboard')
        
        except UserOTP.DoesNotExist:
            messages.error(request, 'Invalid OTP. Please try again.')
            logger.warning(f"Invalid OTP attempt for user: {user.username}")
    
    return render(request, 'attendance/otp_verify.html', {
        'user': user,
        'username': otp_username,
        'role': otp_role
    })


def resend_otp(request):
    """Resend OTP to user's email."""
    otp_user_id = request.session.get('otp_user_id')
    
    if not otp_user_id:
        messages.error(request, 'Please login first.')
        return redirect('login')
    
    try:
        user = User.objects.get(id=otp_user_id)
        
        # Generate and send new OTP
        otp = UserOTP.create_otp_for_user(user, expiry_minutes=2)
        
        send_mail(
            'Your OTP for FaceTrack Login',
            f'''Hello {user.get_full_name()},

Your One-Time Password (OTP) for FaceTrack login is:

{otp.otp_code}

This OTP is valid for 2 minutes only.

If you did not request this OTP, please ignore this email.

--- FaceTrack System ---''',
            settings.EMAIL_HOST_USER,
            [user.email],
            fail_silently=False,
        )
        
        messages.success(request, 'New OTP sent to your email.')
        logger.info(f"OTP resent to user: {user.username}")
        
    except Exception as e:
        messages.error(request, f'Failed to resend OTP: {str(e)}')
        logger.error(f"Failed to resend OTP: {str(e)}")
    
    return redirect('verify_otp')


def build_password_reset_link(request, user):
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    return request.build_absolute_uri(reverse('set_password', kwargs={'uidb64': uid, 'token': token}))


def send_password_setup_email(user, request):
    otp = UserOTP.create_otp_for_user(user, expiry_minutes=5)
    reset_link = build_password_reset_link(request, user)
    send_mail(
        'FaceTrack Password Setup',
        f'''Hello {user.get_full_name() },

A request was made to set your FaceTrack password.

Please use the link below and enter the OTP from this email when prompted.

Username: {user.username}

Set Password Link:
{reset_link}

One-Time Password (OTP): {otp.otp_code}

This OTP is valid for 5 minutes.

If you did not request this, please ignore this email.

--- FaceTrack System ---''',
        settings.EMAIL_HOST_USER,
        [user.email],
        fail_silently=False,
    )
    return otp


def set_password(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is None or not default_token_generator.check_token(user, token):
        messages.error(request, 'Password reset link is invalid or expired.')
        return redirect('forgot_password')

    form = SetPasswordForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        otp_code = form.cleaned_data['otp_code'].strip()
        try:
            otp_obj = UserOTP.objects.get(user=user, otp_code=otp_code)
        except UserOTP.DoesNotExist:
            messages.error(request, 'Invalid OTP. Please try again.')
            return render(request, 'attendance/set_password.html', {'form': form})

        if not otp_obj.is_valid():
            messages.error(request, 'OTP has expired or already been used. Request a new password link.')
            return redirect('forgot_password')

        user.set_password(form.cleaned_data['new_password'])
        user.save()
        otp_obj.mark_as_used()

        login(request, user)
        messages.success(request, 'Your password has been set successfully.')

        if hasattr(user, 'role') and user.role.role == 'admin':
            return redirect('admin_dashboard')
        return redirect('employee_dashboard')

    return render(request, 'attendance/set_password.html', {'form': form})


def forgot_password(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        if not email:
            messages.error(request, 'Please enter your email address.')
            return redirect('forgot_password')

        try:
            user = User.objects.get(email__iexact=email)
            # Check if user has employee role
            if not hasattr(user, 'role') or user.role.role != 'employee':
                messages.error(request, 'This email is not associated with an employee account.')
                return redirect('forgot_password')

            try:
                send_password_setup_email(user, request)
                messages.success(request, 'Password reset link sent to your email address.')
            except Exception as mail_error:
                messages.error(request, f'Unable to send password reset email: {mail_error}')

        except User.DoesNotExist:
            messages.error(request, 'No account found with this email address.')
            return redirect('forgot_password')

    return render(request, 'attendance/forgot_password.html')


def logout_view(request):
    logout(request)
    return redirect('login')


# ─── ADMIN DASHBOARD ─────────────────────────────────
@login_required
@admin_required
def admin_dashboard(request):
    today = timezone.localdate()
    total_employees = Employee.objects.filter(is_active=True).count()
    present_today = Attendance.objects.filter(date=today).count()
    absent_today = total_employees - present_today
    
    # Recent attendance
    recent_attendance = Attendance.objects.select_related('employee__user').order_by('-date', '-check_in_time')[:5]
    
    # Monthly stats
    month_start = today.replace(day=1)
    monthly_attendance = Attendance.objects.filter(date__gte=month_start).count()
    
    # Employees list
    employees = Employee.objects.filter(is_active=True).select_related('user').order_by('-date_joined')[:5]
    
    # Attendance rate
    if total_employees > 0:
        attendance_rate = round((present_today / total_employees) * 100)
    else:
        attendance_rate = 0
    
    context = {
        'total_employees': total_employees,
        'present_today': present_today,
        'absent_today': absent_today,
        'attendance_rate': attendance_rate,
        'recent_attendance': recent_attendance,
        'monthly_attendance': monthly_attendance,
        'employees': employees,
        'today': today,
    }
    return render(request, 'attendance/admin_dashboard.html', context)


# ─── ADD EMPLOYEE ─────────────────────────────────────
@login_required
@admin_required
def add_employee(request):
    if request.method == 'POST':
        form = EmployeeForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                # Create user with unusable password and send setup link
                user = User.objects.create_user(
                    username=form.cleaned_data['username'],
                    email=form.cleaned_data['email'],
                    password=None,
                    first_name=form.cleaned_data['first_name'],
                    last_name=form.cleaned_data['last_name'],
                )
                UserRole.objects.create(user=user, role='employee')

                # Save employee instance
                employee = form.save(commit=False)
                employee.user = user
                try:
                    send_password_setup_email(user, request)
                    messages.success(request, f'Employee account created with username "{user.username}" and password setup email sent.')
                except Exception as mail_error:
                    messages.warning(request, f'Account created with username "{user.username}", but password setup email could not be sent: {mail_error}')

                captured_photo = form.cleaned_data.get('captured_photo')

                #  Handle webcam captured photo
                if captured_photo and not request.FILES.get('photo'):
                    import base64, io
                    from PIL import Image
                    from django.core.files.base import ContentFile
                    from .face_utils import encode_face_from_image

                    format, imgstr = captured_photo.split(';base64,')
                    ext = format.split('/')[-1]
                    image_data = base64.b64decode(imgstr)

                    image = Image.open(io.BytesIO(image_data)).convert("RGB")
                    image = image.resize((800, 800))

                    buffer = io.BytesIO()
                    image.save(buffer, format="JPEG", quality=90)

                    employee.photo = ContentFile(buffer.getvalue(), name=f"{form.cleaned_data['employee_id']}.jpg")
                    employee.save()
                    employee.refresh_from_db()

                    # Encode face safely
                    encoding = encode_face_from_image(employee.photo.path)
                    if encoding is not None and len(encoding) > 0:
                        import json
                        employee.face_encoding = json.dumps(encoding.tolist())
                        employee.save()
                        messages.success(request, f'Employee "{user.username}" added & face encoded!')
                    else:
                        employee.face_encoding = None
                        employee.save()
                        messages.error(request, 'No face detected! Use a clear front-face image.')

                #  Handle uploaded photo
                elif 'photo' in request.FILES:
                    employee.photo = request.FILES['photo']
                    employee.save()
                    employee.refresh_from_db()

                    from .face_utils import encode_face_from_image
                    encoding = encode_face_from_image(employee.photo.path)
                    if encoding is not None and len(encoding) > 0:
                        import json
                        employee.face_encoding = json.dumps(encoding.tolist())
                        employee.save()
                        messages.success(request, f'Employee "{user.username}" added & face encoded!')
                    else:
                        employee.face_encoding = None
                        employee.save()
                        messages.error(request, 'No face detected! Use a clear front-face image.')

                #  No photo
                else:
                    employee.save()
                    messages.success(request, f'Employee "{user.username}" ({employee.employee_id}) added. Please add a photo.')

                return redirect('admin_dashboard')
            except IntegrityError:
                if 'user' in locals():
                    try:
                        user.delete()
                    except Exception:
                        pass
                form.add_error(None, 'A database error occurred while creating the employee. Please try again.')
            except Exception as e:
                if 'user' in locals():
                    try:
                        user.delete()
                    except Exception:
                        pass
                messages.error(request, 'Unable to add employee. Please check all fields and try again.')
                form.add_error(None, 'Unexpected error: ' + str(e))
    else:
        form = EmployeeForm()
    return render(request, 'attendance/add_employee.html', {'form': form})



# ─── EDIT EMPLOYEE ────────────────────────────────────
@login_required
@admin_required
def edit_employee(request, employee_id):
    employee = get_object_or_404(Employee, employee_id=employee_id)

    if request.method == 'POST':
        form = EmployeeEditForm(request.POST, request.FILES, instance=employee)

        if form.is_valid():
            # Update employee fields
            employee = form.save(commit=False)
            employee.user.first_name = form.cleaned_data['first_name']
            employee.user.last_name = form.cleaned_data['last_name']
            employee.user.email = form.cleaned_data['email']
            employee.user.save()

            captured_photo = request.POST.get('captured_photo')
    


            #  Handle webcam capture
            if captured_photo:
                import base64, io
                from PIL import Image
                from django.core.files.base import ContentFile
                from .face_utils import encode_face_from_image

                format, imgstr = captured_photo.split(';base64,')
                image_data = base64.b64decode(imgstr)

                image = Image.open(io.BytesIO(image_data)).convert("RGB")
                image = image.resize((800, 800))  # optional

                buffer = io.BytesIO()
                image.save(buffer, format="JPEG", quality=90)

                employee.photo = ContentFile(buffer.getvalue(), name=f"{employee.employee_id}.jpg")
                employee.save()
                employee.refresh_from_db()
            

                # Encode face safely

                encoding = encode_face_from_image(employee.photo.path)

                if encoding is not None and len(encoding) > 0:
                    print("this is view encoding ",encoding)
                    import json
                    employee.face_encoding = json.dumps(encoding.tolist())
                    employee.save()
                    messages.success(request, 'Employee updated & face re-encoded!')
                else:
                    # print('No face detected! Use a clear front-face image.')
                    employee.face_encoding = None
                    employee.save()
                    messages.error(request, 'No face detected! Use a clear front-face image.')

            #  Handle file upload
            elif 'photo' in request.FILES:
                employee.photo = request.FILES['photo']
                employee.save()
                employee.refresh_from_db()
                print(employee.photo)
                # print(employee.photo.path)

                from .face_utils import encode_face_from_image
                encoding = encode_face_from_image(employee.photo.path)
                if encoding is not None and len(encoding) > 0:
                    print("this is view encoding ",encoding)
                    import json
                    employee.face_encoding = json.dumps(encoding.tolist())
                    employee.save()
                    messages.success(request, 'Employee updated & face re-encoded!')
                else:
                    # print('No face detected! Use a clear front-face image.')
                    employee.face_encoding = None
                    employee.save()
                    messages.error(request, 'No face detected! Use a clear front-face image.')

            #  No photo change
            else:
                employee.save()
                messages.success(request, 'Employee updated successfully!')

            return redirect('admin_dashboard')

    else:
        form = EmployeeEditForm(instance=employee, initial={
            'first_name': employee.user.first_name,
            'last_name': employee.user.last_name,
            'email': employee.user.email,
        })

    return render(request, 'attendance/edit_employee.html', {'form': form, 'employee': employee})


@login_required
@admin_required
def delete_employee(request, employee_id):
    employee = get_object_or_404(Employee, employee_id=employee_id)
    if request.method == 'POST':
        user = employee.user
        employee.delete()
        user.delete()
        messages.success(request, 'Employee deleted successfully.')
    return redirect('admin_dashboard')


# ─── EMPLOYEE LIST ────────────────────────────────────
@login_required
@admin_required
@login_required
@admin_required
def employee_list(request):
    employees_queryset = Employee.objects.filter(is_active=True).select_related('user').order_by('-date_joined')
    
    paginator = Paginator(employees_queryset, 25)  # 25 employees per page
    page = request.GET.get('page')
    
    try:
        employees = paginator.page(page)
    except PageNotAnInteger:
        employees = paginator.page(1)
    except EmptyPage:
        employees = paginator.page(paginator.num_pages)
    
    return render(request, 'attendance/employee_list.html', {'employees': employees})


@login_required
@admin_required
def export_employee_csv(request):
    """Export employee details to CSV format."""
    employees = Employee.objects.filter(is_active=True).select_related('user')
    
    # Create CSV response
    response = HttpResponse(content_type='text/csv')
    filename = f"employee_details_{timezone.now().strftime('%Y%m%d_%H%M%S')}.csv"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    writer = csv.writer(response)
    writer.writerow(['Employee Name', 'Employee ID', 'Department', 'Designation', 'Phone', 'Email', 'Date Joined', 'Face Encoded'])
    
    for emp in employees:
        writer.writerow([
            emp.user.get_full_name(),
            emp.employee_id,
            emp.get_department_display(),
            emp.designation or '',
            emp.phone or '',
            emp.user.email,
            emp.date_joined.strftime('%Y-%m-%d'),
            'Yes' if emp.face_encoding else 'No'
        ])
    
    return response


@login_required
@admin_required
def export_employee_pdf(request):
    """Export employee details to PDF format."""
    employees = Employee.objects.filter(is_active=True).select_related('user')
    
    # Create PDF response
    response = HttpResponse(content_type='application/pdf')
    filename = f"employee_details_{timezone.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    # Create PDF document
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        leftMargin=18,
        rightMargin=18,
        topMargin=18,
        bottomMargin=18,
    )
    elements = []
    
    # Styles
    styles = getSampleStyleSheet()
    title_style = styles['Heading1']
    title_style.alignment = 1  # Center alignment
    
    # Title
    title = Paragraph("Employee Details Report", title_style)
    elements.append(title)
    elements.append(Spacer(1, 12))
    
    # Table data
    data = [['Employee Name', 'ID', 'Department', 'Designation', 'Phone', 'Email', 'Date Joined', 'Face Encoded']]
    
    for emp in employees:
        data.append([
            emp.user.get_full_name(),
            emp.employee_id,
            emp.get_department_display(),
            emp.designation or '-',
            emp.phone or '-',
            emp.user.email,
            emp.date_joined.strftime('%Y-%m-%d'),
            'Yes' if emp.face_encoding else 'No'
        ])
    
    # Create table
    col_widths = [140, 60, 80, 120, 90, 170, 70, 60]
    table = Table(data, colWidths=col_widths, repeatRows=1)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('ALIGN', (0, 1), (0, -1), 'LEFT'),
        ('ALIGN', (3, 1), (-2, -1), 'CENTER'),
        ('ALIGN', (-1, 1), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    elements.append(table)
    
    # Build PDF
    doc.build(elements)
    pdf = buffer.getvalue()
    buffer.close()
    response.write(pdf)
    
    return response


# ─── ATTENDANCE RECORDS ───────────────────────────────
@login_required
@admin_required
def attendance_records(request):
    date_filter = request.GET.get('date', '')
    dept_filter = request.GET.get('department', '')
    
    records_queryset = Attendance.objects.select_related('employee__user').order_by('-date', '-check_in_time')
    
    if date_filter:
        records_queryset = records_queryset.filter(date=date_filter)
    if dept_filter:
        records_queryset = records_queryset.filter(employee__department=dept_filter)
    
    # Calculate hours worked for each record
    records_list = list(records_queryset)
    for record in records_list:
        if record.check_in_time and record.check_out_time:
            check_in_datetime = timezone.datetime.combine(record.date, record.check_in_time)
            check_out_datetime = timezone.datetime.combine(record.date, record.check_out_time)
            
            # Handle case where checkout is next day (overnight work)
            if check_out_datetime < check_in_datetime:
                check_out_datetime += timezone.timedelta(days=1)
            
            record.hours_worked = (check_out_datetime - check_in_datetime).total_seconds() / 3600
        else:
            record.hours_worked = None
    
    paginator = Paginator(records_list, 25)  # 25 records per page
    page = request.GET.get('page')
    
    try:
        records = paginator.page(page)
    except PageNotAnInteger:
        records = paginator.page(1)
    except EmptyPage:
        records = paginator.page(paginator.num_pages)
    
    return render(request, 'attendance/attendance_records.html', {
        'records': records,
        'date_filter': date_filter,
        'dept_filter': dept_filter,
        'departments': Employee.DEPARTMENT_CHOICES,
    })


@login_required
@admin_required
def export_attendance_csv(request):
    """Export attendance records to CSV format."""
    date_filter = request.GET.get('date', '')
    dept_filter = request.GET.get('department', '')
    
    records = Attendance.objects.select_related('employee__user').all()
    
    if date_filter:
        records = records.filter(date=date_filter)
    if dept_filter:
        records = records.filter(employee__department=dept_filter)
    
    # Calculate hours worked for each record
    records_list = list(records)
    for record in records_list:
        if record.check_in_time and record.check_out_time:
            check_in_datetime = timezone.datetime.combine(record.date, record.check_in_time)
            check_out_datetime = timezone.datetime.combine(record.date, record.check_out_time)
            
            # Handle case where checkout is next day (overnight work)
            if check_out_datetime < check_in_datetime:
                check_out_datetime += timezone.timedelta(days=1)
            
            record.hours_worked = (check_out_datetime - check_in_datetime).total_seconds() / 3600
        else:
            record.hours_worked = None
    
    # Create CSV response
    response = HttpResponse(content_type='text/csv')
    filename = f"attendance_records_{timezone.now().strftime('%Y%m%d_%H%M%S')}.csv"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    writer = csv.writer(response)
    writer.writerow(['Employee Name', 'Employee ID', 'Department', 'Date', 'Check In Time', 'Check Out Time', 'Hours Worked', 'Status', 'Marked By'])
    
    for record in records_list:
        writer.writerow([
            record.employee.user.get_full_name(),
            record.employee.employee_id,
            record.employee.get_department_display(),
            record.date.strftime('%Y-%m-%d'),
            record.check_in_time.strftime('%H:%M:%S') if record.check_in_time else '',
            record.check_out_time.strftime('%H:%M:%S') if record.check_out_time else '',
            f"{record.hours_worked:.2f}" if record.hours_worked else '',
            record.get_status_display(),
            record.marked_by
        ])
    
    return response


@login_required
@admin_required
def export_attendance_pdf(request):
    """Export attendance records to PDF format."""
    date_filter = request.GET.get('date', '')
    dept_filter = request.GET.get('department', '')
    
    records = Attendance.objects.select_related('employee__user').all()
    
    if date_filter:
        records = records.filter(date=date_filter)
    if dept_filter:
        records = records.filter(employee__department=dept_filter)
    
    # Calculate hours worked for each record
    records_list = list(records)
    for record in records_list:
        if record.check_in_time and record.check_out_time:
            check_in_datetime = timezone.datetime.combine(record.date, record.check_in_time)
            check_out_datetime = timezone.datetime.combine(record.date, record.check_out_time)
            
            # Handle case where checkout is next day (overnight work)
            if check_out_datetime < check_in_datetime:
                check_out_datetime += timezone.timedelta(days=1)
            
            record.hours_worked = (check_out_datetime - check_in_datetime).total_seconds() / 3600
        else:
            record.hours_worked = None
    
    # Create PDF response
    response = HttpResponse(content_type='application/pdf')
    filename = f"attendance_records_{timezone.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    # Create PDF document
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        leftMargin=18,
        rightMargin=18,
        topMargin=18,
        bottomMargin=18,
    )
    elements = []
    
    # Styles
    styles = getSampleStyleSheet()
    title_style = styles['Heading1']
    title_style.alignment = 1  # Center alignment
    
    # Title
    title = Paragraph("Attendance Records Report", title_style)
    elements.append(title)
    elements.append(Spacer(1, 12))
    
    # Filters info
    filter_info = []
    if date_filter:
        filter_info.append(f"Date: {date_filter}")
    if dept_filter:
        dept_name = dict(Employee.DEPARTMENT_CHOICES).get(dept_filter, dept_filter)
        filter_info.append(f"Department: {dept_name}")
    
    if filter_info:
        filter_text = "Filters: " + ", ".join(filter_info)
        filter_para = Paragraph(filter_text, styles['Normal'])
        elements.append(filter_para)
        elements.append(Spacer(1, 12))
    
    # Table data
    data = [['Employee Name', 'ID', 'Department', 'Date', 'Check In', 'Check Out', 'Hours', 'Status', 'Marked By']]
    
    for record in records_list:
        data.append([
            record.employee.user.get_full_name(),
            record.employee.employee_id,
            record.employee.get_department_display(),
            record.date.strftime('%Y-%m-%d'),
            record.check_in_time.strftime('%H:%M:%S') if record.check_in_time else '-',
            record.check_out_time.strftime('%H:%M:%S') if record.check_out_time else '-',
            f"{record.hours_worked:.2f}h" if record.hours_worked else '-',
            record.get_status_display(),
            record.marked_by
        ])
    
    # Create table
    col_widths = [120, 60, 70, 65, 60, 60, 50, 70, 80]
    table = Table(data, colWidths=col_widths, repeatRows=1)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('ALIGN', (0, 1), (0, -1), 'LEFT'),
        ('ALIGN', (3, 1), (-2, -1), 'CENTER'),
        ('ALIGN', (-1, 1), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    elements.append(table)
    
    # Build PDF
    doc.build(elements)
    pdf = buffer.getvalue()
    buffer.close()
    response.write(pdf)
    
    return response


# ─── START FACE RECOGNITION (via management command) ──
@login_required
@admin_required
def start_recognition(request):
    """Start face recognition - runs OpenCV window on server."""
    if request.method == 'POST':
        try:
            from .face_utils import run_face_recognition_camera
            import threading
            thread = threading.Thread(target=run_face_recognition_camera, daemon=True)
            thread.start()
            messages.success(request, 'Face recognition camera started! Check the OpenCV window on the server.')
        except ImportError:
            messages.error(request, 'Face recognition libraries not installed. Please install opencv-python and face_recognition.')
        except Exception as e:
            messages.error(request, f'Error starting camera: {str(e)}')
    
    return redirect('admin_dashboard')


# ─── WEBCAM ATTENDANCE (Browser-based) ────────────────
@login_required
@admin_required
def live_monitor(request):
    """Live monitoring page with browser webcam."""
    today = timezone.localdate()
    today_records = Attendance.objects.filter(date=today).select_related('employee__user').order_by('-check_in_time')
    total_employees = Employee.objects.filter(is_active=True).count()
    
    return render(request, 'attendance/live_monitor.html', {
        'today_records': today_records,
        'total_employees': total_employees,
        'present_count': today_records.count(),
    })


@csrf_exempt
@login_required
def process_frame(request):
    """API endpoint: receives a webcam frame, returns recognized faces."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    
    try:
        import cv2
        import numpy as np
        from .face_utils import get_all_employee_encodings, recognize_faces_in_frame
        
        data = json.loads(request.body)
        image_data = data.get('image', '')
        
        if not image_data:
            return JsonResponse({'error': 'No image data'}, status=400)
        
        # Decode base64 image
        header, encoded = image_data.split(',', 1)
        img_bytes = base64.b64decode(encoded)
        nparr = np.frombuffer(img_bytes, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if frame is None:
            return JsonResponse({'error': 'Invalid image'}, status=400)
        
        known = get_all_employee_encodings()
        results = recognize_faces_in_frame(frame, known)
        
        today = timezone.localdate()
        response_results = []
        
        for r in results:
            result_data = {
                'name': r['name'],
                'employee_id': r['employee_id'],
                'is_known': r['is_known'],
                'location': r['location'],
                'already_marked': False,
                'just_marked': False,
            }
            
            if r['is_known'] and r['employee']:
                # Check if already marked today
                exists = Attendance.objects.filter(employee=r['employee'], date=today).exists()
                if exists:
                    result_data['already_marked'] = True
                else:
                    # Mark attendance
                    now = timezone.localtime()
                    Attendance.objects.create(
                        employee=r['employee'],
                        date=today,
                        check_in_time=now.time(),
                        status='present' if now.hour < 10 else 'late',
                        marked_by='face_recognition'
                    )
                    result_data['just_marked'] = True
            
            response_results.append(result_data)
        
        return JsonResponse({'faces': response_results})
    
    except ImportError:
        return JsonResponse({'error': 'Face recognition libraries not installed'}, status=500)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# ─── EMPLOYEE DASHBOARD ──────────────────────────────
@login_required
@employee_required
def employee_dashboard(request):
    employee = request.user.employee
    today = timezone.localdate()
    
    # This month's attendance
    month_start = today.replace(day=1)
    monthly_records = Attendance.objects.filter(
        employee=employee, date__gte=month_start
    ).order_by('-date')
    
    # Calculate hours worked for each record
    for record in monthly_records:
        if record.check_in_time and record.check_out_time:
            check_in_datetime = timezone.datetime.combine(record.date, record.check_in_time)
            check_out_datetime = timezone.datetime.combine(record.date, record.check_out_time)
            
            # Handle case where checkout is next day (overnight work)
            if check_out_datetime < check_in_datetime:
                check_out_datetime += timezone.timedelta(days=1)
            
            record.hours_worked = (check_out_datetime - check_in_datetime).total_seconds() / 3600
        else:
            record.hours_worked = None
    
    # Stats
    total_working_days = 0
    d = month_start
    while d <= today:
        if d.weekday() < 5:  # Mon-Fri
            total_working_days += 1
        d += timedelta(days=1)
    
    present_days = monthly_records.count()
    absent_days = total_working_days - present_days
    if total_working_days > 0:
        attendance_pct = round((present_days / total_working_days) * 100)
    else:
        attendance_pct = 0
    
    # Today's status
    today_record = Attendance.objects.filter(employee=employee, date=today).first()
    show_manual_checkout = False
    hours_elapsed = 0
    
    if today_record and today_record.check_in_time and not today_record.check_out_time:
        check_in_datetime = timezone.datetime.combine(today, today_record.check_in_time)
        check_in_datetime = timezone.make_aware(check_in_datetime)
        now = timezone.now()
        hours_elapsed = (now - check_in_datetime).total_seconds() / 3600
        
        # Show manual checkout option if hours exceed 8
        if hours_elapsed > 8:
            show_manual_checkout = True
        
        today_record.hours_worked = None
    elif today_record and today_record.check_in_time and today_record.check_out_time:
        check_in_datetime = timezone.datetime.combine(today, today_record.check_in_time)
        check_out_datetime = timezone.datetime.combine(today, today_record.check_out_time)
        
        # Handle case where checkout is next day (overnight work)
        if check_out_datetime < check_in_datetime:
            check_out_datetime += timezone.timedelta(days=1)
        
        today_record.hours_worked = (check_out_datetime - check_in_datetime).total_seconds() / 3600
    
    # All records with hours calculation
    all_records = Attendance.objects.filter(employee=employee).order_by('-date')[:50]
    for record in all_records:
        if record.check_in_time and record.check_out_time:
            check_in_datetime = timezone.datetime.combine(record.date, record.check_in_time)
            check_out_datetime = timezone.datetime.combine(record.date, record.check_out_time)
            
            # Handle case where checkout is next day (overnight work)
            if check_out_datetime < check_in_datetime:
                check_out_datetime += timezone.timedelta(days=1)
            
            record.hours_worked = (check_out_datetime - check_in_datetime).total_seconds() / 3600
        else:
            record.hours_worked = None
    
    # Late count
    late_count = monthly_records.filter(status='late').count()
    
    context = {
        'employee': employee,
        'today_record': today_record,
        'monthly_records': monthly_records,
        'all_records': all_records,
        'present_days': present_days,
        'absent_days': absent_days,
        'late_count': late_count,
        'total_working_days': total_working_days,
        'attendance_pct': attendance_pct,
        'today': today,
        'show_manual_checkout': show_manual_checkout,
        'hours_elapsed': hours_elapsed,
    }
    return render(request, 'attendance/employee_dashboard.html', context)


# ─── EMPLOYEE PROFILE ────────────────────────────────
@login_required
@employee_required
def employee_profile(request):
    employee = request.user.employee
    return render(request, 'attendance/employee_profile.html', {'employee': employee})


# ─── CHANGE PASSWORD ──────────────────────────────────
@login_required
def change_password(request):
    if request.method == 'POST':
        form = ChangePasswordForm(request.POST)
        if form.is_valid():
            if request.user.check_password(form.cleaned_data['current_password']):
                request.user.set_password(form.cleaned_data['new_password'])
                request.user.save()
                messages.success(request, 'Password changed successfully. Please login again.')
                return redirect('login')
            else:
                messages.error(request, 'Current password is incorrect.')
    else:
        form = ChangePasswordForm()
    
    return render(request, 'attendance/change_password.html', {'form': form})


# ─── EMPLOYEE CHECKOUT ────────────────────────────────
@login_required
@employee_required
def employee_checkout(request):
    employee = request.user.employee
    today = timezone.localdate()
    
    # Get today's attendance record
    today_record = Attendance.objects.filter(employee=employee, date=today).first()
    
    if not today_record:
        messages.error(request, 'You have not checked in today.')
        return redirect('employee_dashboard')
    
    if today_record.check_out_time:
        messages.warning(request, 'You have already checked out today.')
        return redirect('employee_dashboard')
    
    # Set checkout time
    now = timezone.localtime()
    today_record.check_out_time = now.time()
    today_record.save()
    
    # Calculate hours worked
    check_in_datetime = timezone.datetime.combine(today, today_record.check_in_time)
    check_out_datetime = timezone.datetime.combine(today, today_record.check_out_time)
    
    # Handle case where checkout is next day (overnight work)
    if check_out_datetime < check_in_datetime:
        check_out_datetime += timezone.timedelta(days=1)
    
    hours_worked = (check_out_datetime - check_in_datetime).total_seconds() / 3600
    
    messages.success(request, f'Checked out successfully at {now.time().strftime("%I:%M %p")}. Hours worked today: {hours_worked:.2f}')
    return redirect('employee_dashboard')


# ─── MANUAL CHECKOUT ────────────────────────────────
@login_required
@employee_required
def manual_checkout(request):
    employee = request.user.employee
    today = timezone.localdate()
    
    # Get today's attendance record
    today_record = Attendance.objects.filter(employee=employee, date=today).first()
    
    if not today_record:
        messages.error(request, 'You have not checked in today.')
        return redirect('employee_dashboard')
    
    if today_record.check_out_time:
        messages.warning(request, 'You have already checked out today.')
        return redirect('employee_dashboard')
    
    # Check if hours worked exceed 8 hours
    check_in_datetime = timezone.datetime.combine(today, today_record.check_in_time)
    check_in_datetime = timezone.make_aware(check_in_datetime)
    now = timezone.now()
    hours_elapsed = (now - check_in_datetime).total_seconds() / 3600
    
    if hours_elapsed <= 8:
        messages.warning(request, f'You can only set manual checkout after 8 hours. Current hours: {hours_elapsed:.2f}')
        return redirect('employee_dashboard')
    
    if request.method == 'POST':
        # Create check_in_datetime for form validation
        check_in_datetime = timezone.datetime.combine(today, today_record.check_in_time)
        check_in_datetime = timezone.make_aware(check_in_datetime)
        
        form = ManualCheckoutForm(request.POST, check_in_datetime=check_in_datetime)
        if form.is_valid():
            checkout_time = form.cleaned_data['checkout_time']
            checkout_date = form.cleaned_data['checkout_date']
            
            # Set checkout time
            today_record.check_out_time = checkout_time
            today_record.save()
            
            # Calculate hours worked
            check_out_datetime = timezone.datetime.combine(checkout_date, checkout_time)
            check_out_datetime = timezone.make_aware(check_out_datetime)
            
            # Handle case where checkout is next day (overnight work)
            if check_out_datetime < check_in_datetime:
                check_out_datetime += timezone.timedelta(days=1)
            
            hours_worked = (check_out_datetime - check_in_datetime).total_seconds() / 3600
            
            messages.success(request, f'Manual checkout set successfully. Hours worked: {hours_worked:.2f}')
            return redirect('employee_dashboard')
    else:
        # Pre-populate with current time and today as default
        initial_data = {
            'checkout_date': today,
            'checkout_time': now.time()
        }
        check_in_datetime = timezone.datetime.combine(today, today_record.check_in_time)
        check_in_datetime = timezone.make_aware(check_in_datetime)
        form = ManualCheckoutForm(initial=initial_data, check_in_datetime=check_in_datetime)
    
    context = {
        'form': form,
        'today_record': today_record,
        'hours_elapsed': hours_elapsed,
        'employee': employee,
    }
    return render(request, 'attendance/manual_checkout.html', context)
