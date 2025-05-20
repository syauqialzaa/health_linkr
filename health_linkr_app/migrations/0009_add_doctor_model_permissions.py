from django.db import migrations

def add_doctor_permissions(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    Permission = apps.get_model('auth', 'Permission')
    ContentType = apps.get_model('contenttypes', 'ContentType')
    User = apps.get_model('health_linkr_app', 'User')

    # Get or create doctors group
    doctors_group, _ = Group.objects.get_or_create(name='Doctors')

    # Get content types
    app_label = 'health_linkr_app'
    content_types = {
        'appointment': ContentType.objects.get(app_label=app_label, model='appointment'),
        'scheduleslot': ContentType.objects.get(app_label=app_label, model='scheduleslot'),
        'service': ContentType.objects.get(app_label=app_label, model='service')
    }

    # Define permissions to add
    permissions_to_add = [
        ('view_appointment', 'Can view appointment', 'appointment'),
        ('change_appointment', 'Can change appointment', 'appointment'),
        ('view_scheduleslot', 'Can view schedule slot', 'scheduleslot'),
        ('add_scheduleslot', 'Can add schedule slot', 'scheduleslot'),
        ('change_scheduleslot', 'Can change schedule slot', 'scheduleslot'),
        ('delete_scheduleslot', 'Can delete schedule slot', 'scheduleslot'),
        ('view_service', 'Can view service', 'service')
    ]

    # Create permissions and add to group
    permissions = []
    for codename, name, model in permissions_to_add:
        permission, _ = Permission.objects.get_or_create(
            codename=codename,
            content_type=content_types[model],
            defaults={'name': name}
        )
        permissions.append(permission)

    doctors_group.permissions.add(*permissions)

    # Update doctor users
    doctor_users = User.objects.filter(doctor_profile__isnull=False)
    for user in doctor_users:
        user.is_staff = True
        user.groups.add(doctors_group)
        user.save()

def remove_doctor_permissions(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    User = apps.get_model('health_linkr_app', 'User')

    # Remove doctors group and all its permissions
    try:
        doctors_group = Group.objects.get(name='Doctors')
        doctors_group.delete()
    except Group.DoesNotExist:
        pass

    # Remove staff status from doctors
    doctor_users = User.objects.filter(doctor_profile__isnull=False)
    doctor_users.update(is_staff=False)

class Migration(migrations.Migration):
    dependencies = [
        ('health_linkr_app', '0008_enhance_clinic_model'),
    ]

    operations = [
        migrations.RunPython(
            add_doctor_permissions,
            remove_doctor_permissions
        ),
    ]
