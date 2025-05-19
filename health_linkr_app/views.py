from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import login, authenticate, update_session_auth_hash
from django.contrib.auth.forms import AuthenticationForm
from django.urls import reverse_lazy
from django.views.generic.edit import UpdateView
from .models import (
    Clinic, Service, ScheduleSlot, Appointment, DoctorProfile, 
    PatientProfile, User, SessionLog
)
from .forms import (
    AppointmentForm, CustomUserCreationForm, PatientProfileForm,
    UserProfileUpdateForm, PasswordChangeCustomForm
)

def home(request):
  clinics = Clinic.objects.all()
  services = Service.objects.all()
  return render(request, 'home.html', {'clinics': clinics, 'services': services})

def clinic_detail(request, clinic_id):
  clinic = get_object_or_404(Clinic, id=clinic_id)
  doctors = clinic.doctors.all()
  return render(request, 'clinic_detail.html', {'clinic': clinic, 'doctors': doctors})

@login_required
def book_appointment(request, doctor_id):
  doctor = get_object_or_404(DoctorProfile, id=doctor_id)
  slots = doctor.schedule_slots.filter(is_booked=False)
  if request.method == 'POST':
    form = AppointmentForm(request.POST)
    if form.is_valid():
      appt = form.save(commit=False)
      appt.patient = request.user.patient_profile
      appt.doctor = doctor
      slot = get_object_or_404(ScheduleSlot, id=form.cleaned_data['slot'])
      appt.slot = slot
      appt.datetime = slot.start_time
      appt.save()
      slot.is_booked = True
      slot.save()
      messages.success(request, 'Appointment booked successfully.')
      return redirect('appointments')
  else:
    form = AppointmentForm()
  return render(request, 'book_appointment.html', {'form': form, 'doctor': doctor, 'slots': slots})

@login_required
def appointments(request):
  patient = request.user.patient_profile
  appts = Appointment.objects.filter(patient=patient)
  return render(request, 'appointments.html', {'appointments': appts})

def signup(request):
    if request.method == 'POST':
        user_form = CustomUserCreationForm(request.POST)
        profile_form = PatientProfileForm(request.POST)
        
        if user_form.is_valid() and profile_form.is_valid():
            user = user_form.save()
            profile = profile_form.save(commit=False)
            profile.user = user
            profile.save()
            
            # Log the session
            SessionLog.objects.create(
                user=user,
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT'),
                session_id=request.session.session_key or ''
            )
            
            username = user_form.cleaned_data.get('username')
            raw_password = user_form.cleaned_data.get('password1')
            user = authenticate(username=username, password=raw_password)
            login(request, user)
            messages.success(request, 'Account created successfully!')
            return redirect('home')
    else:
        user_form = CustomUserCreationForm()
        profile_form = PatientProfileForm()
    
    return render(request, 'signup.html', {
        'user_form': user_form,
        'profile_form': profile_form
    })

@login_required
def profile(request):
    if request.method == 'POST':
        user_form = UserProfileUpdateForm(request.POST, request.FILES, instance=request.user)
        if hasattr(request.user, 'patient_profile'):
            profile_form = PatientProfileForm(request.POST, instance=request.user.patient_profile)
        else:
            profile_form = None
        
        if user_form.is_valid() and (not profile_form or profile_form.is_valid()):
            user_form.save()
            if profile_form:
                profile_form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('profile')
    else:
        user_form = UserProfileUpdateForm(instance=request.user)
        if hasattr(request.user, 'patient_profile'):
            profile_form = PatientProfileForm(instance=request.user.patient_profile)
        else:
            profile_form = None
    
    return render(request, 'profile.html', {
        'user_form': user_form,
        'profile_form': profile_form
    })

@login_required
def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeCustomForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Your password was successfully updated!')
            return redirect('profile')
    else:
        form = PasswordChangeCustomForm(request.user)
    return render(request, 'change_password.html', {'form': form})