from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, HttpResponseRedirect
from django.views.generic.base import TemplateView
from django.core.mail import EmailMessage
from django.conf import settings
from django.contrib import messages
from .models import Appointment
from django.views.generic.list import ListView
from django.contrib.auth.mixins import LoginRequiredMixin
import datetime
from django.template import Context
from django.template.loader import render_to_string, get_template
import uuid
from django.views.generic.edit import UpdateView
from django.urls import reverse_lazy
from .models import TherapistProfile
from django.http import JsonResponse


class HomeTemplateView(TemplateView):
    template_name = "index.html"

    def post(self, request):
        name = request.POST.get("name")
        email = request.POST.get("email")
        message = request.POST.get("message")

        email = EmailMessage(
            subject= f"{name} from Doctor family.",
            body=message,
            from_email=settings.EMAIL_HOST_USER, 
            to=[settings.EMAIL_HOST_USER],
            reply_to=[email]
        )
        email.send()
        return HttpResponse("Email has been sent successfully")
    
class AppointmentTemplateView(TemplateView):
    template_name = "appointment.html"

    def post(self, request):
        fname = request.POST.get("fname")
        lname = request.POST.get("lname")
        email = request.POST.get("email")
        mobile = request.POST.get("mobile")
        message = request.POST.get("request")

        appointment = Appointment.objects.create(
            first_name=fname,
            last_name=lname,
            email=email,
            phone=mobile,
            request=message,
        )

        appointment.save()

        messages.add_message(request, messages.SUCCESS, f" Thanks {fname} for making an appointment, Our team will reachout ASAP")
        return HttpResponseRedirect(request.path)
    
class ManageAppointmentTemplateView(LoginRequiredMixin, ListView):
    template_name = "manage-appointments.html"
    model = Appointment
    context_object_name = "appointments"
    paginate_by = 3

    def generate_meet_link(self):
        # Generate a unique meeting code
        meeting_code = str(uuid.uuid4())[:8]
        # Create Google Meet link
        meet_link = f"https://meet.google.com/{meeting_code}"
        return meet_link

    def post(self, request):
        date = request.POST.get("date")
        appointment_id = request.POST.get("appointment-id")
        appointment = Appointment.objects.get(id=appointment_id)
        appointment.accepted = True
        appointment.accepted_date = datetime.datetime.now()
        
        # Generate Google Meet link
        meet_link = self.generate_meet_link()
        appointment.meet_link = meet_link
        appointment.save()

        # Format date for email
        formatted_date = datetime.datetime.strptime(date, '%Y-%m-%d').strftime('%B %d, %Y')

        data = {
            "fname": appointment.first_name,
            "date": formatted_date,
            "meet_link": meet_link,
            "time": "9:00 AM"  # You can make this dynamic if needed
        }

        message = get_template('email.html').render(data)
        email = EmailMessage(
            "Your Appointment Confirmation",
            message,
            settings.EMAIL_HOST_USER,
            [appointment.email],
        )
        email.content_subtype = "html"
        email.send()

        messages.add_message(request, messages.SUCCESS, f"Appointment accepted for {appointment.first_name}")
        return HttpResponseRedirect(request.path)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Manage Appointments'
        return context
    
class EditProfileTemplateView(LoginRequiredMixin, UpdateView):
    template_name = 'edit-profile.html'
    model = TherapistProfile
    fields = ['name', 'title', 'location', 'bio', 'image', 'twitter', 'linkedin', 'facebook', 'website']
    success_url = reverse_lazy('edit-profile')

    def get_object(self):
        if self.request.GET.get('new_profile'):
            return None

        profile_id = self.request.GET.get('profile_id')
        if profile_id:
            return get_object_or_404(TherapistProfile, id=profile_id)

        try:
            profile = TherapistProfile.objects.filter(
                username=self.request.user.username
            ).first()

            if not profile:
                profile = TherapistProfile.objects.create(
                    username=self.request.user.username,
                    name=self.request.user.get_full_name() or self.request.user.username,
                    title='Therapist',
                    location='Not specified',
                    bio='No bio provided yet.',
                    profile_order=TherapistProfile.objects.count() + 1
                )
            return profile
        except Exception as e:
            messages.error(self.request, f"Error retrieving profile: {str(e)}")
            return None

    def form_valid(self, form):
        try:
            if not form.instance.pk:
                form.instance.username = self.request.user.username
                form.instance.profile_order = TherapistProfile.objects.count() + 1

            self.object = form.save()

            if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'status': 'success',
                    'message': 'Profile created successfully!' if not form.instance.pk else 'Profile updated successfully!',
                    'redirect_url': self.get_success_url()
                })

            messages.success(self.request, "Profile saved successfully!")
            return super().form_valid(form)

        except Exception as e:
            if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'status': 'error',
                    'message': str(e)
                }, status=400)
            raise

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Create Profile' if self.request.GET.get('new_profile') else 'Edit Profile'
        context['therapists'] = TherapistProfile.objects.all().order_by('profile_order')[:3]
        context['is_new_profile'] = bool(self.request.GET.get('new_profile'))

        profile_id = self.request.GET.get('profile_id')
        if profile_id:
            context['selected_profile'] = get_object_or_404(TherapistProfile, id=profile_id)

        return context

    def post(self, request, *args, **kwargs):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            if request.POST.get('delete_profile'):
                try:
                    profile_id = request.POST.get('profile_id')
                    profile = get_object_or_404(TherapistProfile, id=profile_id)
                    profile.delete()
                    return JsonResponse({
                        'status': 'success',
                        'message': 'Profile deleted successfully!',
                        'redirect_url': reverse_lazy('edit-profile')
                    })
                except Exception as e:
                    return JsonResponse({
                        'status': 'error',
                        'message': str(e)
                    }, status=400)
            else:
                return self.form_valid(form) if form.is_valid() else self.form_invalid(form)
        return super().post(request, *args, **kwargs)
