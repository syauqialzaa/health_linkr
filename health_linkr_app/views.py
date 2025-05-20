from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import login, authenticate, update_session_auth_hash
from django.contrib.auth.forms import AuthenticationForm
from django.urls import reverse_lazy
from django.views.generic.edit import UpdateView
from django.utils import timezone
from django.db import transaction
from .permissions import admin_required, patient_required, is_admin
from .models import (
    Clinic, Service, ScheduleSlot, Appointment, DoctorProfile, 
    PatientProfile, User, SessionLog, Notification
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
@patient_required
def appointments(request):
    # Get user's patient profile or create one if it doesn't exist
    try:
        patient = request.user.patient_profile
    except PatientProfile.DoesNotExist:
        if request.user.is_superuser or request.user.is_staff:
            # Create a patient profile for admin users
            patient = PatientProfile.objects.create(
                user=request.user,
                full_name=f"{request.user.first_name} {request.user.last_name}".strip() or request.user.username,
                birth_date=timezone.now().date(),  # Default date, can be updated later
                gender='M',  # Default gender, can be updated later
                phone=request.user.phone or ''
            )
        else:
            messages.error(request, 'Please complete your patient profile first.')
            return redirect('profile')

    # Get all appointments for the patient
    appointments = Appointment.objects.filter(patient=patient).order_by('-datetime')
    
    # Get available clinics and their services
    clinics = Clinic.objects.filter(is_active=True).prefetch_related(
        'doctors',
        'services'
    )

    return render(request, 'appointments.html', {
        'appointments': appointments,
        'clinics': clinics,
        'now': timezone.now(),
        'pending_appointments': appointments.filter(status='PENDING'),
        'confirmed_appointments': appointments.filter(status='CONFIRMED'),
        'completed_appointments': appointments.filter(status='COMPLETED'),
        'cancelled_appointments': appointments.filter(status='CANCELLED')
    })

@login_required
@patient_required
def book_appointment(request, doctor_id):
    doctor = get_object_or_404(DoctorProfile, id=doctor_id)
    
    # Ensure user has a patient profile
    try:
        patient = request.user.patient_profile
    except PatientProfile.DoesNotExist:
        messages.error(request, 'Please complete your patient profile before booking appointments.')
        return redirect('profile')
    
    # Get only future slots that are available
    current_time = timezone.now()
    slots = doctor.schedule_slots.filter(
        is_booked=False,
        is_available=True,
        start_time__gt=current_time
    ).order_by('start_time')
    
    # Get available services for this doctor
    services = doctor.services.filter(is_active=True)
    
    if request.method == 'POST':
        form = AppointmentForm(request.POST)
        slot_id = request.POST.get('slot')
        service_id = request.POST.get('service')
        
        if not slot_id:
            messages.error(request, 'Please select a time slot.')
            return render(request, 'book_appointment.html', {
                'form': form,
                'doctor': doctor,
                'slots': slots,
                'services': services
            })
            
        if not service_id:
            messages.error(request, 'Please select a service.')
            return render(request, 'book_appointment.html', {
                'form': form,
                'doctor': doctor,
                'slots': slots,
                'services': services
            })
            
        try:
            slot = ScheduleSlot.objects.get(
                id=slot_id,
                doctor=doctor,
                is_booked=False,
                is_available=True,
                start_time__gt=current_time
            )
            
            service = Service.objects.get(
                id=service_id,
                doctors=doctor,
                is_active=True
            )
        except ScheduleSlot.DoesNotExist:
            messages.error(request, 'The selected time slot is no longer available.')
            return redirect('book_appointment', doctor_id=doctor_id)
        except Service.DoesNotExist:
            messages.error(request, 'The selected service is not available.')
            return redirect('book_appointment', doctor_id=doctor_id)
            
        if form.is_valid():
            try:
                with transaction.atomic():
                    appt = form.save(commit=False)
                    appt.patient = patient
                    appt.doctor = doctor
                    appt.slot = slot
                    appt.datetime = slot.start_time
                    appt.service = service
                    appt.save()
                    
                    slot.is_booked = True
                    slot.save()
                    
                    # Notify patient
                    Notification.objects.create(
                        user=request.user,
                        type='IN_APP',
                        title='Appointment Booked',
                        message=f'Your appointment for {service.name} with Dr. {doctor.user.get_full_name()} is scheduled for {slot.start_time.strftime("%B %d, %Y at %I:%M %p")}'
                    )
                    
                    # Notify doctor
                    Notification.objects.create(
                        user=doctor.user,
                        type='IN_APP',
                        title='New Appointment',
                        message=f'New appointment for {service.name} with {patient.full_name} scheduled for {slot.start_time.strftime("%B %d, %Y at %I:%M %p")}'
                    )
                    
                    messages.success(request, 'Your appointment has been booked successfully.')
                    return redirect('appointments')
                    
            except Exception as e:
                messages.error(request, 'There was an error booking your appointment. Please try again.')
                return redirect('book_appointment', doctor_id=doctor_id)
    else:
        form = AppointmentForm()
        
    return render(request, 'book_appointment.html', {
        'form': form,
        'doctor': doctor,
        'slots': slots,
        'services': services
    })

@login_required
@patient_required
def cancel_appointment(request, appointment_id):
    appointment = get_object_or_404(
        Appointment, 
        id=appointment_id,
        patient=request.user.patient_profile
    )
    
    if appointment.status not in ['PENDING', 'CONFIRMED']:
        messages.error(request, 'This appointment cannot be cancelled.')
        return redirect('appointments')
    
    try:
        with transaction.atomic():
            # Update appointment status
            appointment.status = 'CANCELLED'
            appointment.cancellation_reason = request.POST.get('reason', 'Cancelled by patient')
            appointment.save()
            
            # Free up the slot
            if appointment.slot:
                appointment.slot.is_booked = False
                appointment.slot.save()
            
            # Notify the doctor
            Notification.objects.create(
                user=appointment.doctor.user,
                type='IN_APP',
                title='Appointment Cancelled',
                message=f'Appointment with {appointment.patient.full_name} for {appointment.datetime.strftime("%B %d, %Y at %I:%M %p")} has been cancelled.'
            )
            
            messages.success(request, 'Appointment cancelled successfully.')
    except Exception as e:
        messages.error(request, 'There was an error cancelling your appointment.')
    
    return redirect('appointments')

@login_required
@patient_required
def reschedule_appointment(request, appointment_id):
    appointment = get_object_or_404(
        Appointment, 
        id=appointment_id,
        patient=request.user.patient_profile,
        status='PENDING'
    )
    
    if request.method == 'POST':
        new_slot_id = request.POST.get('slot')
        if not new_slot_id:
            messages.error(request, 'Please select a new time slot.')
            return redirect('reschedule_appointment', appointment_id=appointment_id)
        
        try:
            with transaction.atomic():
                # Get the new slot
                new_slot = ScheduleSlot.objects.select_for_update().get(
                    id=new_slot_id,
                    doctor=appointment.doctor,
                    is_booked=False,
                    is_available=True,
                    start_time__gt=timezone.now()
                )
                
                # Free up the old slot
                if appointment.slot:
                    appointment.slot.is_booked = False
                    appointment.slot.save()
                
                # Update appointment with new slot
                appointment.slot = new_slot
                appointment.datetime = new_slot.start_time
                appointment.save()
                
                # Mark new slot as booked
                new_slot.is_booked = True
                new_slot.save()
                
                # Notify the doctor
                Notification.objects.create(
                    user=appointment.doctor.user,
                    type='IN_APP',
                    title='Appointment Rescheduled',
                    message=f'Appointment with {appointment.patient.full_name} has been rescheduled to {new_slot.start_time.strftime("%B %d, %Y at %I:%M %p")}'
                )
                
                messages.success(request, 'Appointment rescheduled successfully.')
                return redirect('appointments')
                
        except ScheduleSlot.DoesNotExist:
            messages.error(request, 'The selected time slot is no longer available.')
        except Exception as e:
            messages.error(request, 'There was an error rescheduling your appointment.')
        
        return redirect('reschedule_appointment', appointment_id=appointment_id)
    
    # For GET requests, show available slots
    available_slots = ScheduleSlot.objects.filter(
        doctor=appointment.doctor,
        is_booked=False,
        is_available=True,
        start_time__gt=timezone.now()
    ).order_by('start_time')
    
    return render(request, 'reschedule_appointment.html', {
        'appointment': appointment,
        'available_slots': available_slots
    })

def signup(request):
    # Redirect authenticated users
    if request.user.is_authenticated:
        if is_admin(request.user):
            return redirect('admin:index')
        return redirect('home')
        
    if request.method == 'POST':
        user_form = CustomUserCreationForm(request.POST)
        profile_form = PatientProfileForm(request.POST)
        
        if user_form.is_valid() and profile_form.is_valid():
            user = user_form.save()
            profile = profile_form.save(commit=False)
            profile.user = user
            profile.save()
            
            username = user_form.cleaned_data.get('username')
            raw_password = user_form.cleaned_data.get('password1')
            # Login the user - this will trigger the user_logged_in signal
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
    # Redirect admin users to admin interface
    if is_admin(request.user):
        return redirect('admin:index')
        
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
    # Redirect admin users to admin interface for password changes
    if is_admin(request.user):
        return redirect('admin:password_change')
        
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