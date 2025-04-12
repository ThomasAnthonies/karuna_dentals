# appointments/forms.py

from django import forms
from .models import Dentist
from .models import Appointment, Patient

class PatientForm(forms.ModelForm):
    class Meta:
        model = Patient
        fields = ['name', 'email', 'phone', 'address', 'date_of_birth']

class AppointmentForm(forms.ModelForm):
    class Meta:
        model = Appointment
        fields = ['notes', 'appointment_type']
        
        
class DentistForm(forms.ModelForm):
    class Meta:
        model = Dentist
        fields = ['name', 'email']

from django import forms

class StaffLoginForm(forms.Form):
    username = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput)
