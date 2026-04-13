from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages


def admin_required(view_func):
    """Decorator to restrict access to admin users only."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if not hasattr(request.user, 'role') or request.user.role.role != 'admin':
            messages.error(request, 'Access denied. Admin privileges required.')
            return redirect('login')
        return view_func(request, *args, **kwargs)
    return wrapper


def employee_required(view_func):
    """Decorator to restrict access to employee users only."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if not hasattr(request.user, 'role') or request.user.role.role != 'employee':
            messages.error(request, 'Access denied.')
            return redirect('login')
        return view_func(request, *args, **kwargs)
    return wrapper
