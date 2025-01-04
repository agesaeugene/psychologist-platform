from django.urls import path
from .views import (
    HomeTemplateView,
    AppointmentTemplateView,
    ManageAppointmentTemplateView,
    EditProfileTemplateView,
    CustomAdminLoginView
)

urlpatterns = [
    path("", HomeTemplateView.as_view(), name="home"),
    path("make-an-appointment/", AppointmentTemplateView.as_view(), name="appointment"),
    path("manage-appointments/", ManageAppointmentTemplateView.as_view(), name="manage"),
    path("edit-profile/", EditProfileTemplateView.as_view(), name="edit-profile"),
    path("administrator/login/", CustomAdminLoginView.as_view(), name="custom_admin_login"),
]
