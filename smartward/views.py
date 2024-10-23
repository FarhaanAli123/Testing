from datetime import timedelta
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import  DoctorAppointment, DoctorAppointmentSlot, Patient, Shift, SpecializedAppointment, SpecializedAppointmentSlot, SpecializedAppointmentType, Visit
from .forms import  DoctorVisitForm, PatientForm, ProfileUpdateForm, ReceptionistAppointmentForm, SpecializedAppointmentForm, VisitForm
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.db.models import Q
import difflib
from django.template.loader import get_template
from xhtml2pdf import pisa
from django.utils import timezone
from django.contrib.auth.forms import PasswordChangeForm


def home(request):
    return render(request, 'home.html')


def user_login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            if user.usertype == 'doctor':
                return redirect('doctor_dashboard') 
            elif user.usertype == 'nurse':
                return redirect('nurse_dashboard')  
            elif user.usertype == 'receptionist':
                return redirect('receptionist_dashboard')  
        else:
            messages.error(request, 'Invalid username or password.')
    
    return render(request, 'login.html')


@login_required
def doctor_dashboard_view(request):
    user = request.user
    now = timezone.now()
    shifts = Shift.objects.filter(doctor=user, start_time__gt=now).order_by('start_time')
    return render(request, 'doctor_dashboard.html', {'user': user, 'shifts': shifts})

@login_required
def nurse_dashboard_view(request):
    user = request.user
    return render(request, 'nurse_dashboard.html', {'user': user})


@login_required
def receptionist_dashboard_view(request):
    user = request.user

    if user.usertype != 'receptionist':
        return redirect('home')

    doctors_shifts = Shift.objects.filter(doctor__usertype='doctor')
    return render(request, 'receptionist_dashboard.html', {
        'user': user,
        'doctors_shifts': doctors_shifts,
    })


from django.contrib.auth.decorators import user_passes_test


@user_passes_test(lambda u: u.usertype == 'receptionist')  
def receptionist_book_appointment(request):
    upcoming_bookings = DoctorAppointment.objects.filter(
        slot__date__gte=timezone.now().date()  # Fetch upcoming bookings
    ).select_related('patient', 'doctor', 'slot').order_by('slot__date')  # Optimize queries
    if request.method == "POST":
        form = ReceptionistAppointmentForm(request.POST)
        if form.is_valid():
            form.save()  # Save the appointment
            messages.success(request, 'Booking Successful.')
            return redirect('book_appointment')
        else:
            messages.error(request, "Booking Unsuccessful")
    else:
        form = ReceptionistAppointmentForm()

    return render(request, 'appointment_booking.html',
                {'form': form,
                'upcoming_bookings': upcoming_bookings})


@login_required
def doctor_profile_view(request):
    user = request.user

    if request.method == 'POST':
        profile_form = ProfileUpdateForm(request.POST, request.FILES, instance=user)
        password_form = PasswordChangeForm(user, request.POST)

        if profile_form.is_valid():
            profile_form.save()
            messages.success(request, 'Your profile has been updated successfully.')

        if password_form.is_valid():
            user = password_form.save()
            update_session_auth_hash(request, user)  # Important to keep the user logged in
            messages.success(request, 'Your password was updated successfully.')
            return redirect('doctor_profile')

    else:
        profile_form = ProfileUpdateForm(instance=user)
        password_form = PasswordChangeForm(user)

    return render(request, 'doctor_profile.html', {
        'user': user,
        'profile_form': profile_form,
        'password_form': password_form
    })


@login_required
def doctor_appointments_view(request):
    user = request.user

    if user.usertype != 'doctor':
        return redirect('home')


    now = timezone.now()
    threshold_time = now - timedelta(minutes=10)

    # Filter appointments to include only those that are scheduled in the future
    appointments = DoctorAppointment.objects.filter(
        doctor=user, 
    ).select_related('patient', 'slot').exclude(
        slot__end_time__lt=threshold_time.time()  # Exclude bookings that have ended more than 10 minutes ago
    )
    return render(request, 'doctor_appointments.html', {
        'appointments': appointments,
    })


def add_patient_view(request):
    if request.method == 'POST':
        form = PatientForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Patient added successfully.')
            return redirect('patient_list')
        else:
            messages.error(request, 'There was an error adding the patient.')
    else:
        form = PatientForm()

    return render(request, 'add_patient.html', {'form': form})


def patient_list_view(request):
    query = request.GET.get('q', '').strip()
    patients = Patient.objects.all()
    suggested_query = None

    if query:
        patients = patients.filter(
            Q(id__icontains=query) |
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(email__icontains=query) |
            Q(phone_contact__icontains=query) |
            Q(emergency_contact__icontains=query)
        )

        if not patients.exists():
            all_names = list(Patient.objects.values_list('first_name', flat=True)) + \
                        list(Patient.objects.values_list('last_name', flat=True))
            close_matches = difflib.get_close_matches(query, all_names, n=1, cutoff=0.6)

            if close_matches:
                suggested_query = close_matches[0]

    return render(request, 'patient_list.html', {
        'patients': patients,
        'query': query,
        'suggested_query': suggested_query
    })


@login_required
def delete_doctor_appointment(request, appointment_id):
    appointment = get_object_or_404(DoctorAppointment, id=appointment_id)

    if request.method == 'POST':
        appointment.delete()
        messages.success(request, "Appointment cancelled successfully.")
        return redirect('book_appointment')

    messages.error(request, "Unable to cancel appointment.")
    return redirect('book_appointment')


def update_patient_view(request, patient_id):
    patient = get_object_or_404(Patient, pk=patient_id)
    if request.method == 'POST':
        form = PatientForm(request.POST, instance=patient)
        if form.is_valid():
            form.save()
            messages.success(request, 'Patient updated successfully.')
            return redirect('patient_list')  
    else:
        form = PatientForm(instance=patient)
    
    return render(request, 'update_patient.html', {'form': form, 'patient': patient})


# def delete_patient_view(request, patient_id):
#     patient = get_object_or_404(Patient, pk=patient_id)
#     if request.method == 'POST':
#         patient.delete()
#         messages.success(request, 'Patient deleted successfully.')
#         return redirect('patient_list') 
    
#     return render(request, 'confirm_delete.html', {'patient': patient})


def patient_detail_view(request, patient_id):
    patient = get_object_or_404(Patient, id=patient_id)
    return render(request, 'patient_detail.html', {'patient': patient})


def book_specialized_appointment(request, appointment_type_id):
    appointment_type = get_object_or_404(SpecializedAppointmentType, id=appointment_type_id)
    available_slots = SpecializedAppointmentSlot.objects.filter(appointment_type=appointment_type, specializedappointment__isnull=True)
    
    if request.method == 'POST':
        form = SpecializedAppointmentForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Appointment booked successfully!')
            return redirect('specialized_appointment_list')
    else:
        form = SpecializedAppointmentForm(initial={'appointment_type': appointment_type})
    
    context = {
        'form': form,
        'available_slots': available_slots,
        'appointment_type': appointment_type,
    }
    return render(request, 'book_specialized_appointment.html', context)



def specialized_appointment_list(request):
    appointment_types = SpecializedAppointmentType.objects.all()
    now = timezone.now()

    # Calculate the time threshold for hiding past bookings (10 minutes after the end time)
    threshold_time = now - timedelta(minutes=10)

    # Filter to show only future bookings or bookings that ended within the last 10 minutes
    specialbookings = SpecializedAppointment.objects.filter(
        slot__date__gte=now.date()
    ).exclude(
        slot__end_time__lt=threshold_time.time()  # Exclude bookings that have ended more than 10 minutes ago
    )

    return render(request, 'specialized_appointment_list.html', {
        'appointment_types': appointment_types,
        'specialbookings': specialbookings
    })


def delete_specialized_appointment(request, appointment_id):
    appointment = get_object_or_404(SpecializedAppointment, id=appointment_id)
    
    if request.method == 'POST':
        appointment.delete()
        messages.success(request, 'Appointment deleted successfully!')
        return redirect('specialized_appointment_list')

    return render(request, 'confirm_delete_specialized_appointment.html', {'appointment': appointment})


def logout_view(request):
    logout(request)
    messages.success(request, "You have been logged out successfully.")
    return redirect('home')


def print_appointment_view(request, appointment_id):
    appointment = get_object_or_404(DoctorAppointment, id=appointment_id)

    template = get_template('appointment_pdf_template.html')
    html = template.render({'appointment': appointment})

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="appointment_{appointment.id}.pdf"'

    # Using xhtml2pdf to create the PDF
    pisa_status = pisa.CreatePDF(html, dest=response)
    if pisa_status.err:
        return HttpResponse(f'Error generating PDF: {pisa_status.err}')

    return response


def appointment_success(request):
    return render(request, 'appointment_success.html')



def patient_visit_list(request):
    patients = Patient.objects.all()
    query = request.GET.get('q')
    suggested_query = None

    if query:
        try:
            query_id = int(query)
            # If query is numeric, filter patients by exact ID match
            patients = patients.filter(Q(id=query_id))
        except ValueError:
            # If query is not numeric, filter by name or contact
            patients = patients.filter(
                Q(first_name__icontains=query) |
                Q(last_name__icontains=query) |
                Q(phone_contact__icontains=query)
            )
        if not patients.exists():
            all_names = list(Patient.objects.values_list('first_name', flat=True)) + \
                        list(Patient.objects.values_list('last_name', flat=True))
            close_matches = difflib.get_close_matches(query, all_names, n=1, cutoff=0.6)

            if close_matches:
                suggested_query = close_matches[0]

    return render(request, 'patient_visit_list.html', {'patients': patients, 'query': query, 'suggested_query':suggested_query})

# Create a new visit for a selected patient
def create_visit(request, patient_id):
    patient = get_object_or_404(Patient, id=patient_id)
    
    if request.method == 'POST':
        form = VisitForm(request.POST)
        if form.is_valid():
            visit = form.save(commit=False)
            visit.nurse = request.user  # Set the nurse as the logged-in user
            visit.save()
            messages.success(request, 'Visit created successfully!')
            return redirect('patient_visit_list')
        else:
            messages.error(request, 'Error creating visit.')
    else:
        form = VisitForm(initial={'patient': patient})

    return render(request, 'create_visit.html', {'form': form, 'patient': patient})



@login_required
def doctor_view_visits(request):
    query = request.GET.get('q')
    visits = Visit.objects.filter(doctor=request.user).order_by('-visit_date')
    suggested_query = None  # Initialize suggested_query to None

    if query:
        try:
            query_id = int(query)
            # Exact ID match for patient
            visits = visits.filter(Q(patient__id=query_id))
        except ValueError:
            # If the query is not numeric, search by patient first name, last name, or phone contact
            visits = visits.filter(
                Q(patient__first_name__icontains=query) |
                Q(patient__last_name__icontains=query) |
                Q(patient__phone_contact__icontains=query)
            )

        if not visits.exists():
            all_names = list(Patient.objects.values_list('first_name', flat=True)) + \
                        list(Patient.objects.values_list('last_name', flat=True))
            close_matches = difflib.get_close_matches(query, all_names, n=1, cutoff=0.6)

            if close_matches:
                suggested_query = close_matches[0]

    return render(request, 'doctor_view_visits.html', {
        'visits': visits,
        'query': query,
        'suggested_query': suggested_query
    })


@login_required
def doctor_attend_visit(request, visit_id):
    visit = get_object_or_404(Visit, id=visit_id, doctor=request.user)

    if request.method == 'POST':
        form = DoctorVisitForm(request.POST, instance=visit)
        if form.is_valid():
            form.save()
            return redirect('doctor_view_visits')
    else:
        form = DoctorVisitForm(instance=visit)

    return render(request, 'doctor_attend_visit.html', {'form': form, 'visit': visit})


def edit_profile(request):
    user = request.user  # Fetch the current logged-in user

    if request.method == 'POST':
        # Check if the user is submitting the profile form
        if 'clear_profile_picture' in request.POST:
            if user.profile_picture:
                user.profile_picture.delete(save=False)  # Delete the file from storage
            user.profile_picture = None  # Clear the image reference
            user.save()
            messages.success(request, 'Your profile picture has been cleared successfully.')
            return redirect('edit_profile')  # Redirect to the same page or wherever appropriate

        # Check if the user is submitting the profile form
        if 'profile_form' in request.POST:
            profile_form = ProfileUpdateForm(request.POST, request.FILES, instance=user)
            if profile_form.is_valid():
                profile_form.save()
                messages.success(request, 'Your profile has been updated successfully.')
        
        # Check if the user is submitting the password change form
        if 'password_form' in request.POST:
            password_form = PasswordChangeForm(user, request.POST)
            if password_form.is_valid():
                user = password_form.save()
                update_session_auth_hash(request, user)  # Keep user logged in after password change
                messages.success(request, 'Your password was updated successfully.')
            else:
                messages.error(request, 'Please correct the errors in your password form.')

        # Redirect based on usertype
        if user.usertype == 'doctor':
            return redirect('doctor_dashboard')
        elif user.usertype == 'nurse':
            return redirect('nurse_dashboard')
        elif user.usertype == 'receptionist':
            return redirect('receptionist_dashboard')
        else:
            return redirect('home')  # Fallback in case no usertype is matched

    else:
        # Load the forms with existing data when the request is GET
        profile_form = ProfileUpdateForm(instance=user)
        password_form = PasswordChangeForm(user)

    # Render the template with both forms
    return render(request, 'profile_edit.html', {
        'profile_form': profile_form,
        'password_form': password_form,
    })


def print_special_appointment_view(request, appointment_id):
    appointment = get_object_or_404(SpecializedAppointment, id=appointment_id)

    template = get_template('sp_Appointment_pdf_template.html')
    html = template.render({'appointment': appointment})

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="appointment_{appointment.id}.pdf"'

    # Using xhtml2pdf to create the PDF
    pisa_status = pisa.CreatePDF(html, dest=response)
    if pisa_status.err:
        return HttpResponse(f'Error generating PDF: {pisa_status.err}')

    return response


from celery import shared_task

@shared_task
def delete_expired_appointments():
    now = timezone.now()
    ten_minutes_ago = now - timedelta(minutes=10)

    # Find and delete all appointments where the time slot has passed by more than 10 minutes
    expired_appointments = DoctorAppointment.objects.filter(slot__end_time__lte=ten_minutes_ago)
    expired_appointments.delete()


@shared_task
def delete_expired_slots():
    now = timezone.now()
    
    # Query for all slots that have passed the end time by 10 minutes
    expired_slots = DoctorAppointmentSlot.objects.filter(
        date__lt=now.date()
    ) | DoctorAppointmentSlot.objects.filter(
        date=now.date(),
        end_time__lte=(now - timedelta(minutes=10)).time()
    )
    
    count = expired_slots.count()
    expired_slots.delete()
    return f"Deleted {count} expired slots."