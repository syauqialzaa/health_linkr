def user_type(request):
    context = {
        'is_patient': False,
        'is_doctor': False,
    }
    
    if request.user.is_authenticated:
        context['is_patient'] = hasattr(request.user, 'patient_profile')
        context['is_doctor'] = hasattr(request.user, 'doctor_profile')
    
    return context