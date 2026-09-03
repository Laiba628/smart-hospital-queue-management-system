from django.db import models
from django.contrib.auth.models import User


# =========================================================
# PATIENT
# =========================================================

class Patient(models.Model):

    GENDER_CHOICES = [
        ("Male", "Male"),
        ("Female", "Female"),
        ("Other", "Other"),
    ]

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="patient_profile"
    )

    cnic = models.CharField(
        max_length=20,
        unique=True
    )

    full_name = models.CharField(
        max_length=100
    )

    father_name = models.CharField(
        max_length=100
    )

    gender = models.CharField(
        max_length=10,
        choices=GENDER_CHOICES
    )

    date_of_birth = models.DateField()

    phone_number = models.CharField(
        max_length=20
    )

    address = models.TextField()

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return self.full_name


# =========================================================
# DOCTOR
# =========================================================

class Doctor(models.Model):

    full_name = models.CharField(
        max_length=100
    )

    specialization = models.CharField(
        max_length=100
    )

    available_days = models.CharField(
        max_length=200,
        default="Mon,Tue,Wed,Thu,Fri"
    )

    available_time = models.CharField(
        max_length=100,
        default="09:00 AM - 02:00 PM"
    )

    is_available = models.BooleanField(
        default=True
    )
    consultation_fee = models.DecimalField(
    max_digits=10,
    decimal_places=2,
    default=0
    )

    image = models.ImageField(
        upload_to="doctors/",
        blank=True,
        null=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return self.full_name


# =========================================================
# APPOINTMENT
# =========================================================

class Appointment(models.Model):

    STATUS_CHOICES = [
        ("Pending", "Pending"),
        ("Confirmed", "Confirmed"),
        ("Completed", "Completed"),
        ("Cancelled", "Cancelled"),
    ]

    patient = models.ForeignKey(
        Patient,
        on_delete=models.CASCADE,
        related_name="appointments"
    )

    doctor = models.ForeignKey(
        Doctor,
        on_delete=models.CASCADE,
        related_name="appointments"
    )

    # Department is stored separately so queue can be
    # managed department-wise.
    department = models.CharField(
        max_length=100,
        blank=True
    )

    appointment_date = models.DateField()

    appointment_time = models.TimeField()

    token_number = models.PositiveIntegerField(
        null=True,
        blank=True
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="Pending"
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def save(self, *args, **kwargs):

        if self.doctor and not self.department:
            self.department = self.doctor.specialization

        super().save(*args, **kwargs)

    def __str__(self):
        return (
            f"{self.patient.full_name} - "
            f"{self.doctor.full_name}"
            f"Token {self.token_number}"
        )