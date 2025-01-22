from django.urls import path
from .views import (
    HomeTemplateView,
    AppointmentTemplateView,
    ManageAppointmentTemplateView,
    EditProfileTemplateView,
    CustomAdminLoginView,
    login_user,
    register_user,
    logout_user,
    AllAppointmentsView,
    reject_appointment
    
)

urlpatterns = [
    path("", HomeTemplateView.as_view(), name="home"),
    path("make-an-appointment/", AppointmentTemplateView.as_view(), name="appointment"),
    path("manage-appointments/", ManageAppointmentTemplateView.as_view(), name="manage"),
    path("edit-profile/", EditProfileTemplateView.as_view(), name="edit-profile"),
    path("administrator/login/", CustomAdminLoginView.as_view(), name="custom_admin_login"),

    path("login/", login_user, name="login"),
    path("register/", register_user, name="register"),
    path("logout/", logout_user, name="logout"),
    path('appointments/', AllAppointmentsView.as_view(), name='appointments'),
    path('reject-appointment/<int:appointment_id>/', reject_appointment, name='reject-appointment'),
]

