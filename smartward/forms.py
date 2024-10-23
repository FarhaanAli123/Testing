from datetime import date, timedelta
from django.utils import timezone
from django import forms
from django.contrib.auth.forms import UserChangeForm
from .models import CustomUser, DoctorAppointment, DoctorAppointmentSlot, Patient, Shift, SpecializedAppointment, SpecializedAppointmentSlot, Visit
from django.core.exceptions import ValidationError
import pytz
import datetime


class ProfileUpdateForm(UserChangeForm):
    password = None  # Exclude the password field

    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'email', 'profile_picture']

class PatientForm(forms.ModelForm):
    dob = forms.DateField(
        widget=forms.DateInput(
            format='%d/%m/%Y',
            attrs={'placeholder': 'dd/mm/yyyy'}
        ),
        input_formats=['%d/%m/%Y']
    )

    class Meta:
        model = Patient
        fields = [
            'first_name', 
            'last_name', 
            'address', 
            'phone_contact', 
            'emergency_contact', 
            'dob', 
            'email', 
            'medical_conditions'
        ]
        widgets = {
            'first_name': forms.TextInput(attrs={'maxlength': 25}),
            'last_name': forms.TextInput(attrs={'maxlength': 25}),
            'phone_contact': forms.TextInput(attrs={'maxlength': 7}),
            'emergency_contact': forms.TextInput(attrs={'maxlength': 7}),
        }

    def clean_first_name(self):
        first_name = self.cleaned_data.get('first_name')
        if len(first_name) > 25:
            raise ValidationError('First name cannot exceed 25 characters.')
        return first_name

    def clean_last_name(self):
        last_name = self.cleaned_data.get('last_name')
        if len(last_name) > 25:
            raise ValidationError('Last name cannot exceed 25 characters.')
        return last_name

    def clean_dob(self):
        dob = self.cleaned_data.get('dob')
        today = date.today()

        if dob > today:
            raise ValidationError('Date of birth cannot be in the future.')

        # Calculate age
        age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))

        if age > 150:
            raise ValidationError('Age must be less than 150 years.')
        return dob

class ShiftForm(forms.ModelForm):
    start_time = forms.DateTimeField(
        label='Start Time',
        input_formats=['%d/%m/%Y %I:%M %p'],
        widget=forms.DateTimeInput(format='%d/%m/%Y %I:%M %p')
    )
    end_time = forms.DateTimeField(
        label='End Time',
        input_formats=['%d/%m/%Y %I:%M %p'],
        widget=forms.DateTimeInput(format='%d/%m/%Y %I:%M %p')
    )

    class Meta:
        model = Shift
        fields = ['doctor', 'start_time', 'end_time']

    def clean(self):
        cleaned_data = super().clean()
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')

        if start_time and end_time and start_time >= end_time:
            raise forms.ValidationError("End time must be after start time.")

        # Convert times to Fiji Time before further validation
        tz = pytz.timezone('Pacific/Fiji')
        if start_time and timezone.is_naive(start_time):
            cleaned_data['start_time'] = timezone.make_aware(start_time, tz)
        if end_time and timezone.is_naive(end_time):
            cleaned_data['end_time'] = timezone.make_aware(end_time, tz)

        return cleaned_data

class DoctorAppointmentSlotAdminForm(forms.ModelForm):
    class Meta:
        model = DoctorAppointmentSlot
        fields = ['doctor', 'date', 'start_time', 'end_time']
        widgets = {
            'date': forms.SelectDateWidget,
            'start_time': forms.TimeInput(attrs={'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'type': 'time'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')
        date = cleaned_data.get('date')

        if start_time is None or end_time is None:
            raise ValidationError("Both start time and end time must be specified.")

        if start_time >= end_time:
            raise ValidationError("End time must be after start time.")

        if date:
            now = timezone.localtime()
            slot_datetime = timezone.make_aware(
                timezone.datetime.combine(date, start_time),
                timezone.get_current_timezone()
            )
            if slot_datetime < now:
                raise ValidationError("The slot cannot be in the past.")
        
        slot_duration = timedelta(
            hours=end_time.hour - start_time.hour,
            minutes=end_time.minute - start_time.minute
        )
        max_duration = timedelta(minutes=30)

        if slot_duration > max_duration:
            raise ValidationError("The appointment slot duration cannot exceed 30 minutes.")

        return cleaned_data
    
    
class SpecializedAppointmentForm(forms.ModelForm):
    patient_id = forms.IntegerField(label='Patient ID', required=True)
    slot = forms.ModelChoiceField(
        queryset=SpecializedAppointmentSlot.objects.none(),
        label='Available Slots',
        widget=forms.Select
    )

    class Meta:
        model = SpecializedAppointment
        fields = ['patient_id', 'slot']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter slots that are only in the future and not already booked
        self.fields['slot'].queryset = SpecializedAppointmentSlot.objects.filter(
            date__gte=timezone.now().date()
        ).exclude(
            specializedappointment__isnull=False  # Exclude already booked slots
        )

    def clean_patient_id(self):
        patient_id = self.cleaned_data.get('patient_id')
        if not Patient.objects.filter(id=patient_id).exists():
            raise forms.ValidationError("No patient found with the provided ID.")
        return patient_id

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.patient = Patient.objects.get(id=self.cleaned_data['patient_id'])
        if commit:
            instance.save()
        return instance

class DoctorAppointmentForm(forms.ModelForm):
    class Meta:
        model = DoctorAppointment
        fields = ['patient', 'doctor', 'slot']  # Use the correct field names

    def clean(self):
        cleaned_data = super().clean()
        patient = cleaned_data.get('patient')
        doctor = cleaned_data.get('doctor')
        slot = cleaned_data.get('slot')

        if not slot:
            raise forms.ValidationError("Please select a valid slot.")

        now = timezone.localtime()  # Get current time in local timezone
        slot_start_datetime = timezone.make_aware(
            timezone.datetime.combine(timezone.localdate(), slot.start_time),
            timezone.get_current_timezone()
        )
        
        if slot_start_datetime <= now:
            raise forms.ValidationError("The selected slot is in the past. Please choose a future time.")

        return cleaned_data


class ReceptionistAppointmentForm(forms.ModelForm):
    patient_id = forms.IntegerField(label='Patient ID', required=True)

    class Meta:
        model = DoctorAppointment
        fields = ['patient_id', 'slot']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter slots that are only in the future and not already booked
        self.fields['slot'].queryset = DoctorAppointmentSlot.objects.filter(
            date__gte=timezone.now().date()
        ).exclude(
            doctorappointment__isnull=False  # Exclude already booked slots
        )

    def clean_patient_id(self):
        patient_id = self.cleaned_data.get('patient_id')
        if not Patient.objects.filter(id=patient_id).exists():
            raise forms.ValidationError("Patient with this ID does not exist.")
        return patient_id

    def save(self, commit=True):
        appointment = super().save(commit=False)
        appointment.patient_id = self.cleaned_data['patient_id']  # Set patient from patient_id
        appointment.doctor = self.cleaned_data['slot'].doctor  # Set doctor from the selected slot
        if commit:
            appointment.save()
        return appointment
    

class VisitForm(forms.ModelForm):
    class Meta:
        model = Visit
        fields = ['patient', 'doctor', 'weight', 'temperature', 'blood_pressure']
        widgets = {
            'patient': forms.HiddenInput(),  # We'll pass patient data directly
        }


class DoctorVisitForm(forms.ModelForm):
    class Meta:
        model = Visit
        fields = ['doctor_notes']  # Only allow the doctor to edit the doctor_notes field
        widgets = {
            'doctor_notes': forms.Textarea(attrs={'rows': 5, 'cols': 40}),
        }
