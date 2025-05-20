from django.contrib.auth.decorators import user_passes_test

def is_admin(user):
    """Check if user is an active admin (staff or superuser)"""
    return user.is_active and (user.is_staff or user.is_superuser)

def is_patient(user):
    """Check if user is an active patient (not staff/superuser)"""
    return user.is_active and not (user.is_staff or user.is_superuser)

def is_doctor(user):
    """Check if user is an active doctor"""
    return user.is_active and hasattr(user, 'doctor_profile') and user.doctor_profile is not None

def admin_required(function=None):
    """Decorator for views that checks that the user is an admin"""
    actual_decorator = user_passes_test(
        lambda u: is_admin(u),
        login_url='home'  # Redirect to home if not admin
    )
    if function:
        return actual_decorator(function)
    return actual_decorator

def patient_required(function=None):
    """Decorator for views that checks that the user is a patient"""
    actual_decorator = user_passes_test(
        lambda u: is_patient(u),
        login_url='admin:index'  # Redirect to admin if not patient
    )
    if function:
        return actual_decorator(function)
    return actual_decorator

def doctor_required(function=None):
    """Decorator for views that checks that the user is a doctor"""
    actual_decorator = user_passes_test(
        lambda u: is_doctor(u),
        login_url='home'  # Redirect to home if not a doctor
    )
    if function:
        return actual_decorator(function)
    return actual_decorator
