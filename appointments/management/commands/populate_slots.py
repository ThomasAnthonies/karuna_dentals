# appointments/management/commands/populate_slots.py

from django.core.management.base import BaseCommand
from datetime import time
from appointments.models import Dentist, available_timmings

class Command(BaseCommand):
    help = 'Populate available slots for each dentist from 10am to 5pm.'

    def handle(self, *args, **kwargs):
        dentists = Dentist.objects.all()

        if not dentists.exists():
            self.stdout.write(self.style.WARNING('No dentists found. Please add dentists first.'))
            return

        slots = [
            (time(10, 0), time(11, 0)),
            (time(11, 0), time(12, 0)),
            (time(12, 0), time(13, 0)),
            (time(15, 0), time(16, 0)),
            (time(16, 0), time(17, 0)),
            (time(17, 0), time(18, 0)),
        ]

        for dentist in dentists:
            for start_time, end_time in slots:
                if not available_timmings.objects.filter(dentist=dentist, start_time=start_time, end_time=end_time).exists():
                    available_timmings.objects.create(
                        dentist=dentist,
                        start_time=start_time,
                        end_time=end_time,
                        maximum_appointments=3,
                        booked_appointments=0
                    )
                    self.stdout.write(self.style.SUCCESS(
                        f'Successfully created slot for {dentist.name} from {start_time} to {end_time}.'
                    ))
                else:
                    self.stdout.write(self.style.WARNING(
                        f'Slot for {dentist.name} from {start_time} to {end_time} already exists.'
                    ))
