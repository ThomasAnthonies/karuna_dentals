# appointments/forms.py

from django import forms
from .models import Dentist

class DentistForm(forms.ModelForm):
    class Meta:
        model = Dentist
        fields = ['name', 'email']

from django import forms

class StaffLoginForm(forms.Form):
    username = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput)
