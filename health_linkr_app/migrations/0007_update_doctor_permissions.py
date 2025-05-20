from django.db import migrations

def update_doctor_permissions(apps, schema_editor):
    User = apps.get_model('health_linkr_app', 'User')
    DoctorProfile = apps.get_model('health_linkr_app', 'DoctorProfile')
    
    # Get all users who are doctors
    doctor_users = User.objects.filter(doctor_profile__isnull=False)
    
    # Update them to be staff members
    doctor_users.update(is_staff=True)

def reverse_doctor_permissions(apps, schema_editor):
    User = apps.get_model('health_linkr_app', 'User')
    DoctorProfile = apps.get_model('health_linkr_app', 'DoctorProfile')
    
    # Get all users who are doctors but not superusers
    doctor_users = User.objects.filter(
        doctor_profile__isnull=False,
        is_superuser=False
    )
    
    # Remove staff status
    doctor_users.update(is_staff=False)

class Migration(migrations.Migration):
    dependencies = [
        ('health_linkr_app', '0006_update_appointment_model'),
    ]

    operations = [
        migrations.RunPython(
            update_doctor_permissions,
            reverse_doctor_permissions
        ),
    ]
