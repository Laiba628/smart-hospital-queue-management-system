from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("register/", views.patient_register, name="register"),
    path("doctors/", views.doctor_list, name="doctor_list"),
    path("appointment/", views.book_appointment, name="book_appointment"),
    path("appointment/<int:doctor_id>/", views.book_appointment, name="book_appointment_doctor"),

    path("queue-dashboard/", views.queue_dashboard, name="queue_dashboard"),
    path("update-appointment/<int:pk>/", views.update_appointment, name="update_appointment"),
    path("doctor/<int:pk>/",views.doctor_detail,name="doctor_detail",),

    # Authentication
    path("signup/", views.patient_signup, name="signup"),
    path("login/", views.patient_login, name="login"),
    path("logout/", views.patient_logout, name="logout"),

    # Token Slip
    path("token-slip/<int:pk>/", views.token_slip, name="token_slip"),
    path("my-appointments/",views.my_appointments,name="my_appointments",),
    path(
    "cancel-appointment/<int:pk>/",views.cancel_appointment,name="cancel_appointment",),
    path("profile/", views.profile, name="profile"),
]