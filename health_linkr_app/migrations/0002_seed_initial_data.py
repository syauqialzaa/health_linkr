from django.db import migrations
from django.contrib.auth.hashers import make_password
from django.utils import timezone
from datetime import timedelta

def create_initial_data(apps, schema_editor):
    # Get models
    User = apps.get_model('health_linkr_app', 'User')
    Role = apps.get_model('health_linkr_app', 'Role')
    Clinic = apps.get_model('health_linkr_app', 'Clinic')
    DoctorProfile = apps.get_model('health_linkr_app', 'DoctorProfile')
    Service = apps.get_model('health_linkr_app', 'Service')
    ScheduleSlot = apps.get_model('health_linkr_app', 'ScheduleSlot')
    
    # Create roles
    admin_role = Role.objects.create(
        name='ADMIN',
        permissions={'can_manage_all': True}
    )
    doctor_role = Role.objects.create(
        name='DOCTOR',
        permissions={
            'can_view_appointments': True,
            'can_change_appointment_status': True,
            'can_add_appointment_notes': True
        }
    )
    patient_role = Role.objects.create(
        name='PATIENT',
        permissions={'can_book_appointments': True}
    )

    # Create clinics
    clinic1 = Clinic.objects.create(
        name='HealthCare Center',
        address='123 Main Street, City Center',
        contact_number='(555) 123-4567',
        email='info@healthcarecenter.com',
        description='A modern healthcare facility providing comprehensive medical services.',
        opening_hours={
            'monday': {'open': '08:00', 'close': '17:00'},
            'tuesday': {'open': '08:00', 'close': '17:00'},
            'wednesday': {'open': '08:00', 'close': '17:00'},
            'thursday': {'open': '08:00', 'close': '17:00'},
            'friday': {'open': '08:00', 'close': '16:00'},
            'saturday': {'open': '09:00', 'close': '13:00'},
            'sunday': {'open': '', 'close': ''}
        },
        is_active=True
    )

    clinic2 = Clinic.objects.create(
        name='City Medical Center',
        address='456 Oak Avenue, Downtown',
        contact_number='(555) 987-6543',
        email='contact@citymedical.com',
        description='Specialized medical care with state-of-the-art facilities.',
        opening_hours={
            'Monday': '8:30-18:00',
            'Tuesday': '8:30-18:00',
            'Wednesday': '8:30-18:00',
            'Thursday': '8:30-18:00',
            'Friday': '8:30-17:00',
            'Saturday': '9:00-14:00',
            'Sunday': 'Closed'
        },
        is_active=True
    )

    # Create doctors
    doctor1_user = User.objects.create(
        username='dr.smith',
        password=make_password('doctor123'),
        email='dr.smith@healthcarecenter.com',
        first_name='John',
        last_name='Smith',
        is_staff=True
    )
    doctor1_user.roles.add(doctor_role)

    doctor1 = DoctorProfile.objects.create(
        user=doctor1_user,
        specialty='Cardiology',
        qualification='MD, PhD in Cardiology',
        clinic=clinic1,
        bio='Experienced cardiologist with over 15 years of practice.',
        consultation_fee=150.00,
        years_of_experience=15,
        is_active=True
    )

    doctor2_user = User.objects.create(
        username='dr.jones',
          d=make_password('doctor123'),
        email='dr.jones@citymedical.com',
        first_name='Sarah',
        last_name='Jones',
        is_staff=True
    )
    doctor2_user.roles.add(doctor_role)

    doctor2 = DoctorProfile.objects.create(
        user=doctor2_user,
        specialty='Pediatrics',
        qualification='MD, Board Certified in Pediatrics',
        clinic=clinic2,
        bio='Dedicated pediatrician focused on child healthcare.',
        consultation_fee=100.00,
        years_of_experience=10,
        is_active=True
    )

    # Create services
    service1 = Service.objects.create(
        name='General Consultation',
        description='Regular medical consultation and check-up',
        duration_minutes=30,
        fee=100.00,
        is_active=True,
        clinic=clinic1
    )
    service1.doctors.add(doctor1)

    service2 = Service.objects.create(
        name='Pediatric Check-up',
        description='Comprehensive child health examination',
        duration_minutes=45,
        fee=120.00,
        is_active=True,
        clinic=clinic2
    )
    service2.doctors.add(doctor2)

    # Create schedule slots for the next 7 days
    start_date = timezone.now().replace(hour=9, minute=0, second=0, microsecond=0)
    for day in range(7):
        current_date = start_date + timedelta(days=day)
        
        # Morning slots
        for hour in range(9, 12):
            ScheduleSlot.objects.create(
                doctor=doctor1,
                start_time=current_date.replace(hour=hour),
                end_time=current_date.replace(hour=hour) + timedelta(minutes=30),
                is_booked=False,
                is_available=True
            )
            ScheduleSlot.objects.create(
                doctor=doctor2,
                start_time=current_date.replace(hour=hour),
                end_time=current_date.replace(hour=hour) + timedelta(minutes=45),
                is_booked=False,
                is_available=True
            )
        
        # Afternoon slots
        for hour in range(14, 17):
            ScheduleSlot.objects.create(
                doctor=doctor1,
                start_time=current_date.replace(hour=hour),
                end_time=current_date.replace(hour=hour) + timedelta(minutes=30),
                is_booked=False,
                is_available=True
            )
            ScheduleSlot.objects.create(
                doctor=doctor2,
                start_time=current_date.replace(hour=hour),
                end_time=current_date.replace(hour=hour) + timedelta(minutes=45),
                is_booked=False,
                is_available=True
            )

def remove_initial_data(apps, schema_editor):
    # Get models
    User = apps.get_model('health_linkr_app', 'User')
    Role = apps.get_model('health_linkr_app', 'Role')
    Clinic = apps.get_model('health_linkr_app', 'Clinic')
    Service = apps.get_model('health_linkr_app', 'Service')
    ScheduleSlot = apps.get_model('health_linkr_app', 'ScheduleSlot')
    
    # Remove all seeded data
    ScheduleSlot.objects.all().delete()
    Service.objects.all().delete()
    Clinic.objects.all().delete()
    User.objects.exclude(is_superuser=True).delete()
    Role.objects.all().delete()

class Migration(migrations.Migration):
    dependencies = [
        ('health_linkr_app', '0001_init_tables'),
    ]

    operations = [
        migrations.RunPython(create_initial_data, remove_initial_data),
    ]
