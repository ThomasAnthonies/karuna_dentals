from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from datetime import date, datetime
from django.core.mail import send_mail
import random
from django.db.models import Q, Max
from django.db import IntegrityError, DataError
from django.core.exceptions import ValidationError

# Create your views here.

def get_client_ip(request):
    """Retrieve the client's IP address from the request."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip
from dentist_side.models import Follow_up, Patient_details, Doctor_login, Temporary_patient_location, DoctorLoginHistory
from appointments.models import Dentist, Patient, Appointment, available_timmings, OTP


from django.views.decorators.http import require_http_methods

from django.views.decorators.csrf import csrf_exempt


@csrf_exempt
def put_the_patient_record(request, patient_id, date):
    # Step 1: Authentication check
    if not is_authenticated_doctor(request):
        messages.error(request, "Access denied. Please log in as a doctor to add follow-ups.")
        return redirect('doctor_login')

    try:
        doctor = Dentist.objects.get(id=request.session.get('dentist_id'))
    except Dentist.DoesNotExist:
        messages.error(request, "Doctor not found.")
        return redirect('doctor_login')

    # Step 2: Get patient from either model
    try:
        patient = Patient.objects.get(id=patient_id)
    except Patient.DoesNotExist:
        try:
            patient = Temporary_patient_location.objects.get(id=patient_id)
        except Temporary_patient_location.DoesNotExist:
            messages.error(request, "No patient record found for this doctor on the selected date.")
            return redirect('doctor_dashboard')

    # Step 3: Handle POST
    if request.method == 'POST':
        print("POST request received")
        # Create patient follow-up entry
        try:
            follow_patient = Patient_details.objects.create(
                name=patient.name,
                email=patient.email,
                phone=patient.phone,
                address=patient.address,
                date_of_birth=patient.date_of_birth
            )
            print(follow_patient)
        except IntegrityError as e: # here we have to do something like update the stuff 
            try:
                follow_patient=Patient_details.objects.get(email=patient.email)
            except Patient_details.DoesNotExist :
                messages.error(request, "some error occoured ")
            print("IntegrityError: Could not create follow-up patient record due to a constraint violation.", e)
        except DataError as e:
            print("DataError: Invalid data provided for follow-up patient record.", e)
            try:
                follow_patient=Patient_details.objects.get(email=patient.email)
            except Patient_details.DoesNotExist :
                messages.error(request, "some error occoured ")
        except ValidationError as e:
            print("ValidationError: One or more fields failed validation.", e)
            try:
                follow_patient=Patient_details.objects.get(email=patient.email)
            except Patient_details.DoesNotExist :
                messages.error(request, "some error occoured ")
        except Exception as e:
            print("Unexpected error while creating follow-up patient record:", e)
            try:
                follow_patient=Patient_details.objects.get(email=patient.email)
            except Patient_details.DoesNotExist :
                messages.error(request, "some error occoured ")
        
        
        
        
        # Save follow-up record
        follow = Follow_up.objects.create(
            patient=follow_patient,
            date=datetime.strptime(date, "%Y-%m-%d").date(),
            doctor_attended=doctor,
            diagnosis=request.POST.get('diagnosis'),
            medicine=request.POST.get('medicine'),
        )
        print (follow)

        # Clean up original records
        Appointment.objects.filter(patient=patient).delete()
        try:
            patient.delete()
            print("the patient is deleted ")
        except Exception:
            messages.warning(request, 'Could not delete the patient record.')

        messages.success(request, "Follow-up recorded successfully.")
        return render(request, 'patients_visit.html', {
            'patient': follow_patient,
            'follow_up': follow,
            'doctor': doctor,
            
        })

    # Step 4: Handle GET
    return render(request, 'followup_creation_of_site_visited.html', {
        'patient': patient,
        'doctor': doctor,
        'date': date,
    })




def is_authenticated_doctor(request):
    return 'dentist_id' in request.session

def get_logged_in_doctor(request):
   
    return Dentist.objects.get(id=request.session['dentist_id'])

def follow_up_records(request, patient_id):
    # 1. Check session
    if not is_authenticated_doctor(request):
        messages.error(request, "You must be logged in as a doctor to view this.")
        return redirect('doctor_login')

    # 2. Get the doctor
    try:
        doctor = get_logged_in_doctor(request)
    except Dentist.DoesNotExist:
        messages.error(request, "Doctor session is invalid.")
        return redirect('doctor_login')

    # 3. Filter follow-ups where:
    #    - patient_id matches
    #    - AND this doctor attended them
    try  :
        patient=Patient_details.objects.get(id=patient_id)
        patient_record = Follow_up.objects.filter(
            patient=patient,
            doctor_attended=doctor
        )
    except Patient_details.DoesNotExist :
        messages.error(request, "No records found or you are not authorized to view this patient.")
        return render(request,'patients_records.html')
    return render(request, 'patient_record.html', {'patient': patient, 'followups' :patient_record})
    
def all_patients_visited(request):
    today = date.today()

    # Step 1: Securely get the logged-in doctor
    if not is_authenticated_doctor(request):
        messages.error(request, "You must be logged in as a doctor to view patient data.")
        return redirect('doctor_login')

    try:
        doctor = get_logged_in_doctor(request)
    except Dentist.DoesNotExist:
        messages.error(request, "Invalid doctor session. Please log in again.")
        return redirect('doctor_login')

    # Step 2: Get all appointments for this doctor today
    appointments_today = Appointment.objects.filter(
        appointed_doctor=doctor,
        date=today
    ).select_related('patient')

    patients_today = [appt.patient for appt in appointments_today]

    # Step 3: Restrict access to temporary patients (optional: show only those related to this doctor)
    # You might want to filter by doctor if there's a relationship
    try :
        temporary_patients = Temporary_patient_location.objects.all()
    except Exception :
        messages.error(request,"you are upto-date")
        temporary_patients = []
    context = {
    'appointments_today': appointments_today,
    'patients_today': patients_today,
    'temporary_patients': temporary_patients,
    'today': today,
    'today_str': today.strftime('%Y-%m-%d'),
    'doctor': doctor,
    }


    return render(request, 'today_patients.html', context)

    
def patients_records(request):
    # Step 1: Authenticate doctor login
    if not is_authenticated_doctor(request):
        messages.error(request, "Access denied. Please log in as a doctor to view patient records.")
        return redirect('doctor_login')

    # Step 2: Get the logged-in doctor
    try:
        doctor = get_logged_in_doctor(request)
    except Dentist.DoesNotExist:
        messages.error(request, "Invalid doctor session. Please log in again.")
        return redirect('doctor_login')

    # Step 3: Retrieve patient records
    patients = Patient_details.objects.all()

    if not patients.exists():
        messages.info(request, "No patient records found.")

    return render(request, 'patients_records.html', {'patients': patients})



##################################################################################


       
def doctor_login(request):
    
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        raw_password = request.POST.get('password', '').strip()
        
        try:
            # 1. Check if a dentist with the given email exists
            dentist = Dentist.objects.get(email=email)
            # 2. Check if login credentials exist for that dentist
            doctor_login = Doctor_login.objects.get(dentist=dentist)
            
            # 3. Verify password
            if doctor_login.check_password(raw_password):
                # 4. Store in session
                request.session.flush()  # Clear any old session
                request.session.clear_expired()  # optional but helps clean dead sessions
                # Use a new session
                request.session.cycle_key()
                request.session['dentist_id'] = dentist.pk
                request.session['dentist_name'] = dentist.name
                request.session['login_time'] = timezone.now().isoformat()

                # 5. Store user environment (IP + browser info)
                user_ip = get_client_ip(request)
                user_agent = request.META.get('HTTP_USER_AGENT', '')
                session_key = request.session.session_key or request.session._get_or_create_session_key()

                request.session['user_ip'] = user_ip
                request.session['user_agent'] = user_agent
                request.session['session_key'] = session_key
                request.session.set_expiry(3600)  # 1 hour

                # 6. Save login history
                doctr_history =DoctorLoginHistory.objects.create(
                    dentist=dentist,
                    ip_address=user_ip,
                    user_agent=user_agent,
                    session_key=session_key,
                )

                messages.success(request, "Login successful! This session is valid for 1 hour.")
                return render(request,'doctor_home.html')  # Your dashboard URL

            else:
                print("the password is incorrect ")
                messages.error(request, "Incorrect password.")

        except Dentist.DoesNotExist  as e :
            messages.error(request, "No account found with this email.")
            print(e)
        except Doctor_login.DoesNotExist as e :
            messages.error(request, "Login credentials not set for this dentist.")
            print(e)
        
    return render(request, 'doctor_login.html')



def doctor_logout(request):
    # Clear all session data
    request.session.flush()

    # Optional: Set a logout success message
    messages.success(request, "You have been successfully logged out.")

    # Redirect back to login page
    return redirect('doctor_login')



def send_otp_email(request):
    if request.method=='POST':
        email= request.POST.get('email')
        print(email)
        try :
            dentist=Dentist.objects.get(email=email)
            print(dentist.email)
        except Dentist.DoesNotExist as e :
            print (e)
            messages.error(request, 'Sorry!!!!!!the entered email is not the registered email for the Doctor,')
            return redirect('send_otp_email')
        otp_code = f"{random.randint(100000, 999999)}"

        # Step 2: Save OTP to DB
        OTP.objects.create(email=email, otp=otp_code)
        request.session['email']= email
        send_mail(
            'Your OTP for Doctor Login Creation',
            f'Your OTP is: {otp_code}. It is valid for 5 minutes.',
            'clinic@example.com',
            [email],
            fail_silently=False,
        )
        messages.success(request, "OTP sent to your email.")
        return redirect('verify_otp')
    return render(request, 'send_otp_.html')



def verify_otp_view(request):
    if request.method == 'POST':
        email = request.session.get('email')
        entered_otp = request.POST.get('otp')

        try:
            otp_entry = OTP.objects.filter(email=email, is_verified=False).latest('created_at')

            if otp_entry.expired():
                messages.error(request, "OTP has expired. Please request a new one.")
                return redirect('send_otp_email')

            if otp_entry.otp == entered_otp:
                otp_entry.is_verified = True
                otp_entry.save()
                request.session['verified_email'] = email
                messages.success(request, "OTP verified! You may now set your password.")
                return redirect('doctor_login_creation')

            else:
                messages.error(request, "Invalid OTP.")
        except OTP.DoesNotExist:
            messages.error(request, "No OTP found for this email.")
    return render(request, 'verify_otp_.html')



def doctor_login_creation(request):
    if request.method == 'POST':
        email = request.session.get('verified_email')
        raw_password = request.POST.get('password')

        if not email:
            messages.error(request, "Please verify your email with OTP first.")
            return redirect('send_otp_email')

        try:
            dentist = Dentist.objects.get(email=email)
        except Dentist.DoesNotExist:
            messages.error(request, "Dentist with this email not found.")
            return redirect('send_otp_email')

        # Step 1: Create login entry
        doctor_login = Doctor_login.objects.create(dentist=dentist)
        doctor_login.set_password(raw_password)

        # Optional: Clear the session
        del request.session['verified_email']

        messages.success(request, "Doctor login created successfully!")
        return redirect('doctor_login')
    
    return render(request, 'doctor_login_creation.html')


def walk_ins(request):
    if request.method == 'POST':
        if not is_authenticated_doctor(request):
            messages.error(request, "Access denied. Please login as a doctor to view patient records.")
            return redirect('doctor_login')
        try :
            email=request.POST.get('email')
            Patient_details.objects.get(email= email)
            request.session['walk_in_email']=email
            messages.success(request, 'We have found a matching email address')
            return render(request, 'walkin_follow_up.html')
        except Patient_details.DoesNotExist :  
            request.session['walk_in_email']=email
            try :
                phone=request.POST.get('phone')
                
                Patient_details.objects.get(phone=request.POST.get('phone'))
                del request.session['walk_in_email']
                request.session['phone']=phone
                messages.error(request, 'Sorry !! the email doesnot exist, but the phone number do and we have fetched the patient detials of this number')
                return redirect(request, 'walkin_follow_up')
            except Patient_details.DoesNotExist:
                request.session['phone']=phone
                messages.error(request, 'Sorry !!! No patient exist with that phone number or email, so we are creating a new on with the phone number and email you entered')
                return render (request,'create_new_form.html')
    return render(request,'get_patient_by_email_or_phone.html')#############
        
        

    
def create_new_form(request):
    if request.method == 'POST':    
        try :
            patient = Patient_details.objects.create(
                    name=request.POST.get('name', ''),
                    email=request.POST.get('walk_in_email'),
                    phone=request.POST.get('phone'),
                    address=request.POST.get('address', ''),
                    date_of_birth=request.POST.get('date_of_birth', '')
                )
            request.session['walk_in_email']
        except  :       
            messages.error(request,'some error occured try changing the email  or phone number because no same email or phone for a patient is allowded ')
            return render(request, 'form_for_new_patient.html')  
        return render(request, 'walkin_follow_up.html')
    return render(request, 'create_new_form.html')
    
    
from datetime import date
from django.db import IntegrityError

def create_walkin_follow_ups_details(request):
    if not is_authenticated_doctor(request):
        messages.error(request, "Access denied. Please log in as a doctor to view patient records.")
        return redirect('doctor_login')

    email = request.session.get('walk_in_email')
    try:
        patient = Patient_details.objects.get(email=email)
    except Patient_details.DoesNotExist:
        messages.error(request, 'No patient details found. Please try registering.')
        return render(request, 'form_for_new_patient.html')

    # Fetch existing followups for display
    follow = list(Follow_up.objects.filter(patient=patient).order_by('-date'))

    if request.method == 'POST':
        try:
            doc = Dentist.objects.get(id=request.session.get('dentist_id'))                   
        except Dentist.DoesNotExist:
            messages.error(request, 'Doctor not found.')
            return redirect('doctor_login')

        try:
            followup = Follow_up.objects.create(
                patient=patient,
                date=date.today(),
                doctor_attended=doc,
                diagnosis=request.POST.get('diagnosis'),
                medicine=request.POST.get('medicine')
            )
            messages.success(request, 'Follow-up created successfully.')

            # Refresh followup list to include the new one
            follow = list(Follow_up.objects.filter(patient=patient).order_by('-date'))

        except IntegrityError:
            messages.error(request, 'Could not save follow-up.')

    return render(request, 'walkin_follow_up.html', {'follow': follow})
    
def all_patients_visited_from_start(request):
    if not is_authenticated_doctor(request):
        messages.error(request, "Access denied. Please log in as a doctor to view patient records.")
        return redirect('doctor_login')

    doc = request.session.get('dentist_id')

    try:
        unique_patients = Patient_details.objects.filter(
            followups__doctor_attended=doc
        ).annotate(
            last_visit=Max('followups__date')
        ).order_by('-last_visit')
    except Exception as e:
        messages.error(request, f'Some error occurred: {str(e)}')
        unique_patients = []

    return render(request, 'patients_visited.html', {'patients': unique_patients})
def all_patients_visited_s_selected_patients_followups(request, patient_id):
    if not is_authenticated_doctor(request):
        messages.error(request, "Access denied. Please log in as a doctor to view patient records.")
        return redirect('doctor_login')

    patient = get_object_or_404(Patient_details, id=patient_id)

    patient_followups = Follow_up.objects.filter(
        patient=patient,
        doctor_attended=request.session.get('dentist_id')
    ).order_by('-date')  # optional: latest follow-ups first

    return render(request, 'specified_patients_followup.html', {
        'patient_followups': patient_followups,
        'patient': patient
    })
def patient_visit_repeat_followups(request, patient_id):
    if not is_authenticated_doctor(request):
        messages.error(request, "Access denied. Please log in as a doctor to add follow-ups.")
        return redirect('doctor_login')

    patient = get_object_or_404(Patient_details, id=patient_id)
    doctor = get_object_or_404(Dentist, id=request.session.get('dentist_id'))

    if request.method == 'POST':
        try:
            Follow_up.objects.create(
                patient=patient,
                date=date.today(),
                doctor_attended=doctor,
                diagnosis=request.POST.get('diagnosis', ''),
                medicine=request.POST.get('medicine', '')
            )
            messages.success(request, "Follow-up successfully added.")
        except Exception as e:
            messages.error(request, f"Error creating follow-up: {str(e)}")

    return redirect('patients_visited')  # or wherever your list view is 
    
def home_go(request):
    return render(request, 'doctor_home.html')

def all_patients_from_past_and_future(request):
    if request.method == 'POST':
        selected_date_str = request.POST.get("date")
        try:
            selected_date = datetime.strptime(selected_date_str, "%Y-%m-%d").date()
            appointments = Appointment.objects.filter(date=selected_date,appointed_doctor=get_logged_in_doctor(request)).order_by('appointment_timming__start_time')
        except (ValueError, TypeError):
            appointments = Appointment.objects.none()
            messages.error(request, "Invalid date format provided.")
    else:
        appointments = Appointment.objects.filter(appointed_doctor=get_logged_in_doctor(request)).order_by('date', 'appointment_timming__start_time')

    return render(request, "all_patients_from_past_and_future.html", {'appointments': appointments})



def temporary_patients_followup(request, patient_id):
    patient = get_object_or_404(Temporary_patient_location, id=patient_id)

    if request.method == 'POST':
        try:
            doctor = get_logged_in_doctor(request)
            if not doctor:
                messages.error(request, "Doctor session expired. Please log in again.")
                return redirect('doctor_login')

            # Check for existing patient by email or phone
            existing_patient = Patient_details.objects.filter(
                Q(email=patient.email) | Q(phone=patient.phone)
            ).first()

            if existing_patient:
                new_patient = existing_patient
            else:
                # Create a new permanent patient record
                new_patient = Patient_details.objects.create(
                    name=patient.name,
                    email=patient.email,
                    phone=patient.phone,
                    address=patient.address,
                    date_of_birth=patient.date_of_birth
                )

            # Create the follow-up record
            Follow_up.objects.create(
                patient=new_patient,
                doctor_attended=doctor,
                diagnosis=request.POST.get('diagnosis', ''),
                medicine=request.POST.get('medicine', '')
            )

            # Clean up temporary record
            patient.delete()

            messages.success(request, "Follow-up saved. Patient successfully recorded.")
            return redirect('patients_records')

        except IntegrityError as e:
            messages.error(request, f"Integrity error: {str(e)}")
            return redirect('doctor_dashboard')
        except Exception as e:
            messages.error(request, f"Unexpected error: {str(e)}")
            return redirect('doctor_dashboard')

    else:
        # GET request: Show the follow-up form along with existing history
        # Try to find existing patient details if they exist
        existing_patient = Patient_details.objects.filter(
            Q(email=patient.email) | Q(phone=patient.phone)
        ).first()

        followups = Follow_up.objects.filter(patient=existing_patient).order_by('-date') if existing_patient else []

        return render(request, 'followup_form.html', {
            'patient': patient,
            'followups': followups
        })