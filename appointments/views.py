
from django.shortcuts import render, redirect, get_object_or_404
from django.core.exceptions import ValidationError
from django.http import HttpResponse, JsonResponse
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
import logging
from datetime import datetime, timedelta, time
from django.utils.timezone import now
import random
from django.urls import reverse

from .models import Dentist, Appointment, OTP, Patient, available_timmings, Blacklist
from .utils import generate_otp,  send_email_notification
from appointments.models import appointment_cancellation


logger = logging.getLogger(__name__)



    
    
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
        messages.success(request, "OTP sent successfully!")
        return redirect('verify_otp_patient')  # <-- this should match the URL name in urls.py

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
from django.db import IntegrityError, transaction
from django.db.utils import OperationalError
from datetime import datetime
from django.utils import timezone
from appointments.models import Blacklist



from .models import Patient, Appointment, Dentist, available_timmings
from .utils import send_email_notification  # Assuming you have this defined



def home(request):
    return render(request, 'home.html')


def book_slot(request):
    """
    Books an appointment if the OTP has been verified. Clears the OTP verification flag after booking.
    """
    # Ensure OTP is verified before booking
    if not request.session.get('otp_verified', False):
        messages.error(request, "OTP not verified. Please verify your email before booking.") 
        return render(request, 'available_slots.html')

    if request.method == 'POST':
        # Validate slot
        

        # Check if email already exists
        if Patient.objects.filter(email=request.session.get('otp_email')).exists():
            return HttpResponse("Patient with the same email already exists.", status=400)

        # Validate required form fields
        required_fields = ['name', 'phone', 'date_of_birth']
        if not all(request.POST.get(field) for field in required_fields):
            return HttpResponse("Missing required fields", status=400)

        email = request.session.get('otp_email')
        blacklist_entry = Blacklist.objects.filter(email=email).first()
        if blacklist_entry and blacklist_entry.blacklisted_on > timezone.now() - timedelta(days=30):
            messages.error(request, "Your email is blacklisted. Please contact support.")
            return render(request, 'available_slots.html')
        date_str=request.session.get('date_')
        start_time= request.session.get('start_time')
        end_time=request.session.get('end_time')
        print("DEBUG - Raw start_time:", start_time)
        print("DEBUG - Raw end_time:", end_time) 
        print("DEBUG - date_str:", date_str)
        print("DEBUG - session data snapshot:", dict(request.session))
        print("DEBUG - POST data:", request.POST)
        print("DEBUG - Checking if patient already exists:", request.session.get('otp_email'))



   
        
       
        # Try to create a new patient record
 

        try:
            with transaction.atomic():
                # 1. Create Patient
                new_patient = Patient.objects.create(
                    name=request.POST.get('name'),
                    email=request.session.get('otp_email'),
                    phone=request.POST.get('phone'),
                    address=request.POST.get('address', ''),
                    date_of_birth=request.POST.get('date_of_birth')
                )

                # 2. Fetch Dentist
                doctor = Dentist.objects.get(id=request.session.get('dentist'))

                # 3. Parse date and time
                start_time = request.session.get('start_time')
                end_time = request.session.get('end_time')
                date_str = request.session.get('date_')

                try:
                    # Try HH:MM:SS format
                    start_time_obj = datetime.strptime(start_time, '%H:%M:%S').time()
                    end_time_obj = datetime.strptime(end_time, '%H:%M:%S').time()
                except (ValueError, TypeError):
                    # Try HH:MM fallback
                    try:
                        start_time_obj = datetime.strptime(start_time, '%H:%M').time()
                        end_time_obj = datetime.strptime(end_time, '%H:%M').time()
                    except Exception:
                        messages.error(request, "Invalid time format. Try selecting the time again.")
                        return HttpResponse("Invalid time format. Try selecting the time again.", status=400)

                date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()

                # 4. Get or Create available_timmings
                try:
                    timming = available_timmings.objects.get(
                        dentist=doctor,
                        start_time=start_time_obj,
                        end_time=end_time_obj,
                        date=date_obj
                    )
                    timming.booked_appointments += 1
                    timming.save()
                except available_timmings.DoesNotExist:
                    timming = available_timmings.objects.create(
                        dentist=doctor,
                        start_time=start_time_obj,
                        end_time=end_time_obj,
                        date=date_obj
                    )

                # 5. Create Appointment
                appointment = Appointment.objects.create(
                    patient=new_patient,
                    date=date_obj,
                    status='scheduled',
                    notes=request.POST.get('notes', ''),
                    appointed_doctor=doctor,
                    appointment_type=request.POST.get('appointment_type', 'checkup'),
                    appointment_timming=timming
                )

        except Dentist.DoesNotExist:
            messages.error(request, "Selected dentist does not exist.")
            return HttpResponse("Selected dentist does not exist.", status=404)

        except available_timmings.MultipleObjectsReturned:
            messages.error(request, "Multiple timing slots found. Please contact admin.")
            return HttpResponse("Multiple timing slots found. Contact admin.", status=400)

        except ValueError as ve:
            messages.error(request, f"Time formatting error: {ve}")
            return HttpResponse("Invalid time format. Try again.", status=400)

        except IntegrityError as e:
            if 'phone' in str(e):
                messages.error(request, "The phone number is already registered.")
                context = {
                    'name': request.POST.get('name'),
                    'email': request.session.get('otp_email'),
                    'address': request.POST.get('address', ''),
                    'date_of_birth': request.POST.get('date_of_birth'),
                    'phone': request.POST.get('phone'),
                }
                return render(request, 'available_slots.html', context)
            else:
                messages.error(request, f"Database integrity error: {e}")
                return HttpResponse("Error saving data.", status=500)

        except ValidationError as ve:
            messages.error(request, f"Validation error: {ve}")
            return HttpResponse("Validation failed.", status=400)

        except OperationalError:
            messages.error(request, "Database connection issue. Try later.")
            return HttpResponse("Temporary DB issue. Try again.", status=500)

        except TypeError as te:
            messages.error(request, f"Missing session data: {te}")
            return HttpResponse("Missing session data. Please reselect slot.", status=400)

        except Exception as e:
            messages.error(request, f"Unexpected error: {str(e)}")
            return HttpResponse("Something went wrong during booking.", status=500)

        # 6. Send confirmation email
        try:
            send_email_notification(
                new_patient.email,
                appointment.date,
                appointment.appointment_timming.start_time,
                appointment.appointment_timming.end_time,
                appointment.appointed_doctor
            )
        except Exception as e:
            print(f"Email failed: {e}")

        # 7. Clear session and redirect
        request.session['otp_verified'] = False
        messages.success(request, "Appointment booked successfully!")
        return redirect('home')

    return HttpResponse("Invalid request method", status=405)










def book_appointment_page(request, slot_id):
    if not request.session.get('otp_verified', False):
        return HttpResponse("Please verify OTP before booking.", status=403)

    # Get the slot object
    slot = get_object_or_404(available_timmings, id=slot_id)

    return render(request, 'book_slot.html', {'slot_id': slot_id, 'slot': slot})





def view_appointments(request):
    if not request.session.get('staff_logged_in'):
     return redirect('staff_login')

    username = request.session.get('staff_username')
    if not username or username not in settings.STAFF_CREDENTIALS:
        return redirect('staff_login')
    """Display all scheduled appointments."""
    appointments = Appointment.objects.filter(status="scheduled").order_by("date")
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
    if not request.session.get('staff_logged_in'):
     return redirect('staff_login')

    username = request.session.get('staff_username')
    if not username or username not in settings.STAFF_CREDENTIALS:
        return redirect('staff_login')
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

from django.conf import settings
from django.shortcuts import render, redirect
from django.contrib import messages
from django.views.decorators.cache import never_cache
from .forms import StaffLoginForm

def staff_login_view(request):
    if request.method == 'POST':
        form = StaffLoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']

            credentials = settings.STAFF_CREDENTIALS
            if username in credentials and credentials[username] == password:
                request.session['staff_logged_in'] = True
                request.session['staff_username'] = username  # Store for future verification
                request.session['staff_password'] = password  # Store for future verification
                return redirect('staff_dashboard')
            else:
                messages.error(request, 'Invalid credentials')
    else:
        form = StaffLoginForm()

    return render(request, 'staff_login.html', {'form': form})

@never_cache
def staff_dashboard_view(request):
    if not request.session.get('staff_logged_in'):
        return redirect('staff_login')

    username = request.session.get('staff_username')
    # Optional check again for safety
    if username not in settings.STAFF_CREDENTIALS:
        return redirect('staff_login')

    return render(request, 'staff_dashboard.html', {'username': username})


def staff_logout_view(request):
    request.session.flush()
    messages.success(request, "Logged out successfully!")
    return redirect('staff_login')

def by_patient_canellation(request):
    """Cancel an appointment by the patient."""
    appointment = get_object_or_404(Appointment, patient__email=request.session.get('otp_email'))

    
    if request.method == "POST":
        reason = request.POST.get("cancellation_reason", "No reason provided")

        try:
            cancellation = appointment_cancellation.objects.get(email=appointment.patient.email)

            # Update last_cancellation if more than 10 days ago
            if timezone.now() - cancellation.last_cancellation > timedelta(days=10):
                cancellation.last_cancellation = timezone.now()

            # Update cancellation details
            cancellation.cancellation_count += 1
            cancellation.cancellation_reason = reason
            cancellation.cancelled_by = 'patient'
            cancellation.cancelled_at = timezone.now()
            cancellation.save()
            
            if cancellation.cancellation_count >= 3:
            # Add to blacklist if canceled more than 3 times
                try:
                    Blacklist.objects.create(
                        phone=cancellation.phone,
                        email=cancellation.email,
                        reason=reason,
                        blacklisted_on=timezone.now()
                    )
                    
                except IntegrityError:
                    messages.error(request, "you are all ready BLACKLISTED due to multiple canelations .")  
                cancellation.delete()  # Delete the cancellation record after blacklisting
                messages.success(request, "Sorry for the trouble you have been BLACK LISTED due to multiple cancellations. Please contact support for further assistance or try again after 30 days.")

        except appointment_cancellation.DoesNotExist:
            # Create a new record if one doesn't exist
            appointment_cancellation.objects.create(
                name=appointment.patient.name,
                email=appointment.patient.email,
                phone=appointment.patient.phone,
                cancellation_count=1,
                cancellation_reason=reason,
                cancelled_by='patient',
                cancelled_at=timezone.now(),  # manually setting this now
                last_cancellation=timezone.now(),
            )
        appointment_cancellation_o=appointment_cancellation.objects.get(email=appointment.patient.email)
        # Send cancellation email to the patient
        if appointment_cancellation.email:
            send_mail(
                subject="Appointment Cancellation Notice",
                message=f"Dear {appointment_cancellation_o.name},\n\nYour appointment on {appointment_cancellation_o.cancelled_at} has been canceled.\nReason : {reason}\n\nSorry for the inconvenience. This is your {appointment_cancellation_o.cancellation_count} cancellation. Make sure you dont cross the limit of 3 cancellations.\n\nIf you exceeds the limits try after 30 days. \n\n For further assistance please contact ph no : +91 92497 66351. Thank you.",    
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=[appointment_cancellation_o.email],
                fail_silently=False,
            )
        patient=Patient.objects.get(email=appointment.patient.email)   
        slot=available_timmings.objects.get(date=appointment.appointment_timming.date, dentist=appointment.appointment_timming.dentist,start_time= appointment.appointment_timming.start_time,end_time=appointment.appointment_timming.end_time)
        if slot.booked_appointments > 0:
            slot.booked_appointments -= 1
            slot.save()

        patient.delete()
        
        appointment.delete()  # Delete the appointment record after sending email
        
        
        messages.success(request, "Appointment has been canceled, and an email notification was sent.")
        return redirect("home")

    return redirect('home')  # Redirect to home or any other page if GET request

def getting_the_email_of_the_patient(request):
    """
    Fetches the email of the patient from the session.
    """
    email = request.post.get('email')
    try:
        Patient.objects.filter(email=email).get()
    except Patient.DoesNotExist:
        messages.error(request, "Patient not found please check wether the entered email id is correct .")
        return redirect('home')
    request.session['otp_email'] = email
    sending_otp( email)  # Call the function to send OTP
    return render(request,'verify_otp_for_cancelation.html')  # Redirect to OTP verification page
def sending_otp( email):
    try:
        
        OTP.objects.filter(email=email).delete()

# Create new OTP
        otp_record = OTP.objects.create(
            email=email,
            otp=generate_otp(),
            expiry_time=now() + timedelta(minutes=5)
        )
    except Exception as e:
        logger.error(f"Error sending OTP: {e}")
        return HttpResponse("Failed to send OTP", status=500)
    return HttpResponse("OTP sent successfully", status=200)
        
def verify_otp_view_for_cancellation(request):
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
            request.session['otp_attempts'] = 0  # reset attempts

            # Redirect user to book the slot after verification
            return render(request, 'show_appointment_details')

        except OTP.DoesNotExist:
            return HttpResponse("Invalid OTP.", status=400)

    return render(request, 'get_email.html', {
    'otp_email': request.session.get('otp_email'),
    'slot_id': request.session.get('slot_id')
})
    
def show_Details(request):
    """
    Show details of a specific appointment using email from session.
    """
    email = request.session.get('otp_email')
    if not email:
        messages.error(request, "Session expired or email not found.")
        return redirect('home')

    try:
        appointment = Appointment.objects.get(patient__email=email)
    except Appointment.DoesNotExist:
        messages.error(request, "No appointment found for the provided email.")
        return redirect('home')
    except Appointment.MultipleObjectsReturned:
        messages.error(request, "Multiple appointments found. Please contact support.")
        return redirect('home')

    # Try to fetch existing cancellation record, or create a blank one
    try:
        cancel = appointment_cancellation.objects.get(email=email)
    except appointment_cancellation.DoesNotExist:
        cancel = appointment_cancellation(
            name=appointment.patient.name,
            email=email,
            phone=appointment.patient.phone,
            cancellation_count=0,
            cancellation_reason='',
            cancelled_by='patient'
        )

    return render(request, 'cancel_appointment_by_patient.html', {
        'appointment': appointment,
        'cancel': cancel
    })
    
def date_of_booking(request, slot_id,date,dentist_id):
    """
    Fetches the date of booking from the request and stores it in the session.
    """
    date = request.POST.get('date')
    slot= request.POST.get('slot_id')
    if not date:
        messages.error(request, "Date is required.")
        return redirect('home')

    request.session['date'] = date  # Store the date in the session
    return render(request, 'available_slots.html', {'date': date})  # Redirect to available slots page
    
    # appointments/views.py
from django.http import JsonResponse
from appointments.tasks import move_appointments

def trigger_task(request):
    move_appointments.apply_async()  # Triggers the task asynchronously
    return JsonResponse({"status": "Task triggered"})




    
    