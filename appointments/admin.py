from django.contrib import admin
from .models import Patient, Dentist, Appointment,available_timmings,OTP,Appointment,Blacklist,Staff,appointment_cancellation

admin.site.register(Patient)
admin.site.register(Dentist)
admin.site.register(Appointment)
admin.site.register(available_timmings)
admin.site.register(OTP)
admin.site.register(Blacklist)
admin.site.register(Staff)
admin.site.register(appointment_cancellation)


# # Register your models here.

