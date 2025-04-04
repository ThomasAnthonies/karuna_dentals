# appointments/forms.py

from django import forms
from .models import Dentist

class DentistForm(forms.ModelForm):
    class Meta:
        model = Dentist
        fields = ['name', 'email', 'phone']
