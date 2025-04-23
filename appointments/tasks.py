from celery import shared_task
from datetime import datetime
from .models import Appointment
from dentist_side.models import Temporary_patient_location
import logging

logger = logging.getLogger(__name__)

@shared_task
def move_appointments():
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
