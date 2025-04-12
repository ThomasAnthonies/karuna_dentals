from django.db import models
from appointments.models import Dentist,OTP
from django.contrib.auth.hashers import make_password, check_password
from django.utils import timezone


class Patient_details(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(default='thomasanthonies33@gmail.com', unique=True)
    phone = models.CharField(max_length=15, unique=True)
    address = models.TextField()
    date_of_birth = models.DateField()

    def __str__(self):
        return self.name

class Follow_up(models.Model):
    patient = models.ForeignKey(Patient_details, on_delete=models.CASCADE, related_name='followups')
    date = models.DateField(auto_now_add=True)
    doctor_attended = models.ForeignKey(Dentist, on_delete=models.CASCADE)
    diagnosis = models.CharField(max_length=200)
    medicine = models.CharField(max_length=200)

    def __str__(self):
        return f"{self.patient.name} - {self.date} - {self.diagnosis}"

class Doctor_login(models.Model):
    dentist=models.ForeignKey(Dentist, on_delete=models.CASCADE)
    password=models.CharField(max_length=128)
    
    def set_password(self, raw_password):
        self.password = make_password(raw_password)
        self.save()

    def check_password(self, raw_password):
        return check_password(raw_password, self.password)


class Temporary_patient_location(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=15, unique=True)
    address = models.TextField()
    date_of_birth = models.DateField()

    def __str__(self):
        return self.name


class DoctorLoginHistory(models.Model):
    dentist = models.ForeignKey(Dentist, on_delete=models.CASCADE)
    login_time = models.DateTimeField(default=timezone.now)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    session_key = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.dentist.name} at {self.login_time}"