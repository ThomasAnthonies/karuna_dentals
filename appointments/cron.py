from django_cron import CronJobBase, Schedule
from datetime import datetime
from .models import Appointment, Patient
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
        
        for appt in appointments:
            try:
                patient = appt.patient  # Directly using FK relation

                Temporary_patient_location.objects.create(
                    name=patient.name,
                    email=patient.email,
                    phone=patient.phone,
                    address=patient.address,
                    date_of_birth=patient.date_of_birth,
                )

                logger.info(f"Moved patient {patient.name} to temporary location.")
                patient.delete()
                appt.delete()

            except Exception as e:
                logger.error(f"Error moving patient from appointment {appt.pk}: {str(e)}")
