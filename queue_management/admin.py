from django.contrib import admin

from .models import Doctor, Patient, Appointment


# =========================================================
# DOCTOR ADMIN
# =========================================================

@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):

    list_display = (
        "full_name",
        "specialization",
        "is_available",
        "created_at",
    )

    search_fields = (
        "full_name",
        "specialization",
    )

    list_filter = (
        "specialization",
        "is_available",
        "created_at",
    )

    fields = (
        "full_name",
        "specialization",
        "image",
        "available_time",
        "available_days",
        "consultation_fee",
        "is_available",
    )

    readonly_fields = (
        "created_at",
    )

# =========================================================
# PATIENT ADMIN
# =========================================================

@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):

    list_display = (
        "full_name",
        "cnic",
        "gender",
        "phone_number",
        "user",
        "created_at",
    )

    search_fields = (
        "full_name",
        "cnic",
        "phone_number",
        "user__username",
    )

    list_filter = (
        "gender",
        "created_at",
    )

    readonly_fields = (
        "created_at",
    )


# =========================================================
# APPOINTMENT ADMIN
# =========================================================

@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):

    list_display = (
        "token_number",
        "patient",
        "doctor",
        "department",
        "appointment_date",
        "appointment_time",
        "status",
    )

    search_fields = (
        "patient__full_name",
        "doctor__full_name",
        "department",
        "token_number",
    )

    list_filter = (
        "department",
        "status",
        "appointment_date",
    )

    ordering = (
        "appointment_date",
        "appointment_time",
        "token_number",
    )

    readonly_fields = (
        "department",
        "token_number",
        "created_at",
    )