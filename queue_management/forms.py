from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm

from .models import Patient, Appointment


# =========================================================
# PATIENT REGISTRATION FORM
# =========================================================

class PatientForm(forms.ModelForm):

    class Meta:
        model = Patient

        fields = [
            "cnic",
            "full_name",
            "father_name",
            "gender",
            "date_of_birth",
            "phone_number",
            "address",
        ]

        widgets = {
            "date_of_birth": forms.DateInput(
                attrs={
                    "type": "date",
                    "class": "form-control",
                }
            ),
        }


# =========================================================
# APPOINTMENT FORM
# =========================================================

class AppointmentForm(forms.ModelForm):

    class Meta:
        model = Appointment

        fields = [
            "patient",
            "doctor",
            "appointment_date",
            "appointment_time",
        ]

        widgets = {
            "appointment_date": forms.DateInput(
                attrs={
                    "type": "date",
                    "class": "form-control",
                }
            ),

            "appointment_time": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),
        }

        labels = {
            "patient": "Select Patient",
            "doctor": "Select Doctor",
            "appointment_date": "Appointment Date",
            "appointment_time": "Preferred Appointment Time",
        }

    def __init__(self, *args, **kwargs):

        selected_doctor = kwargs.pop(
            "selected_doctor",
            None
        )

        super().__init__(*args, **kwargs)

        time_choices = [
            ("", "--------- Select Time ---------"),

            ("09:00", "09:00 AM - 09:15 AM"),
            ("09:15", "09:15 AM - 09:30 AM"),
            ("09:30", "09:30 AM - 09:45 AM"),
            ("09:45", "09:45 AM - 10:00 AM"),

            ("10:00", "10:00 AM - 10:15 AM"),
            ("10:15", "10:15 AM - 10:30 AM"),
            ("10:30", "10:30 AM - 10:45 AM"),
            ("10:45", "10:45 AM - 11:00 AM"),

            ("11:00", "11:00 AM - 11:15 AM"),
            ("11:15", "11:15 AM - 11:30 AM"),
            ("11:30", "11:30 AM - 11:45 AM"),
            ("11:45", "11:45 AM - 12:00 PM"),

            ("12:00", "12:00 PM - 12:15 PM"),
            ("12:15", "12:15 PM - 12:30 PM"),
            ("12:30", "12:30 PM - 12:45 PM"),
            ("12:45", "12:45 PM - 01:00 PM"),

            ("13:00", "01:00 PM - 01:15 PM"),
            ("13:15", "01:15 PM - 01:30 PM"),
            ("13:30", "01:30 PM - 01:45 PM"),
            ("13:45", "01:45 PM - 02:00 PM"),
        ]

        self.fields["appointment_time"].choices = time_choices

        if selected_doctor:

            self.fields["doctor"].initial = selected_doctor

            self.fields["doctor"].widget = forms.HiddenInput()


# =========================================================
# APPOINTMENT STATUS FORM
# =========================================================

class AppointmentStatusForm(forms.ModelForm):

    class Meta:
        model = Appointment

        fields = [
            "status",
        ]


# =========================================================
# PATIENT SIGNUP FORM
# =========================================================

class PatientSignupForm(UserCreationForm):

    email = forms.EmailField(
        widget=forms.EmailInput(
            attrs={
                "class": "form-control",
                "placeholder": "Enter your email",
                "autocomplete": "email",
            }
        )
    )

    class Meta:
        model = User

        fields = [
            "username",
            "email",
            "password1",
            "password2",
        ]

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        self.fields["username"].widget.attrs.update({
            "class": "form-control",
            "placeholder": "Enter username",
            "autocomplete": "username",
        })

        self.fields["password1"].widget = forms.PasswordInput(
            attrs={
                "class": "form-control password-input",
                "placeholder": "Enter password",
                "autocomplete": "new-password",
            }
        )

        self.fields["password2"].widget = forms.PasswordInput(
            attrs={
                "class": "form-control password-input",
                "placeholder": "Confirm password",
                "autocomplete": "new-password",
            }
        )


# =========================================================
# PATIENT LOGIN FORM
# =========================================================

class PatientLoginForm(AuthenticationForm):

    username = forms.CharField(
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Enter username",
                "autocomplete": "username",
            }
        )
    )

    password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control password-input",
                "placeholder": "Enter password",
                "autocomplete": "current-password",
            }
        )
    )