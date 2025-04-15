from django_cron import CronJobBase, Schedule
from django.core.mail import send_mail
from datetime import datetime
from .models import Appointment, Patient, Dentist
from dentist_side.models import Temporary_patient_location  
import logging

logger = logging.getLogger(__name__)

class MoveAppointmentsCronJob(CronJobBase):
    RUN_AT_TIMES = ['07:00']
    schedule = Schedule(run_at_times=RUN_AT_TIMES)
    code = 'appointments.move_appointments_cron_job'

    def do(self):
        today = datetime.today().date()
        appointments = Appointment.objects.filter(date=today)
        moved_patients = []

        for appt in appointments:
            try:
                patient = appt.patient

                Temporary_patient_location.objects.create(
                    name=patient.name,
                    email=patient.email,
                    phone=patient.phone,
                    address=patient.address,
                    date_of_birth=patient.date_of_birth,
                )

                moved_patients.append(patient.name)
                logger.info(f"Moved patient {patient.name} to temporary location.")
                patient.delete()
                appt.delete()

            except Exception as e:
                logger.error(f"Error processing appointment {appt.pk}: {e}")

        # Step 3: Send Email if any patients were moved
        if moved_patients:
            subject = f"[Auto Notification] {len(moved_patients)} Patients Moved to Temporary Location"
            message = "The following patients were moved to the temporary list today:\n\n"
            message += "\n".join(moved_patients)
            message += f"\n\nTime: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

            # Get all dentist emails (fetching emails from the Dentist model)
            recipients = Dentist.objects.values_list('email', flat=True)

            send_mail(
                subject=subject,
                message=message,
                from_email=None,  # Uses DEFAULT_FROM_EMAIL as defined in settings.py
                recipient_list=list(recipients),
                fail_silently=False,
            )

            logger.info(f"Notification sent to dentists: {', '.join(recipients)}")
