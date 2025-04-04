import logging
import random
import string
from django.core.mail import send_mail
from django.conf import settings

logger = logging.getLogger(__name__)

def generate_otp():
    """Generate a random 6-digit OTP."""
    return ''.join(random.choices(string.digits, k=6))

def send_otp_email(email):
    """
    Sends an OTP email to the given address.
    Note: In a production environment, avoid logging sensitive OTP values.
    """
    otp = generate_otp()
    subject = "Your OTP Code"
    message = f"Your OTP code is: {otp}"
    from_email = settings.DEFAULT_FROM_EMAIL
    send_mail(subject, message, from_email, [email])
    logger.info(f"OTP sent to {email}")
    # Optionally, save the OTP in the database:
    # OTP.objects.create(email=email, otp=otp)
    return ('otp send to {email} sucessfullly')

def send_email_notification(email, appointment_date, start_time, end_time, dentist):
    """
    Sends a confirmation email for the appointment.
    """
    subject = "Appointment Confirmation"
    message = (
        f"Dear Patient,\n\n"
        f"Your appointment has been successfully booked.\n"
        f"Appointment Date: {appointment_date}\n"
        f"Appointment Time: {start_time} - {end_time}\n"
        f"Dentist: {dentist}\n\n"
        "Thank you for choosing our dental clinic."
    )
    from_email = settings.DEFAULT_FROM_EMAIL
    send_mail(subject, message, from_email, [email])
    logger.info(f"Confirmation email sent to {email} for appointment on {appointment_date}.")
    return
