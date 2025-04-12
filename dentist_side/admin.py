from django.contrib import admin
from dentist_side.models import Patient_details,Follow_up,Doctor_login,Temporary_patient_location,DoctorLoginHistory
# Register your models here
admin.site.register(Patient_details)
admin.site.register(Follow_up)
admin.site.register(Doctor_login)
admin.site.register(Temporary_patient_location)
admin.site.register(DoctorLoginHistory)
