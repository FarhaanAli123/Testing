from django.contrib import admin

from smartward.forms import DoctorAppointmentSlotAdminForm
from .models import CustomUser, DoctorAppointment, DoctorAppointmentSlot, Shift
from django.contrib.auth.admin import UserAdmin
from django.utils import timezone

class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ['username', 'email', 'id_number', 'usertype', 'is_staff']
    list_filter = ['is_staff', 'is_active', 'usertype']
    fieldsets = UserAdmin.fieldsets + (
        (None, {'fields': ('id_number', 'usertype')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        (None, {'fields': ('id_number', 'usertype')}),
    )

admin.site.register(CustomUser, CustomUserAdmin)

@admin.register(Shift)
class ShiftAdmin(admin.ModelAdmin):
    list_display = ('doctor', 'formatted_start_time', 'formatted_end_time')
    search_fields = ('doctor__username', 'doctor__id_number')

    def formatted_start_time(self, obj):
        # Use timezone aware start time
        local_time = timezone.localtime(obj.start_time)
        return local_time.strftime("%d/%m/%Y %I:%M %p")
    formatted_start_time.short_description = 'Start Time'

    def formatted_end_time(self, obj):
        # Use timezone aware end time
        local_time = timezone.localtime(obj.end_time)
        return local_time.strftime("%d/%m/%Y %I:%M %p")
    formatted_end_time.short_description = 'End Time'

    def get_form(self, request, obj=None, **kwargs):
        # Customize the form to only show doctors with usertype 'doctor'
        form = super().get_form(request, obj, **kwargs)
        form.base_fields['doctor'].queryset = CustomUser.objects.filter(usertype='doctor')
        return form

from .models import SpecializedAppointmentType, SpecializedAppointmentSlot, Patient, SpecializedAppointment

@admin.register(SpecializedAppointmentType)
class SpecializedAppointmentTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'description']
    search_fields = ['name']

@admin.register(SpecializedAppointmentSlot)
class SpecializedAppointmentSlotAdmin(admin.ModelAdmin):
    list_display = ['appointment_type', 'formatted_date', 'get_start_time', 'get_end_time']
    list_filter = ['appointment_type', 'date']
    search_fields = ['appointment_type__name', 'date']

    def formatted_date(self, obj):
        return obj.date.strftime("%d/%m/%Y")
    formatted_date.short_description = 'Date'

    def get_start_time(self, obj):
        local_time = timezone.localtime(obj.start_time)
        return local_time.strftime("%I:%M %p")  # Assuming start_time is a datetime field
    get_start_time.short_description = 'Start Time'

    def get_end_time(self, obj):
        local_time = timezone.localtime(obj.end_time)
        return local_time.strftime("%I:%M %p")  # Assuming end_time is a datetime field
    get_end_time.short_description = 'End Time'

@admin.register(SpecializedAppointment)
class SpecializedAppointmentAdmin(admin.ModelAdmin):
    list_display = ['patient', 'slot', 'booked_at']
    list_filter = ['slot__appointment_type', 'slot__date']
    search_fields = ['patient__first_name', 'patient__last_name', 'slot__appointment_type__name']

@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ['first_name', 'last_name', 'email', 'phone_contact']
    search_fields = ['first_name', 'last_name', 'email']

@admin.register(DoctorAppointmentSlot)
class DoctorAppointmentSlotAdmin(admin.ModelAdmin):
    form = DoctorAppointmentSlotAdminForm
    list_display = ['doctor', 'date', 'start_time', 'end_time']
    search_fields = ['doctor__username', 'date']

@admin.register(DoctorAppointment)
class DoctorAppointmentAdmin(admin.ModelAdmin):
    list_display = ['patient', 'doctor', 'slot', 'booked_at']
    list_filter = ['doctor', 'slot']

    def booked_at(self, obj):
        local_time = timezone.localtime(obj.booked_at)
        return local_time.strftime("%d/%m/%Y %I:%M %p")
    booked_at.admin_order_field = 'booked_at'
    booked_at.short_description = 'Booked At'
