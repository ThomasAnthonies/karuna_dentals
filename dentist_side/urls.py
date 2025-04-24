from django.urls import path
from . import views

urlpatterns = [
    # Doctor Authentication & Session
    path('doctor/login/', views.doctor_login, name='doctor_login'),
    path('doctor/logout/', views.doctor_logout, name='doctor_logout'),
    path('doctor/dashboard/', views.all_patients_visited, name='doctor_dashboard'),

    # OTP-based login creation
    path('doctor/send-otp/', views.send_otp_email, name='send_otp_email'),
    path('doctor/verify-otp/', views.verify_otp_view, name='verify_otp'),
    path('doctor/create-login/', views.doctor_login_creation, name='doctor_login_creation'),

    # Follow-Up and Patient Records
    path('doctor/followup/<int:patient_id>/<str:date>', views.put_the_patient_record, name='put_the_patient_record'),
    path('doctor/records/<int:patient_id>/', views.follow_up_records, name='follow_up_records'),
    path('doctor/patients-records/', views.patients_records, name='patients_records'),

    # Walk-in Patients
    path('doctor/walkins/', views.walk_ins, name='walkins'),
    path('doctor/walkins/new-form/', views.create_new_form, name='create_new_form'),
    path('doctor/walkins/follow-up-details/', views.create_walkin_follow_ups_details, name='walkin_follow_up'),

    # Optional: if you want a **separate** view-only page for follow-up records of walk-in patients
    path('doctor/walkins/follow-up-records/<int:patient_id>/', views.follow_up_records, name='walkin_follow_up_records'),
   
    path('doctor/home/', views.home_go, name='doctor_home'),
    path('patients/', views.all_patients_visited_from_start, name='patients_visited'),
    path('patients/<int:patient_id>/followups/', views.all_patients_visited_s_selected_patients_followups, name='patient_followups'),
    path('patients/<int:patient_id>/add_followup/', views.patient_visit_repeat_followups, name='add_followup'),
    path('appointments/all/', views.all_patients_from_past_and_future, name='all_appointments'),
    path('temporary-patient/followup/<int:patient_id>/', views.temporary_patients_followup, name='put_the_temporary_patient_record'),

]
