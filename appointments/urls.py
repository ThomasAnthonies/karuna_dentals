from django.urls import path
from . import views

urlpatterns = [
    # Existing Routes
    path('slots/', views.available_slots, name='available_slots'),
    path('slot/<int:slot_id>/', views.get_slot_details, name='slot_details'),
    path('slot/<int:slot_id>/book/', views.book_slot, name='book_slot'),
    path('otp/send/', views.send_otp_email, name='send_otp'),
    path('otp/verify/', views.verify_otp_view, name='verify_otp'),
    path('book_appointment/<int:slot_id>/', views.book_slot, name='book_appointment_page'),

    # New Routes
    path('appointments/', views.view_appointments, name='view_appointments'),
    path('cancel/<int:appointment_id>/', views.cancel_appointment, name='cancel_appointment'),
    path('add-dentist/', views.add_dentist, name='add_dentist'),
    
    path('staff/login/', views.staff_login_view, name='staff_login'),
    path('staff/dashboard/', views.staff_dashboard_view, name='staff_dashboard'),
    path('staff/view-appointments/', views.view_appointments, name='view_appointments'),
    
]

