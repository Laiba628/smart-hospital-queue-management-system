from datetime import time, timedelta, datetime

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required

from .forms import (
    PatientForm,
    AppointmentForm,
    AppointmentStatusForm,
    PatientSignupForm,
    PatientLoginForm,
)

from .models import Patient, Doctor, Appointment


# =========================================================
# APPOINTMENT SLOT HELPER
# =========================================================

def get_appointment_slots(department, appointment_date):

    slots = []

    if not department or not appointment_date:
        return slots

    current = datetime.combine(
        appointment_date,
        time(9, 0)
    )

    end_datetime = datetime.combine(
        appointment_date,
        time(14, 0)
    )

    while current < end_datetime:

        slot_start = current.time()

        slot_end_datetime = current + timedelta(minutes=15)

        slot_end = slot_end_datetime.time()

        booked = Appointment.objects.filter(
            department=department,
            appointment_date=appointment_date,
            appointment_time__gte=slot_start,
            appointment_time__lt=slot_end,
        ).count()

        available = max(0, 6 - booked)

        slots.append({
            "start": slot_start,
            "end": slot_end,
            "booked": booked,
            "available": available,
            "full": booked >= 6,
        })

        current = slot_end_datetime

    return slots


# =========================================================
# DOCTOR AVAILABLE DAY
# =========================================================

def is_doctor_available_on_date(doctor, appointment_date):

    if not doctor or not appointment_date:
        return False

    day_map = {
        0: "mon",
        1: "tue",
        2: "wed",
        3: "thu",
        4: "fri",
        5: "sat",
        6: "sun",
    }

    selected_day = day_map[appointment_date.weekday()]

    available_days = [
        day.strip().lower()
        for day in (doctor.available_days or "").split(",")
        if day.strip()
    ]

    day_variations = {
        "mon": ["mon", "monday"],
        "tue": ["tue", "tues", "tuesday"],
        "wed": ["wed", "wednesday"],
        "thu": ["thu", "thur", "thurs", "thursday"],
        "fri": ["fri", "friday"],
        "sat": ["sat", "saturday"],
        "sun": ["sun", "sunday"],
    }

    return any(
        day in day_variations[selected_day]
        for day in available_days
    )


# =========================================================
# DOCTOR AVAILABLE TIME
# =========================================================

def get_doctor_available_time(doctor):

    if not doctor or not doctor.available_time:
        return None, None

    try:

        parts = doctor.available_time.split("-")

        if len(parts) != 2:
            return None, None

        start_text = parts[0].strip()
        end_text = parts[1].strip()

        start_time = datetime.strptime(
            start_text,
            "%I:%M %p"
        ).time()

        end_time = datetime.strptime(
            end_text,
            "%I:%M %p"
        ).time()

        return start_time, end_time

    except (ValueError, TypeError):

        return None, None

# =========================================================
# HOME
# =========================================================

def home(request):

    total_doctors = Doctor.objects.count()

    total_patients = Patient.objects.count()

    total_appointments = Appointment.objects.count()

    completed = Appointment.objects.filter(
        status="Completed"
    ).count()

    # -----------------------------------------------------
    # DOCTOR IMAGES FOR HOME PAGE SLIDER
    # -----------------------------------------------------

    doctors = (
        Doctor.objects
        .filter(
            image__isnull=False
        )
        .exclude(
            image=""
        )
        .order_by("id")[:5]
    )

    return render(
        request,
        "home.html",
        {
            "total_doctors": total_doctors,
            "total_patients": total_patients,
            "total_appointments": total_appointments,
            "completed": completed,

            # Doctor images
            "doctors": doctors,
        }
    )
# =========================================================
# PATIENT REGISTRATION / PROFILE
# =========================================================

@login_required
def patient_register(request):

    patient = Patient.objects.filter(
        user=request.user
    ).first()

    if request.method == "POST":

        form = PatientForm(
            request.POST,
            instance=patient
        )

        if form.is_valid():

            patient = form.save(
                commit=False
            )

            patient.user = request.user

            patient.save()

            messages.success(
                request,
                "Patient information saved successfully!"
            )

            return redirect("doctor_list")

    else:

        form = PatientForm(
            instance=patient
        )

        if not patient:

            form.initial["full_name"] = (
                request.user.get_full_name()
                or request.user.username
            )

    return render(
        request,
        "register.html",
        {
            "form": form,
            "patient": patient,
        }
    )


# =========================================================
# DOCTOR LIST
# =========================================================

def doctor_list(request):

    doctors = Doctor.objects.filter(
        is_available=True
    )

    search = request.GET.get("search")

    specialization = request.GET.get(
        "specialization"
    )

    if search:

        doctors = doctors.filter(
            full_name__icontains=search
        )

    if specialization:

        doctors = doctors.filter(
            specialization=specialization
        )

    specializations = (
        Doctor.objects
        .values_list(
            "specialization",
            flat=True
        )
        .distinct()
    )

    return render(
        request,
        "doctor_list.html",
        {
            "doctors": doctors,
            "specializations": specializations,
        }
    )


# =========================================================
# DOCTOR DETAIL
# =========================================================

def doctor_detail(request, pk):

    doctor = get_object_or_404(
        Doctor,
        pk=pk
    )

    return render(
        request,
        "doctor_detail.html",
        {
            "doctor": doctor,
        }
    )


# =========================================================
# BOOK APPOINTMENT
# =========================================================

@login_required
def book_appointment(request, doctor_id=None):

    # -----------------------------------------------------
    # CURRENT LOGGED-IN PATIENT
    # -----------------------------------------------------

    patient = Patient.objects.filter(
        user=request.user
    ).first()

    # -----------------------------------------------------
    # IF PROFILE DOES NOT EXIST
    # -----------------------------------------------------

    if not patient:

        messages.warning(
            request,
            "Please complete your patient profile first."
        )

        return redirect("register")

    # -----------------------------------------------------
    # SELECTED DOCTOR
    # -----------------------------------------------------

    selected_doctor = None

    if doctor_id:

        selected_doctor = get_object_or_404(
            Doctor,
            pk=doctor_id,
            is_available=True
        )

    else:

        selected_doctor_id = request.GET.get(
            "doctor"
        )

        if selected_doctor_id:

            selected_doctor = get_object_or_404(
                Doctor,
                pk=selected_doctor_id,
                is_available=True
            )

    # -----------------------------------------------------
    # SELECTED DATE
    # -----------------------------------------------------

    selected_date = None

    date_value = request.GET.get(
        "appointment_date"
    )

    if date_value:

        try:

            selected_date = datetime.strptime(
                date_value,
                "%Y-%m-%d"
            ).date()

        except ValueError:

            selected_date = None

    # -----------------------------------------------------
    # AVAILABLE SLOTS
    # -----------------------------------------------------

    available_slots = []

    if selected_doctor and selected_date:

        available_slots = get_appointment_slots(
            selected_doctor.specialization,
            selected_date
        )

    # =====================================================
    # POST
    # =====================================================

    if request.method == "POST":

        post_data = request.POST.copy()

        # -------------------------------------------------
        # FORCE CURRENT LOGGED-IN PATIENT
        # -------------------------------------------------

        post_data["patient"] = str(
            patient.id
        )

        # -------------------------------------------------
        # SELECTED DOCTOR
        # -------------------------------------------------

        if selected_doctor:

            post_data["doctor"] = str(
                selected_doctor.id
            )

            form = AppointmentForm(
                post_data,
                selected_doctor=selected_doctor
            )

        else:

            form = AppointmentForm(
                post_data
            )

        # -------------------------------------------------
        # IMPORTANT:
        # ONLY CURRENT PATIENT IN PATIENT FIELD
        # -------------------------------------------------

        if "patient" in form.fields:

            form.fields["patient"].queryset = (
                Patient.objects.filter(
                    id=patient.id
                )
            )

            form.fields["patient"].initial = patient.id

        # =================================================
        # FORM VALIDATION
        # =================================================

        if form.is_valid():

            appointment = form.save(
                commit=False
            )

            doctor = appointment.doctor

            department = doctor.specialization

            appointment_date = (
                appointment.appointment_date
            )

            appointment_time = (
                appointment.appointment_time
            )

            # -------------------------------------------------
            # DOCTOR DAY CHECK
            # -------------------------------------------------

            if not is_doctor_available_on_date(
                doctor,
                appointment_date
            ):

                form.add_error(
                    "appointment_date",
                    f"Dr. {doctor.full_name} is not available "
                    f"on {appointment_date.strftime('%A')}. "
                    f"Available days: {doctor.available_days}."
                )

                available_slots = get_appointment_slots(
                    department,
                    appointment_date
                )

                return render(
                    request,
                    "appointment.html",
                    {
                        "form": form,
                        "selected_doctor": selected_doctor,
                        "available_slots": available_slots,
                        "selected_date": appointment_date,
                        "patient": patient,
                    }
                )

            # -------------------------------------------------
            # DOCTOR TIME CHECK
            # -------------------------------------------------

            doctor_start_time, doctor_end_time = (
                get_doctor_available_time(doctor)
            )

            if doctor_start_time and doctor_end_time:

                if (
                    appointment_time < doctor_start_time
                    or appointment_time >= doctor_end_time
                ):

                    form.add_error(
                        "appointment_time",
                        f"Dr. {doctor.full_name} is available "
                        f"from {doctor_start_time.strftime('%I:%M %p')} "
                        f"to {doctor_end_time.strftime('%I:%M %p')}."
                    )

                    available_slots = get_appointment_slots(
                        department,
                        appointment_date
                    )

                    return render(
                        request,
                        "appointment.html",
                        {
                            "form": form,
                            "selected_doctor": selected_doctor,
                            "available_slots": available_slots,
                            "selected_date": appointment_date,
                            "patient": patient,
                        }
                    )

            # -------------------------------------------------
            # GENERAL OPD TIME
            # -------------------------------------------------

            if (
                appointment_time < time(9, 0)
                or appointment_time >= time(14, 0)
            ):

                form.add_error(
                    "appointment_time",
                    "Appointments are available between "
                    "9:00 AM and 2:00 PM."
                )

                available_slots = get_appointment_slots(
                    department,
                    appointment_date
                )

                return render(
                    request,
                    "appointment.html",
                    {
                        "form": form,
                        "selected_doctor": selected_doctor,
                        "available_slots": available_slots,
                        "selected_date": appointment_date,
                        "patient": patient,
                    }
                )

            # -------------------------------------------------
            # CALCULATE 15 MINUTE SLOT
            # -------------------------------------------------

            total_minutes = (
                appointment_time.hour * 60
                + appointment_time.minute
            )

            start_minutes = 9 * 60

            slot_number = (
                total_minutes - start_minutes
            ) // 15

            slot_start_minutes = (
                start_minutes
                + slot_number * 15
            )

            slot_end_minutes = (
                slot_start_minutes + 15
            )

            slot_start = time(
                slot_start_minutes // 60,
                slot_start_minutes % 60
            )

            slot_end = time(
                slot_end_minutes // 60,
                slot_end_minutes % 60
            )

            # -------------------------------------------------
            # COUNT BOOKED PATIENTS
            # -------------------------------------------------

            total_booked = Appointment.objects.filter(
                department=department,
                appointment_date=appointment_date,
                appointment_time__gte=slot_start,
                appointment_time__lt=slot_end,
            ).count()

            # -------------------------------------------------
            # MAX 6 PATIENTS
            # -------------------------------------------------

            if total_booked >= 6:

                form.add_error(
                    None,
                    f"⚠️ {department} department is FULL "
                    f"for {slot_start.strftime('%I:%M %p')} - "
                    f"{slot_end.strftime('%I:%M %p')}. "
                    f"6 patients are already booked."
                )

                available_slots = get_appointment_slots(
                    department,
                    appointment_date
                )

                return render(
                    request,
                    "appointment.html",
                    {
                        "form": form,
                        "selected_doctor": selected_doctor,
                        "available_slots": available_slots,
                        "selected_date": appointment_date,
                        "patient": patient,
                    }
                )

            # -------------------------------------------------
            # PREVENT SAME PATIENT DUPLICATE BOOKING
            # -------------------------------------------------

            already_booked = Appointment.objects.filter(
                patient=patient,
                doctor=doctor,
                appointment_date=appointment_date,
                appointment_time__gte=slot_start,
                appointment_time__lt=slot_end,
            ).exists()

            if already_booked:

                form.add_error(
                    None,
                    "You already have an appointment "
                    "with this doctor in this time slot."
                )

                available_slots = get_appointment_slots(
                    department,
                    appointment_date
                )

                return render(
                    request,
                    "appointment.html",
                    {
                        "form": form,
                        "selected_doctor": selected_doctor,
                        "available_slots": available_slots,
                        "selected_date": appointment_date,
                        "patient": patient,
                    }
                )

            # -------------------------------------------------
            # TOKEN NUMBER
            # -------------------------------------------------

            token_start = slot_number * 6

            appointment.token_number = (
                token_start
                + total_booked
                + 1
            )

            # -------------------------------------------------
            # SAVE APPOINTMENT
            # -------------------------------------------------

            appointment.patient = patient

            appointment.doctor = doctor

            appointment.department = department

            appointment.save()

            messages.success(
                request,
                "Appointment booked successfully!"
            )

            # -------------------------------------------------
            # DIRECTLY TO TOKEN SLIP
            # -------------------------------------------------

            return redirect(
                "token_slip",
                pk=appointment.pk
            )

    # =====================================================
    # GET
    # =====================================================

    else:

        if selected_doctor:

            form = AppointmentForm(
                initial={
                    "patient": patient.id,
                    "doctor": selected_doctor.id,
                },
                selected_doctor=selected_doctor
            )

        else:

            form = AppointmentForm(
                initial={
                    "patient": patient.id,
                }
            )

        # -------------------------------------------------
        # IMPORTANT:
        # ONLY CURRENT PATIENT SHOULD APPEAR
        # -------------------------------------------------

        if "patient" in form.fields:

            form.fields["patient"].queryset = (
                Patient.objects.filter(
                    id=patient.id
                )
            )

            form.fields["patient"].initial = patient.id

    # =====================================================
    # RENDER
    # =====================================================

    return render(
        request,
        "appointment.html",
        {
            "form": form,
            "selected_doctor": selected_doctor,
            "available_slots": available_slots,
            "selected_date": selected_date,
            "patient": patient,
        }
    )


# =========================================================
# QUEUE DASHBOARD
# =========================================================

@login_required
def queue_dashboard(request):

    # -----------------------------------------------------
    # STAFF / RECEPTION HANDLER SECURITY
    # -----------------------------------------------------

    if not request.user.is_staff:

        messages.error(
            request,
            "You do not have permission to access "
            "the Queue Dashboard."
        )

        return redirect("home")

    # -----------------------------------------------------
    # TODAY'S DATE
    # -----------------------------------------------------

    today = datetime.today().date()

    # -----------------------------------------------------
    # AUTOMATICALLY UPDATE APPOINTMENT STATUS
    #
    # Previous dates  -> Completed
    # Today           -> Confirmed
    # Future dates    -> Pending
    #
    # Cancelled appointments are NEVER changed.
    # -----------------------------------------------------

    # Previous appointments
    Appointment.objects.filter(
        appointment_date__lt=today
    ).exclude(
        status="Cancelled"
    ).update(
        status="Completed"
    )

    # Today's appointments
    # Only Pending appointments become Confirmed.
    # Already Completed appointments remain Completed.
    Appointment.objects.filter(
        appointment_date=today,
        status="Pending"
    ).update(
        status="Confirmed"
    )

    # Future appointments
    # Only Confirmed appointments are moved back to Pending.
    # Completed and Cancelled appointments remain unchanged.
    Appointment.objects.filter(
        appointment_date__gt=today,
        status="Confirmed"
    ).update(
        status="Pending"
    )

    # -----------------------------------------------------
    # SELECTED DATE
    # -----------------------------------------------------

    selected_date = today

    date_value = request.GET.get("date")

    if date_value:

        try:

            selected_date = datetime.strptime(
                date_value,
                "%Y-%m-%d"
            ).date()

        except ValueError:

            selected_date = today

    # -----------------------------------------------------
    # BASE QUERY
    # ONLY SELECTED DATE
    # -----------------------------------------------------

    appointments = (
        Appointment.objects
        .select_related(
            "patient",
            "doctor"
        )
        .filter(
            appointment_date=selected_date
        )
    )

    # -----------------------------------------------------
    # TOKEN FILTER
    # -----------------------------------------------------

    token = request.GET.get("token")

    if token:

        appointments = appointments.filter(
            token_number=token
        )

    # -----------------------------------------------------
    # PATIENT SEARCH
    # -----------------------------------------------------

    patient_search = request.GET.get(
        "patient"
    )

    if patient_search:

        appointments = appointments.filter(
            patient__full_name__icontains=patient_search
        )

    # -----------------------------------------------------
    # DOCTOR FILTER
    # -----------------------------------------------------

    doctor = request.GET.get(
        "doctor"
    )

    if doctor:

        appointments = appointments.filter(
            doctor_id=doctor
        )

    # -----------------------------------------------------
    # STATUS FILTER
    # -----------------------------------------------------

    status = request.GET.get(
        "status"
    )

    if status:

        appointments = appointments.filter(
            status=status
        )

    # -----------------------------------------------------
    # ORDER QUEUE
    # -----------------------------------------------------

    appointments = appointments.order_by(
        "appointment_time",
        "token_number"
    )

    # -----------------------------------------------------
    # STATISTICS
    # FOR SELECTED DATE
    # -----------------------------------------------------

    total_appointments = Appointment.objects.filter(
        appointment_date=selected_date
    ).count()

    pending = Appointment.objects.filter(
        appointment_date=selected_date,
        status="Pending"
    ).count()

    confirmed = Appointment.objects.filter(
        appointment_date=selected_date,
        status="Confirmed"
    ).count()

    completed = Appointment.objects.filter(
        appointment_date=selected_date,
        status="Completed"
    ).count()

    # -----------------------------------------------------
    # DOCTORS
    # -----------------------------------------------------

    doctors = Doctor.objects.all()

    # -----------------------------------------------------
    # PREVIOUS / NEXT DATE
    # -----------------------------------------------------

    previous_date = selected_date - timedelta(
        days=1
    )

    next_date = selected_date + timedelta(
        days=1
    )

    # -----------------------------------------------------
    # TODAY CHECK
    # -----------------------------------------------------

    is_today = selected_date == today

    # -----------------------------------------------------
    # RENDER
    # -----------------------------------------------------

    return render(
        request,
        "queue_dashboard.html",
        {
            "appointments": appointments,
            "doctors": doctors,

            "total_appointments": total_appointments,
            "pending": pending,
            "confirmed": confirmed,
            "completed": completed,

            "selected_date": selected_date,
            "today": today,

            "previous_date": previous_date,
            "next_date": next_date,

            "is_today": is_today,
        }
    )

# =========================================================
# UPDATE APPOINTMENT
# =========================================================

@login_required
def update_appointment(request, pk):

    if not request.user.is_staff:

        messages.error(
            request,
            "You do not have permission to update "
            "appointments."
        )

        return redirect("home")

    appointment = get_object_or_404(
        Appointment,
        pk=pk
    )

    if request.method == "POST":

        form = AppointmentStatusForm(
            request.POST,
            instance=appointment
        )

        if form.is_valid():

            form.save()

            messages.success(
                request,
                "Appointment Updated Successfully!"
            )

            return redirect(
                "queue_dashboard"
            )

    else:

        form = AppointmentStatusForm(
            instance=appointment
        )

    return render(
        request,
        "update_appointment.html",
        {
            "form": form,
            "appointment": appointment,
        }
    )


# =========================================================
# PATIENT SIGNUP
# =========================================================

def patient_signup(request):

    if request.method == "POST":

        form = PatientSignupForm(
            request.POST
        )

        if form.is_valid():

            user = form.save()

            # -------------------------------------------------
            # CREATE PATIENT PROFILE
            # -------------------------------------------------

            Patient.objects.create(
                user=user,
                full_name=(
                    user.get_full_name()
                    or user.username
                ),
                father_name="Not Provided",
                gender="Other",
                phone_number="Not Provided",
                address="Not Provided",
                date_of_birth="2000-01-01",
                cnic=f"TEMP-{user.id}",
            )

            login(
                request,
                user
            )

            messages.success(
                request,
                "Account Created Successfully!"
            )

            # -------------------------------------------------
            # FIX:
            # NEW ACCOUNT ALSO GOES TO DOCTOR LIST
            # because patient profile was already created.
            # -------------------------------------------------

            return redirect(
                "doctor_list"
            )

    else:

        form = PatientSignupForm()

    return render(
        request,
        "signup.html",
        {
            "form": form
        }
    )


# =========================================================
# PATIENT LOGIN
# =========================================================

def patient_login(request):

    if request.method == "POST":

        form = PatientLoginForm(
            request,
            data=request.POST
        )

        if form.is_valid():

            user = form.get_user()

            login(
                request,
                user
            )

            messages.success(
                request,
                "Login Successful!"
            )

            # -------------------------------------------------
            # FIX:
            # ALREADY REGISTERED USER DOES NOT GO TO
            # REGISTRATION PAGE AGAIN.
            # -------------------------------------------------

            patient = Patient.objects.filter(
                user=user
            ).first()

            if patient:

                return redirect(
                    "doctor_list"
                )

            # Only if profile somehow does not exist
            return redirect(
                "register"
            )

    else:

        form = PatientLoginForm()

    return render(
        request,
        "login.html",
        {
            "form": form
        }
    )


# =========================================================
# PATIENT LOGOUT
# =========================================================

@login_required
def patient_logout(request):

    logout(request)

    messages.success(
        request,
        "Logged Out Successfully!"
    )

    return redirect("login")


# =========================================================
# MY APPOINTMENTS
# =========================================================

@login_required
def my_appointments(request):

    patient = Patient.objects.filter(
        user=request.user
    ).first()

    if not patient:

        messages.warning(
            request,
            "Please complete your patient profile first."
        )

        return redirect(
            "register"
        )

    appointments = (
        Appointment.objects
        .filter(patient=patient)
        .select_related(
            "patient",
            "doctor"
        )
        .order_by(
            "appointment_date",
            "appointment_time",
            "token_number"
        )
    )

    return render(
        request,
        "my_appointments.html",
        {
            "appointments": appointments,
            "patient": patient,
        }
    )


# =========================================================
# CANCEL APPOINTMENT
# =========================================================

@login_required
def cancel_appointment(request, pk):

    appointment = get_object_or_404(
        Appointment,
        pk=pk
    )

    # -----------------------------------------------------
    # SECURITY
    # -----------------------------------------------------

    if appointment.patient.user != request.user:

        messages.error(
            request,
            "You can only cancel your own appointment."
        )

        return redirect(
            "my_appointments"
        )

    if request.method != "POST":

        return redirect(
            "my_appointments"
        )

    if appointment.status != "Pending":

        messages.error(
            request,
            "Only pending appointments can be cancelled."
        )

        return redirect(
            "my_appointments"
        )

    appointment.delete()

    messages.success(
        request,
        "Appointment cancelled successfully. "
        "The seat is now available again."
    )

    return redirect(
        "my_appointments"
    )


# =========================================================
# TOKEN SLIP
# =========================================================

@login_required
def token_slip(request, pk):

    appointment = get_object_or_404(
        Appointment,
        pk=pk
    )

    # -----------------------------------------------------
    # SECURITY
    # -----------------------------------------------------

    if (
        appointment.patient.user != request.user
        and not request.user.is_staff
    ):

        messages.error(
            request,
            "You do not have permission to view "
            "this token slip."
        )

        return redirect("home")

    return render(
        request,
        "token_slip.html",
        {
            "appointment": appointment,
        }
    )


# =========================================================
# PATIENT PROFILE
# =========================================================

@login_required
def profile(request):

    patient = Patient.objects.filter(
        user=request.user
    ).first()

    if not patient:

        messages.warning(
            request,
            "Please complete your patient profile first."
        )

        return redirect(
            "register"
        )

    appointments = (
        Appointment.objects
        .filter(patient=patient)
        .select_related(
            "doctor"
        )
        .order_by(
            "-appointment_date",
            "-appointment_time"
        )
    )

    total_appointments = appointments.count()

    pending = appointments.filter(
        status="Pending"
    ).count()

    confirmed = appointments.filter(
        status="Confirmed"
    ).count()

    completed = appointments.filter(
        status="Completed"
    ).count()

    return render(
        request,
        "profile.html",
        {
            "patient": patient,
            "appointments": appointments,
            "total_appointments": total_appointments,
            "pending": pending,
            "confirmed": confirmed,
            "completed": completed,
        }
    )