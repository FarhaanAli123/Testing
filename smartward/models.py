from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings
from django.forms import ValidationError
from django.utils import timezone
import pytz
from datetime import date

class CustomUser(AbstractUser):
    USER_TYPE_CHOICES = [
        ('doctor', 'Doctor'),
        ('nurse', 'Nurse'),
        ('receptionist', 'Receptionist'),
        ('admin', 'Admin'),
    ]
    
    id_number = models.CharField(max_length=20, unique=True)
    usertype = models.CharField(max_length=20, choices=USER_TYPE_CHOICES)
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['id_number', 'usertype']

    def __str__(self):
        return self.username

class Shift(models.Model):
    doctor = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE,
        limit_choices_to={'usertype': 'doctor'},
        related_name='shifts'
    )
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Shift for {self.doctor.username} from {self.get_start_time()} to {self.get_end_time()}"

    def is_active(self):
        """Return True if the shift is currently active."""
        now = timezone.localtime()  # Ensure timezone aware
        return self.start_time <= now <= self.end_time

    def get_start_time(self):
        """Return the formatted start time in local timezone."""
        return timezone.localtime(self.start_time).strftime("%d/%m/%Y %I:%M %p")

    def get_end_time(self):
        """Return the formatted end time in local timezone."""
        return timezone.localtime(self.end_time).strftime("%d/%m/%Y %I:%M %p")

class Patient(models.Model):
    first_name = models.CharField(max_length=25)
    last_name = models.CharField(max_length=25)
    address = models.TextField()
    phone_contact = models.CharField(max_length=7)
    emergency_contact = models.CharField(max_length=7)
    dob = models.DateField()
    email = models.EmailField(unique=True)
    medical_conditions = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

class SpecializedAppointmentType(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name

class SpecializedAppointmentSlot(models.Model):
    appointment_type = models.ForeignKey(SpecializedAppointmentType, on_delete=models.CASCADE, related_name='slots')
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()

    def __str__(self):
        return f"{self.appointment_type.name} on {self.date} from {self.get_start_time()} to {self.get_end_time()}"

    def is_booked(self):
        """Check if the appointment slot is booked."""
        return self.specializedappointment_set.exists()

    def get_start_time(self):
        """Return the formatted start time in local timezone."""
        return timezone.localtime(timezone.make_aware(timezone.datetime.combine(self.date, self.start_time))).strftime("%d/%m/%Y %I:%M %p")

    def get_end_time(self):
        """Return the formatted end time in local timezone."""
        return timezone.localtime(timezone.make_aware(timezone.datetime.combine(self.date, self.end_time))).strftime("%d/%m/%Y %I:%M %p")

class SpecializedAppointment(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    slot = models.ForeignKey(SpecializedAppointmentSlot, on_delete=models.CASCADE)
    booked_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Appointment for {self.patient} for {self.slot.appointment_type.name} on {self.slot.date} at {self.slot.get_start_time()}"

class DoctorAppointmentSlot(models.Model):
    doctor = models.ForeignKey(CustomUser, on_delete=models.CASCADE, limit_choices_to={'usertype': 'doctor'})
    date = models.DateField(default=date.today)
    start_time = models.TimeField()
    end_time = models.TimeField()

    def clean(self):
        """Ensure the end time is after the start time and is not in the past."""
        if self.start_time is None or self.end_time is None:
            raise ValidationError("Both start time and end time must be specified.")

        if self.start_time >= self.end_time:
            raise ValidationError("End time must be after start time.")

        now = timezone.localtime()
        slot_datetime = timezone.make_aware(
            timezone.datetime.combine(self.date, self.start_time),
            timezone.get_current_timezone()
        )
        if slot_datetime < now:
            raise ValidationError("The slot cannot be in the past.")
        
        # Validate that the slot is within the doctor's shift times
        shifts = Shift.objects.filter(doctor=self.doctor)

        if not shifts.exists():
            raise ValidationError("The doctor does not have any shifts defined.")

        # Check if the slot falls within any active shift
        is_valid_slot = False
        for shift in shifts:
            if (shift.start_time <= slot_datetime < shift.end_time) and \
               (shift.start_time < timezone.make_aware(
                   timezone.datetime.combine(self.date, self.end_time),
                   timezone.get_current_timezone()) <= shift.end_time):
                is_valid_slot = True
                break

        if not is_valid_slot:
            raise ValidationError("The slot must be within the doctor's shift time.")

    def __str__(self):
        return f"Slot on {self.date} from {self.start_time} to {self.end_time} for {self.doctor.username}"



class DoctorAppointment(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    doctor = models.ForeignKey(CustomUser, on_delete=models.CASCADE, limit_choices_to={'usertype': 'doctor'})
    slot = models.ForeignKey(DoctorAppointmentSlot, on_delete=models.CASCADE)
    booked_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Appointment for {self.patient.first_name} {self.patient.last_name} with {self.doctor.username} on {self.slot.start_time}"




class Visit(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    doctor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, limit_choices_to={'usertype': 'doctor'}, related_name='doctor_visits', default=1)
    nurse = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, limit_choices_to={'usertype': 'nurse'}, related_name='nurse_visits', default=1)
    visit_date = models.DateTimeField(default=timezone.now)
    weight = models.DecimalField(max_digits=5, decimal_places=2, help_text="Enter weight in kg", null=True)
    temperature = models.DecimalField(max_digits=4, decimal_places=1, help_text="Enter temperature in °C", default=36.6)
    blood_pressure = models.CharField(max_length=7, help_text="Enter blood pressure in format: Systolic/Diastolic", default="120/80")
    doctor_notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Visit for {self.patient} on {self.visit_date.strftime('%d/%m/%Y')} by Nurse {self.nurse.username}"
