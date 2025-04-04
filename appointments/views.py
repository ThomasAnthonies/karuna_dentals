
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
import logging
from datetime import datetime
import random
from django.urls import reverse

from .models import Dentist, Appointment, OTP, Patient, available_timmings
from .utils import generate_otp,  send_email_notification


logger = logging.getLogger(__name__)

def get_slot_details(request, slot_id):
    slot = get_object_or_404(available_timmings, id=slot_id)
    request.session['slot_id'] = slot_id  # Store the slot ID in the session for later use
    request.session['dentist_'] = slot.dentist.name  # Store the dentist ID in the session for later use
    request.session['start_time'] = str(slot.start_time  )
    request.session['endtime']=str(slot.end_time)

   
    return render(request, 'slot_details.html', {
        'slot': slot,
        'dentist': slot.dentist,
        'start_time': slot.start_time,
        'end_time': slot.end_time,
        'maximum_people': slot.booked_appointments       
    })

def available_slots(request):
    """
    Displays available and unavailable slots.
    """
    dentists = Dentist.objects.all()
    slots = available_timmings.objects.all()
    slots_available = [slot for slot in slots if slot.is_available()]
    slots_not_available = [slot for slot in slots if not slot.is_available()]
    return render(request, 'available_slots.html', {
        'slots_available': slots_available,
        'slots_not_available': slots_not_available,
        'dentists': dentists
    })
    


from django.views.decorators.csrf import csrf_exempt  # Optional, only if you're testing without CSRF token

def generate_otp():
    return str(random.randint(100000, 999999))  # Generates a 6-digit OTP

def send_otp_email(request):
    if request.method == "POST":
        email = request.POST.get("email")  # ✅ Fetch the email from POST data
        slot_id = request.POST.get("slot_id")  # Optional: if you want to store/use this too

        # Clean old OTPs
        OTP.objects.filter(email=email).delete()

        # Generate and save new OTP
        otp_code = generate_otp()
        OTP.objects.create(email=email, otp=otp_code)

        # ✅ Save email in session
        request.session['otp_email'] = email

        # Send email
        send_mail(
            'Your OTP Code',
            f'Your OTP code is {otp_code}. It is valid for 5 minutes.',
            'yourclinic@example.com',
            [email],
            fail_silently=False,
        )

        logger.info(f'OTP sent to {email}')
        logger.info(f'OTP sent to {email}')
        return redirect('verify_otp')  # <-- this should match the URL name in urls.py

    else:
        return HttpResponse("Invalid request", status=400)

    

def verify_otp_view(request):
    if request.method == 'POST':
        email = request.session.get('otp_email')
        otp_input = request.POST.get('otp')

        if  not otp_input:
            return HttpResponse("Email and OTP are required.", status=400)

        attempts = request.session.get('otp_attempts', 0)
        if attempts >= 4:
            return HttpResponse("Maximum OTP attempts reached.", status=403)

        request.session['otp_attempts'] = attempts + 1

        try:
            otp_record = OTP.objects.filter(email=email, otp=otp_input).latest('created_at')
            if otp_record.is_verified:
                return HttpResponse("OTP already verified.", status=400)
            if otp_record.expired():
                return HttpResponse("OTP expired.", status=400)

            otp_record.is_verified = True
            otp_record.save()
            request.session['otp_verified'] = True

            # Redirect user to book the slot after verification
            return render(request, 'book_slot.html', {'slot_id': request.session.get('slot_id')})

        except OTP.DoesNotExist:
            return HttpResponse("Invalid OTP.", status=400)

    return render(request, 'verify_otp.html', {
    'otp_email': request.session.get('otp_email'),
    'slot_id': request.session.get('slot_id')
})


from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.contrib import messages
from django.urls import reverse
from django.db import IntegrityError
from datetime import datetime

from .models import Patient, Appointment, Dentist, available_timmings
from .utils import send_email_notification  # Assuming you have this defined

def book_slot(request, slot_id):
    """
    Books an appointment if the OTP has been verified. Clears the OTP verification flag after booking.
    """
    # Ensure OTP is verified before booking
    if not request.session.get('otp_verified', False):
        messages.error(request, "OTP not verified. Please verify your email before booking.") 
        return render(request, 'available_slots.html')

    if request.method == 'POST':
        # Validate slot
        slot = get_object_or_404(available_timmings, id=slot_id)

        # Check if email already exists
        if Patient.objects.filter(email=request.session.get('otp_email')).exists():
            return HttpResponse("Patient with the same email already exists.", status=400)

        # Validate required form fields
        required_fields = ['name', 'phone', 'date_of_birth']
        if not all(request.POST.get(field) for field in required_fields):
            return HttpResponse("Missing required fields", status=400)

        # Try to create a new patient record
        try:
            new_patient = Patient.objects.create(
                name=request.POST.get('name'),
                email=request.session.get('otp_email'),  # Use the verified email
                phone=request.POST.get('phone'),
                address=request.POST.get('address', ''),  # Optional field
                date_of_birth=request.POST.get('date_of_birth')
            )
        except IntegrityError as e:
            if 'phone' in str(e):
                messages.error(request, "The phone number is already registered. Please use a different number.")
                # Re-render form with old data to improve user experience
                context = {
                    'slot_id': slot_id,
                    'name': request.POST.get('name'),
                    'email': request.session.get('otp_email'),
                    'address': request.POST.get('address', ''),
                    'date_of_birth': request.POST.get('date_of_birth'),
                    'phone': request.POST.get('phone'),
                }
                return render(request, 'available_slots.html', context)
            else:
                return HttpResponse("An error occurred while creating patient.", status=500)

        # Fetch dentist from session
        dentist_name = request.session.get('dentist_')
        try:
            dentist = Dentist.objects.get(name=dentist_name)
        except Dentist.DoesNotExist:
            return HttpResponse("Dentist not found.", status=404)

        # Create the appointment
        appointment = Appointment.objects.create(
            patient=new_patient,
            date=request.POST.get('date'),
            from_time=datetime.strptime(request.session.get('start_time'), '%H:%M:%S'),
            to_time=datetime.strptime(request.session.get('endtime'), '%H:%M:%S'),
            status='scheduled',
            notes=request.POST.get('notes', ''),
            appointed_doctor=dentist,
            appointment_type=request.POST.get('appointment_type', 'general')
        )

        # Send confirmation email (with error handling)
        try:
            send_email_notification(
                new_patient.email,
                appointment.date,
                appointment.from_time,
                appointment.to_time,
                appointment.appointed_doctor
            )
        except Exception as e:
            print(f"Email failed: {e}")

        # Clear the OTP verification flag
        request.session['otp_verified'] = False
        messages.success(request, "Appointment booked successfully!")
        return redirect(reverse('available_slots'))

    return HttpResponse("Invalid request method", status=405)



def book_appointment_page(request, slot_id):
    if not request.session.get('otp_verified', False):
        return HttpResponse("Please verify OTP before booking.", status=403)

    # Get the slot object
    slot = get_object_or_404(available_timmings, id=slot_id)

    return render(request, 'book_slot.html', {'slot_id': slot_id, 'slot': slot})


def view_appointments(request):
    """Display all scheduled appointments."""
    appointments = Appointment.objects.filter(status="scheduled").order_by("date", "from_time")
    return render(request, "view_appointments.html", {"appointments": appointments})


def cancel_appointment(request, appointment_id):
    """Cancel an appointment and send an email notification to the patient."""
    appointment = get_object_or_404(Appointment, id=appointment_id)

    if request.method == "POST":
        reason = request.POST.get("cancellation_reason", "No reason provided")
        appointment.status = "canceled"
        appointment.cancellation_reason = reason
        appointment.save()

        # Send cancellation email to the patient
        if appointment.patient.email:
            send_mail(
                subject="Appointment Cancellation Notice",
                message=f"Dear {appointment.patient.name},\n\nYour appointment on {appointment.date} has been canceled.\nReason: {reason}\n\nSorry for the inconvenience.",
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=[appointment.patient.email],
                fail_silently=False,
            )

        messages.success(request, "Appointment has been canceled, and an email notification was sent.")
        return redirect("view_appointments")

    return render(request, "cancel_appointment.html", {"appointment": appointment})


def add_dentist(request):
    """Add a new dentist to the system."""
    if request.method == "POST":
        name = request.POST.get("name")
        email = request.POST.get("email")

        if not name or not email:
            messages.error(request, "Both name and email are required!")
            return redirect("add_dentist")

        if Dentist.objects.filter(email=email).exists():
            messages.error(request, "A dentist with this email already exists!")
            return redirect("add_dentist")

        Dentist.objects.create(name=name, email=email)
        messages.success(request, f"Dentist {name} has been added successfully!")
        return redirect("add_dentist")  # Changed to stay on the same page

    return render(request, "add_dentist.html")