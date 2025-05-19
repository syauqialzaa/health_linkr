from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import (
    User, Role, PatientProfile, DoctorProfile, Clinic,
    Service, ScheduleSlot, Appointment, Notification,
    SessionLog, AuditTrail
)

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'is_active', 'is_superuser', 'get_roles')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    list_filter = ('is_staff', 'is_active', 'is_superuser', 'roles')
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'email', 'phone', 'profile_photo')}),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'roles', 'groups', 'user_permissions'),
            'classes': ('collapse',),
            'description': 'Important: Staff status is required to access the admin interface.'
        }),
        ('Important dates', {'fields': ('last_login', 'date_joined'), 'classes': ('collapse',)}),
    )
    
    def get_roles(self, obj):
        return ", ".join([role.get_name_display() for role in obj.roles.all()])
    get_roles.short_description = 'Roles'
    
    def get_readonly_fields(self, request, obj=None):
        if not request.user.is_superuser:
            return ('is_superuser', 'user_permissions', 'groups')
        return super().get_readonly_fields(request, obj)
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            return qs.filter(is_superuser=False)
        return qs
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2'),
        }),
    )

@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

@admin.register(PatientProfile)
class PatientProfileAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'gender', 'birth_date', 'phone')
    search_fields = ('full_name', 'phone', 'emergency_contact')
    list_filter = ('gender',)

@admin.register(Clinic)
class ClinicAdmin(admin.ModelAdmin):
    list_display = ('name', 'contact_number', 'email', 'is_active')
    search_fields = ('name', 'address', 'contact_number', 'email')
    list_filter = ('is_active',)

@admin.register(DoctorProfile)
class DoctorProfileAdmin(admin.ModelAdmin):
    list_display = ('get_full_name', 'specialty', 'clinic', 'consultation_fee', 'is_active')
    search_fields = ('user__first_name', 'user__last_name', 'specialty', 'qualification')
    list_filter = ('specialty', 'is_active', 'clinic')
    
    def get_full_name(self, obj):
        return f"Dr. {obj.user.get_full_name()}"
    get_full_name.short_description = 'Name'

@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('name', 'clinic', 'duration_minutes', 'fee', 'is_active')
    search_fields = ('name', 'description')
    list_filter = ('clinic', 'is_active')

@admin.register(ScheduleSlot)
class ScheduleSlotAdmin(admin.ModelAdmin):
    list_display = ('doctor', 'start_time', 'end_time', 'is_booked', 'is_available')
    search_fields = ('doctor__user__first_name', 'doctor__user__last_name')
    list_filter = ('is_booked', 'is_available', 'doctor')
    date_hierarchy = 'start_time'

@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ('patient', 'doctor', 'datetime', 'status', 'service')
    search_fields = (
        'patient__full_name',
        'doctor__user__first_name',
        'doctor__user__last_name'
    )
    list_filter = ('status', 'doctor', 'service')
    date_hierarchy = 'datetime'

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'type', 'title', 'sent_at', 'read_flag')
    search_fields = ('user__username', 'title', 'message')
    list_filter = ('type', 'read_flag')
    date_hierarchy = 'sent_at'

@admin.register(SessionLog)
class SessionLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'login_time', 'logout_time', 'is_expired')
    search_fields = ('user__username', 'ip_address')
    list_filter = ('is_expired',)
    date_hierarchy = 'login_time'

@admin.register(AuditTrail)
class AuditTrailAdmin(admin.ModelAdmin):
    list_display = ('user', 'action', 'model_name', 'timestamp')
    search_fields = ('user__username', 'action', 'model_name', 'object_repr')
    list_filter = ('action', 'model_name')
    date_hierarchy = 'timestamp'
