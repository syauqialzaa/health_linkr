from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.db import transaction
from django.contrib.auth.models import Permission
from django.db.models import Q
from django.utils.html import format_html
from .models import (
    User, Role, PatientProfile, DoctorProfile, Clinic,
    Service, ScheduleSlot, Appointment, Notification,
    SessionLog, AuditTrail
)

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'is_active', 'is_superuser')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    list_filter = ('is_staff', 'is_active', 'is_superuser', 'roles')
    ordering = ('username',)
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'email', 'phone', 'profile_photo')}),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'roles', 'groups', 'user_permissions'),
        }),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )

@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

@admin.register(PatientProfile)
class PatientProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'full_name', 'gender', 'phone')
    search_fields = ('full_name', 'phone')
    list_filter = ('gender',)

@admin.register(Clinic)
class ClinicAdmin(admin.ModelAdmin):
    list_display = ('name', 'address', 'contact_number', 'is_active')
    search_fields = ('name', 'address')
    list_filter = ('is_active',)

@admin.register(DoctorProfile)
class DoctorProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'specialty', 'clinic', 'is_active')
    search_fields = ('user__username', 'specialty')
    list_filter = ('specialty', 'clinic', 'is_active')

@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('name', 'clinic', 'duration_minutes', 'fee', 'is_active')
    search_fields = ('name',)
    list_filter = ('clinic', 'is_active')
    ordering = ['name']
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        if hasattr(request.user, 'doctor_profile'):
            return qs.filter(doctors=request.user.doctor_profile)
        return qs.none()
    
    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser
        
    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser
        
    def has_add_permission(self, request):
        return request.user.is_superuser

@admin.register(ScheduleSlot)
class ScheduleSlotAdmin(admin.ModelAdmin):
    list_display = ('doctor', 'start_time', 'end_time', 'is_booked', 'is_available')
    search_fields = ('doctor__user__username',)
    list_filter = ('is_booked', 'is_available')
    date_hierarchy = 'start_time'
    ordering = ['start_time']
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        if hasattr(request.user, 'doctor_profile'):
            return qs.filter(doctor=request.user.doctor_profile)
        return qs.none()
        
    def has_change_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        if not hasattr(request.user, 'doctor_profile'):
            return False
        if obj is None:
            return True
        return obj.doctor == request.user.doctor_profile and not obj.is_booked
        
    def has_delete_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        if not hasattr(request.user, 'doctor_profile'):
            return False
        if obj is None:
            return True
        return obj.doctor == request.user.doctor_profile and not obj.is_booked
        
    def has_add_permission(self, request):
        return request.user.is_superuser or hasattr(request.user, 'doctor_profile')
        
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "doctor" and not request.user.is_superuser:
            if hasattr(request.user, 'doctor_profile'):
                kwargs["queryset"] = DoctorProfile.objects.filter(user=request.user)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ('patient_name', 'doctor_name', 'service_name', 'formatted_datetime', 'colored_status', 'notes_preview')
    list_filter = ('status', 'datetime', 'service')
    search_fields = ('patient__full_name', 'doctor__user__username', 'notes')
    date_hierarchy = 'datetime'
    list_per_page = 20
    actions = ['mark_as_confirmed', 'mark_as_completed', 'mark_as_cancelled']
    
    def patient_name(self, obj):
        return obj.patient.full_name
    patient_name.short_description = 'Patient'
    
    def doctor_name(self, obj):
        return f"Dr. {obj.doctor.user.get_full_name()}"
    doctor_name.short_description = 'Doctor'
    
    def service_name(self, obj):
        return obj.service.name
    service_name.short_description = 'Service'
    
    def formatted_datetime(self, obj):
        return obj.datetime.strftime("%B %d, %Y at %I:%M %p")
    formatted_datetime.short_description = 'Date & Time'
    
    def colored_status(self, obj):
        colors = {
            'PENDING': 'orange',
            'CONFIRMED': 'blue',
            'COMPLETED': 'green',
            'CANCELLED': 'red'
        }
        return format_html(
            '<span style="color: {};">{}</span>',
            colors.get(obj.status, 'black'),
            obj.status
        )
    colored_status.short_description = 'Status'

    def notes_preview(self, obj):
        """Show a preview of notes in list view"""
        if obj.notes:
            return obj.notes[:50] + '...' if len(obj.notes) > 50 else obj.notes
        return '-'
    notes_preview.short_description = 'Notes'

    fieldsets = (
        ('Appointment Details', {
            'fields': (
                ('patient', 'doctor'),
                ('service', 'datetime'),
                'status',
            ),
            'description': 'Core appointment information'
        }),
        ('Medical Notes', {
            'fields': ('notes',),
            'description': 'Add medical notes, prescriptions, or follow-up instructions'
        }),
    )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        # Doctors can only see their own appointments
        if hasattr(request.user, 'doctor_profile'):
            return qs.filter(doctor=request.user.doctor_profile)
        return qs.none()

    def has_add_permission(self, request):
        # Only superusers can add appointments directly
        return request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        if not hasattr(request.user, 'doctor_profile'):
            return False
        # Doctors can only change their own appointments that aren't cancelled
        if obj is None:  # This is for the changelist view
            return True
        if obj.status == 'CANCELLED':
            return False
        return obj.doctor == request.user.doctor_profile

    def has_delete_permission(self, request, obj=None):
        # Only superusers can delete appointments
        return request.user.is_superuser

    def has_view_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        # Doctors can view appointments list and their own appointments
        return hasattr(request.user, 'doctor_profile')

    def get_readonly_fields(self, request, obj=None):
        if request.user.is_superuser:
            return []
        # Doctors can only update status, notes, and add prescription/followup info
        if hasattr(request.user, 'doctor_profile'):
            status_allowed = obj.status if obj else None
            if status_allowed == 'COMPLETED':
                return ['patient', 'doctor', 'service', 'datetime', 'status']
            return ['patient', 'doctor', 'service', 'datetime']
        return self.get_fields(request)

    def save_model(self, request, obj, form, change):
        if change:
            old_obj = self.model.objects.get(pk=obj.pk)
            old_status = old_obj.status
            old_notes = old_obj.notes
            new_status = obj.status
            
            # Track status changes
            if old_status != new_status:
                status_messages = {
                    'CONFIRMED': f'Please arrive 10 minutes before your scheduled time: {obj.datetime.strftime("%B %d, %Y at %I:%M %p")}',
                    'COMPLETED': 'Thank you for visiting. Please check your medical notes for any follow-up instructions.',
                    'CANCELLED': 'If you need to reschedule, please book a new appointment.',
                }
                
                message = f'Your appointment with Dr. {obj.doctor.user.get_full_name()} has been {new_status.lower()}'
                if new_status in status_messages:
                    message += '. ' + status_messages[new_status]
                
                Notification.objects.create(
                    user=obj.patient.user,
                    type='IN_APP',
                    title=f'Appointment {new_status.title()}',
                    message=message
                )
            
            # Track notes changes
            if old_notes != obj.notes and obj.notes:
                Notification.objects.create(
                    user=obj.patient.user,
                    type='IN_APP',
                    title='Medical Notes Updated',
                    message=f'Dr. {obj.doctor.user.get_full_name()} has updated your appointment notes.'
                )
        
        super().save_model(request, obj, form, change)

    class Media:
        css = {
            'all': ['admin/css/custom_admin.css']
        }

    def mark_as_confirmed(self, request, queryset):
        """Bulk action to mark appointments as confirmed"""
        updated = queryset.update(status='CONFIRMED')
        for appointment in queryset:
            Notification.objects.create(
                user=appointment.patient.user,
                type='IN_APP',
                title='Appointment Confirmed',
                message=f'Your appointment with Dr. {appointment.doctor.user.get_full_name()} on {appointment.datetime.strftime("%B %d, %Y at %I:%M %p")} has been confirmed.'
            )
        self.message_user(request, f'{updated} appointments were successfully confirmed.')
    mark_as_confirmed.short_description = 'Mark selected appointments as confirmed'

    def mark_as_completed(self, request, queryset):
        """Bulk action to mark appointments as completed"""
        updated = queryset.update(status='COMPLETED')
        for appointment in queryset:
            Notification.objects.create(
                user=appointment.patient.user,
                type='IN_APP',
                title='Appointment Completed',
                message=f'Your appointment with Dr. {appointment.doctor.user.get_full_name()} has been marked as completed.'
            )
        self.message_user(request, f'{updated} appointments were successfully completed.')
    mark_as_completed.short_description = 'Mark selected appointments as completed'

    def mark_as_cancelled(self, request, queryset):
        """Bulk action to mark appointments as cancelled"""
        with transaction.atomic():
            for appointment in queryset:
                appointment.status = 'CANCELLED'
                appointment.save()  # This will trigger the save method to free up slots
                Notification.objects.create(
                    user=appointment.patient.user,
                    type='IN_APP',
                    title='Appointment Cancelled',
                    message=f'Your appointment with Dr. {appointment.doctor.user.get_full_name()} scheduled for {appointment.datetime.strftime("%B %d, %Y at %I:%M %p")} has been cancelled.'
                )
        self.message_user(request, f'{queryset.count()} appointments were successfully cancelled.')
    mark_as_cancelled.short_description = 'Mark selected appointments as cancelled'

    def formfield_for_choice_field(self, db_field, request, **kwargs):
        """Control which status options are available based on current status and user role"""
        if db_field.name == "status" and not request.user.is_superuser:
            if hasattr(request.user, 'doctor_profile'):
                if 'object_id' in request.resolver_match.kwargs:
                    obj = self.get_object(request, request.resolver_match.kwargs['object_id'])
                    if obj:
                        # Define allowed transitions
                        status_transitions = {
                            'PENDING': ['CONFIRMED', 'CANCELLED'],
                            'CONFIRMED': ['COMPLETED', 'CANCELLED'],
                            'COMPLETED': ['COMPLETED'],  # Can't change once completed
                            'CANCELLED': ['CANCELLED'],  # Can't change once cancelled
                        }
                        kwargs['choices'] = [
                            (key, value) for key, value in Appointment.STATUS_CHOICES
                            if key in status_transitions.get(obj.status, [])
                        ]
        return super().formfield_for_choice_field(db_field, request, **kwargs)

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'type', 'title', 'sent_at', 'read_flag')
    search_fields = ('user__username', 'title', 'message')
    list_filter = ('type', 'read_flag')
    date_hierarchy = 'sent_at'

@admin.register(SessionLog)
class SessionLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'login_time', 'logout_time', 'is_expired', 'ip_address')
    search_fields = ('user__username', 'ip_address')
    list_filter = ('is_expired',)
    date_hierarchy = 'login_time'

@admin.register(AuditTrail)
class AuditTrailAdmin(admin.ModelAdmin):
    list_display = ('user', 'action', 'model_name', 'timestamp', 'ip_address')
    search_fields = ('user__username', 'action', 'model_name')
    list_filter = ('action', 'model_name')
    date_hierarchy = 'timestamp'

class CustomAdminSite(admin.AdminSite):
    site_title = 'HealthLinkr Admin'
    site_header = 'HealthLinkr Administration'
    index_title = 'Administration'

    def has_permission(self, request):
        """Allow both superusers and staff (doctors) to access admin"""
        return request.user.is_active and (request.user.is_staff or request.user.is_superuser)

    def get_app_list(self, request, app_label=None):
        """Customize the admin index for doctors"""
        app_list = super().get_app_list(request, app_label)
        
        if not request.user.is_superuser and hasattr(request.user, 'doctor_profile'):
            # Show only models doctors can access
            filtered_app_list = []
            for app in app_list:
                if app['app_label'] == 'health_linkr_app':
                    filtered_models = []
                    for model in app['models']:
                        if model['object_name'] in ['Appointment', 'ScheduleSlot', 'Service']:
                            # Check if user has any permissions for this model
                            model_admin = self._registry[model['model']]
                            if (model_admin.has_view_permission(request) or 
                                model_admin.has_change_permission(request) or 
                                model_admin.has_add_permission(request) or 
                                model_admin.has_delete_permission(request)):
                                filtered_models.append(model)
                    if filtered_models:
                        app['models'] = filtered_models
                        filtered_app_list.append(app)
            return filtered_app_list
            
        return app_list

# Replace the default admin site
admin.site = CustomAdminSite(name='customadmin')
admin.site.register(User, CustomUserAdmin)
admin.site.register(Role, RoleAdmin)
admin.site.register(PatientProfile, PatientProfileAdmin)
admin.site.register(DoctorProfile, DoctorProfileAdmin)
admin.site.register(Clinic, ClinicAdmin)
admin.site.register(Service, ServiceAdmin)
admin.site.register(ScheduleSlot, ScheduleSlotAdmin)
admin.site.register(Appointment, AppointmentAdmin)
admin.site.register(Notification, NotificationAdmin)
admin.site.register(SessionLog, SessionLogAdmin)
admin.site.register(AuditTrail, AuditTrailAdmin)
