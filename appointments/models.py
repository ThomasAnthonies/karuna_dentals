from django.db import models
from django.utils.timezone import now, timedelta
from datetime import time


class Patient(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=15, unique=True)
    address = models.TextField()
    date_of_birth = models.DateField()

    def __str__(self):
        return self.name

class Dentist(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(default='thomasanthonies33@gmail.com', unique=True)

    def __str__(self):
        return self.name


class available_timmings(models.Model):
    dentist = models.ForeignKey(Dentist, on_delete=models.CASCADE)
    maximum_appointments = models.IntegerField(default=3)
    booked_appointments = models.IntegerField(default=0)
    date= models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
  
    
    def is_available(self):
        return self.booked_appointments < self.maximum_appointments

    def available_slots(self):
        return self.maximum_appointments - self.booked_appointments

class OTP(models.Model):
    email = models.EmailField()
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    expiry_time = models.DateTimeField()
    is_verified = models.BooleanField(default=False)

    def expired(self):
        return now() > self.expiry_time

    def save(self, *args, **kwargs):
        if not self.expiry_time:
            self.expiry_time = now() + timedelta(minutes=5)
        super().save(*args, **kwargs)

class Appointment(models.Model):
    STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('completed', 'Completed'),
        ('canceled', 'Canceled'),
    ]

    APPOINTMENT_TYPES = [
        ('checkup', 'Checkup'),
        ('cleaning', 'Cleaning'),
        ('extraction', 'Extraction'),
        ('filling', 'Filling'),
    ]

    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)  
    date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')
    notes = models.TextField(blank=True, null=True)
    slot_verified = models.BooleanField(default=False)
    slot_verified_by = models.CharField(max_length=100, blank=True, null=True)
    cancellation_count = models.IntegerField(default=0)
    cancellation_reason = models.TextField(blank=True, null=True)
    appointed_doctor = models.ForeignKey(Dentist, on_delete=models.CASCADE, blank=True, null=True)
    appointment_type = models.CharField(max_length=50, choices=APPOINTMENT_TYPES)
    appointment_timming=models.ForeignKey(available_timmings, on_delete=models.CASCADE)
    def __str__(self):
        return f"Appointment for {self.patient.name} on {self.date}"

class Blacklist(models.Model):
    phone = models.CharField(max_length=15, unique=True)
    email = models.EmailField(unique=True)
    reason = models.TextField(blank=True, null=True)
    blacklisted_on = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Blacklisted: {self.phone} - {self.email}"
    
    def blacklisting_over(self):
        return now() > self.blacklisted_on + timedelta(days=30)

class Staff(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    role_description = models.TextField(blank=True, null=True)  # Optional role details
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class appointment_cancellation(models.Model):
    
    name= models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=15)
    cancellation_count = models.IntegerField(default=0)
    cancellation_reason = models.TextField(blank=True, null=True)
    cancelled_by = models.CharField(max_length=100, default='staff')  # Could be 'patient' or 'staff'
    cancelled_at = models.DateTimeField(auto_now_add=True)
    last_cancellation = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Cancellation of {self.name} by {self.cancelled_by}"
    
