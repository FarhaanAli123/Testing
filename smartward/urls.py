from django.urls import path
from .views import (
    create_visit,
    doctor_attend_visit,
    doctor_view_visits,
    edit_profile,
    logout_view,
    patient_visit_list,
    user_login,
    doctor_dashboard_view,
    nurse_dashboard_view,
    receptionist_dashboard_view,
    home,
    doctor_profile_view,
    doctor_appointments_view,
    add_patient_view,
    patient_list_view,
    delete_doctor_appointment,
    update_patient_view,
    #delete_patient_view,
    patient_detail_view,
    book_specialized_appointment,
    specialized_appointment_list,
    delete_specialized_appointment,
    print_appointment_view,
    appointment_success,
    receptionist_book_appointment,
    print_special_appointment_view
)

urlpatterns = [
    path('login/', user_login, name='login'),
    path('', home, name='home'),

    # Dashboard URLs
    path('doctor_dashboard/', doctor_dashboard_view, name='doctor_dashboard'),
    path('nurse_dashboard/', nurse_dashboard_view, name='nurse_dashboard'),
    path('receptionist_dashboard/', receptionist_dashboard_view, name='receptionist_dashboard'),
    path('logout/', logout_view, name='logout'),

    # Profile URLs
    path('doctor_profile/', doctor_profile_view, name='doctor_profile'),
    path('edit-profile/', edit_profile, name='edit_profile'),

    # Appointment URLs
    path('book-appointment/', receptionist_book_appointment, name='book_appointment'),
    path('appointment-success/', appointment_success, name='appointment_success'),
    path('doctor_appointments/', doctor_appointments_view, name='doctor_appointments'),
    path('delete-appointment/<int:appointment_id>/', delete_doctor_appointment, name='delete_doctor_appointment'),
    path('book/<int:appointment_type_id>/', book_specialized_appointment, name='book_specialized_appointment'),
    path('specialized-appointments/', specialized_appointment_list, name='specialized_appointment_list'),
    path('delete_specialized_appointment/<int:appointment_id>/', delete_specialized_appointment, name='delete_specialized_appointment'),
    path('appointment/<int:appointment_id>/print/', print_appointment_view, name='print_appointment'),
    path('special_app/<int:appointment_id>/print/',print_special_appointment_view, name='sp_print_appointment'),


    # Patient Management URLs
    path('patients/add/', add_patient_view, name='add_patient'),
    path('patients/', patient_list_view, name='patient_list'),
    path('patient/update/<int:patient_id>/', update_patient_view, name='update_patient'),
#    path('patient/delete/<int:patient_id>/', delete_patient_view, name='delete_patient'),
    path('patients/<int:patient_id>/', patient_detail_view, name='patient_detail'),

    path('visit_list', patient_visit_list, name='patient_visit_list'),
    path('patients/<int:patient_id>/create-visit/', create_visit, name='create_visit'),
    path('doctor/view-visits/', doctor_view_visits, name='doctor_view_visits'),
    path('doctor/attend_visit/<int:visit_id>/', doctor_attend_visit, name='doctor_attend_visit'),
]
