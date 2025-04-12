from django.urls import path
from . import views
from availablity.views import datess,date_selector, get_slots,book_the_slot

urlpatterns = [
    # Existing Routes
    path('slots/', views.available_slots, name='available_slots'),
    path('slot/book/', views.book_slot, name='book_slot'),
    path('otp/send/', views.send_otp_email, name='send_otp'),
    path('otp/verify/', views.verify_otp_view, name='verify_otp_patient'),

    # New Routes
    path('appointments/', views.view_appointments, name='view_appointments'),
    path('cancel/<int:appointment_id>/', views.cancel_appointment, name='cancel_appointment'),
    path('add-dentist/', views.add_dentist, name='add_dentist'),
    
    path('staff/login/', views.staff_login_view, name='staff_login'),
    path('staff/dashboard/', views.staff_dashboard_view, name='staff_dashboard'),
    path('staff/view-appointments/', views.view_appointments, name='view_appointments'),
    path('staff/logout/', views.staff_logout_view, name='staff_logout'),
    path('cancel/email/', views.getting_the_email_of_the_patient, name='get_patient_email'),
    path('cancel/verify-otp/', views.verify_otp_view_for_cancellation, name='verify_otp_for_cancelation'),
    path('cancel/appointment/', views.by_patient_canellation, name='cancel_appointment'),
    path('appointment/details/', views.show_Details, name='show_appointment_details'),
    
    path('appointments_/date-selector/', date_selector, name='date_selector'),
    path('select-date/', datess, name='date_selection'),
    
    
    path('select-date/', datess, name='select_date'),
    path('date-selector/<str:selected_date>/', date_selector, name='date_selector'),
    path('get-slots/', get_slots, name='get_slots'),
    path('book/<int:dentist_id>/<str:start_time>/<str:end_time>/<str:date>/<int:booked_appointments>/', book_the_slot, name='book_the_slot'),

]
    

