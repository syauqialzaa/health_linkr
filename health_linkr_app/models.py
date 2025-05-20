from django.db import models
from django.contrib.auth.models import AbstractUser, Group, Permission
from django.utils import timezone

class Role(models.Model):
    ADMIN = 'ADMIN'
    DOCTOR = 'DOCTOR'
    PATIENT = 'PATIENT'
    
    ROLE_CHOICES = [
        (ADMIN, 'Administrator'),
        (DOCTOR, 'Doctor'),
        (PATIENT, 'Patient'),
    ]
    
    name = models.CharField(max_length=50, unique=True, choices=ROLE_CHOICES)
    permissions = models.JSONField(
        default=dict,
        help_text="Dictionary of custom permissions, e.g. {'can_edit_appointment': True}"
    )

    def __str__(self):
        return self.name

class User(AbstractUser):
    email = models.EmailField(unique=True)
    roles = models.ManyToManyField(Role, related_name='users')
    profile_photo = models.ImageField(upload_to='profile_photos/', null=True, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    
    groups = models.ManyToManyField(
        Group,
        related_name='custom_user_set',
        blank=True,
        help_text='The groups this user belongs to.',
        verbose_name='groups',
    )
    user_permissions = models.ManyToManyField(
        Permission,
        related_name='custom_user_set',
        blank=True,
        help_text='Specific permissions for this user.',
        verbose_name='user permissions',
    )

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        
        if is_new:
            if self.is_superuser:
                admin_role, _ = Role.objects.get_or_create(
                    name=Role.ADMIN,
                    defaults={'permissions': {'can_manage_all': True}}
                )
                self.roles.add(admin_role)
                self.is_staff = True
                self.save(update_fields=['is_staff'])
            elif hasattr(self, 'doctor_profile'):
                # Make doctors staff members with limited permissions
                self.is_staff = True
                self.save(update_fields=['is_staff'])

    REQUIRED_FIELDS = ['email']

    def __str__(self):
        return f"{self.get_full_name()} ({self.email})"

class PatientProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='patient_profile')
    full_name = models.CharField(max_length=150)
    birth_date = models.DateField()
    gender = models.CharField(max_length=10, choices=[('M', 'Male'), ('F', 'Female')])
    phone = models.CharField(max_length=20)
    medical_history = models.TextField(blank=True)
    emergency_contact = models.CharField(max_length=150, blank=True)
    emergency_phone = models.CharField(max_length=20, blank=True)

    def __str__(self):
        return f"{self.full_name} (Patient)"

class Clinic(models.Model):
    name = models.CharField(max_length=150)
    address = models.TextField()
    contact_number = models.CharField(max_length=20)
    email = models.EmailField(blank=True)
    description = models.TextField(blank=True)
    website = models.URLField(blank=True)
    opening_hours = models.JSONField(
        default=dict,
        help_text='Format: {"monday": {"open": "09:00", "close": "17:00"}, ...}'
    )
    facilities = models.JSONField(
        default=list,
        help_text='List of available facilities and equipment'
    )
    insurance_accepted = models.JSONField(
        default=list,
        help_text='List of accepted insurance providers'
    )
    specialties = models.JSONField(
        default=list,
        help_text='Medical specialties available at this clinic'
    )
    emergency_number = models.CharField(max_length=20, blank=True)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return self.name

    def get_available_doctors(self):
        """Get all active doctors in this clinic"""
        return self.doctors.filter(is_active=True)

    def get_available_services(self):
        """Get all active services in this clinic"""
        return self.services.filter(is_active=True)

    def get_formatted_hours(self):
        """Return opening hours in a formatted way"""
        days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
        formatted = {}
        for day in days:
            hours = self.opening_hours.get(day, {})
            if hours:
                formatted[day] = f"{hours.get('open', 'Closed')} - {hours.get('close', 'Closed')}"
            else:
                formatted[day] = "Closed"
        return formatted

class DoctorProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='doctor_profile')
    specialty = models.CharField(max_length=100)
    qualification = models.CharField(max_length=200)
    clinic = models.ForeignKey(Clinic, on_delete=models.SET_NULL, null=True, related_name='doctors')
    bio = models.TextField(blank=True)
    consultation_fee = models.DecimalField(max_digits=10, decimal_places=2)
    years_of_experience = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"Dr. {self.user.get_full_name()} ({self.specialty})"

class Service(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    duration_minutes = models.PositiveIntegerField()
    fee = models.DecimalField(max_digits=10, decimal_places=2)
    is_active = models.BooleanField(default=True)
    clinic = models.ForeignKey(Clinic, on_delete=models.CASCADE, related_name='services')
    doctors = models.ManyToManyField(DoctorProfile, related_name='services')

    def __str__(self):
        return f"{self.name} at {self.clinic.name} ({self.duration_minutes} mins, ${self.fee})"

class ScheduleSlot(models.Model):
    doctor = models.ForeignKey(DoctorProfile, on_delete=models.CASCADE, related_name='schedule_slots')
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    is_booked = models.BooleanField(default=False)
    is_available = models.BooleanField(default=True)
    recurrence_pattern = models.JSONField(null=True, blank=True)

    class Meta:
        ordering = ['start_time']
        constraints = [
            models.CheckConstraint(
                check=models.Q(end_time__gt=models.F('start_time')),
                name='valid_schedule_slot_duration'
            )
        ]

    def __str__(self):
        return f"Dr. {self.doctor.user.get_full_name()} - {self.start_time}"

class Appointment(models.Model):
    PENDING = 'PENDING'
    CONFIRMED = 'CONFIRMED'
    COMPLETED = 'COMPLETED'
    CANCELLED = 'CANCELLED'
    
    STATUS_CHOICES = [
        (PENDING, 'Pending'),
        (CONFIRMED, 'Confirmed'),
        (COMPLETED, 'Completed'),
        (CANCELLED, 'Cancelled'),
    ]
    
    patient = models.ForeignKey(PatientProfile, on_delete=models.CASCADE, related_name='appointments')
    doctor = models.ForeignKey(DoctorProfile, on_delete=models.CASCADE, related_name='appointments')
    service = models.ForeignKey(Service, on_delete=models.SET_NULL, null=True, related_name='appointments')
    datetime = models.DateTimeField()
    slot = models.ForeignKey(ScheduleSlot, on_delete=models.SET_NULL, null=True, related_name='appointment')
    notes = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-datetime']
        indexes = [
            models.Index(fields=['status', 'datetime']),
            models.Index(fields=['patient', 'status']),
            models.Index(fields=['doctor', 'status']),
        ]

    def __str__(self):
        return f"[{self.status}] {self.patient.full_name} with {self.doctor} on {self.datetime.strftime('%B %d, %Y at %I:%M %p')}"

    def save(self, *args, **kwargs):
        if self.status == self.CANCELLED and self.slot:
            # Free up the slot if appointment is cancelled
            self.slot.is_booked = False
            self.slot.save()
        super().save(*args, **kwargs)

class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ('EMAIL', 'Email'),
        ('SMS', 'SMS'),
        ('IN_APP', 'In-App'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    type = models.CharField(max_length=10, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=200)
    message = models.TextField()
    sent_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)
    read_flag = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.type} notification for {self.user.username}"

class SessionLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='session_logs')
    login_time = models.DateTimeField(auto_now_add=True)
    logout_time = models.DateTimeField(null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)  # Made nullable for flexibility
    user_agent = models.TextField(blank=True)
    session_id = models.CharField(max_length=100, blank=True)
    is_expired = models.BooleanField(default=False)

    class Meta:
        ordering = ['-login_time']
        indexes = [
            models.Index(fields=['user', 'session_id', 'is_expired']),
            models.Index(fields=['login_time', 'logout_time']),
        ]

    def __str__(self):
        status = 'Active' if not self.is_expired and not self.logout_time else 'Expired/Logged out'
        return f"Session for {self.user.username} - {status} - Started at {self.login_time}"

    def save(self, *args, **kwargs):
        if self.logout_time and not self.is_expired:
            self.is_expired = True
        super().save(*args, **kwargs)

class AuditTrail(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=50)
    model_name = models.CharField(max_length=50)
    object_id = models.PositiveIntegerField()
    object_repr = models.CharField(max_length=200)
    changes = models.JSONField()
    timestamp = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True)

    def __str__(self):
        return f"{self.user.username} - {self.action} - {self.timestamp}"