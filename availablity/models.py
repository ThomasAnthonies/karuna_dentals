from django.db import models
from appointments.models import Dentist

class Dentist_leave(models.Model):  # ✅ Use PascalCase for model names
    dentist = models.ForeignKey(Dentist, on_delete=models.CASCADE)
    leave_date = models.DateField()

    def __str__(self):
        return f"{self.dentist.name} - {self.leave_date}"
