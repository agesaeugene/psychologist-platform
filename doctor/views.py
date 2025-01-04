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
import os
from django.conf import settings
from django.contrib.auth import authenticate, login
from django.views import View


class HomeTemplateView(TemplateView):
    template_name = "index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Get all therapist profiles ordered by profile_order
        context['therapists'] = TherapistProfile.objects.all().order_by('profile_order')
        return context

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
            return TherapistProfile.objects.filter(username=self.request.user.username).first()
        except Exception as e:
            messages.error(self.request, f"Error retrieving profile: {str(e)}")
            return None

    def form_valid(self, form):
        try:
            if form.instance.pk:
                # Updating existing profile
                existing_profile = TherapistProfile.objects.get(pk=form.instance.pk)
                form.instance.username = existing_profile.username
                form.instance.profile_order = existing_profile.profile_order
            else:
                # Creating new profile
                existing_profiles_count = TherapistProfile.objects.filter(
                    username=self.request.user.username
                ).count()
                base_username = self.request.user.username
                form.instance.username = f"{base_username}_{existing_profiles_count + 1}" if existing_profiles_count > 0 else base_username
                form.instance.profile_order = existing_profiles_count + 1
            
            if 'image' in self.request.FILES:
                try:
                    if form.instance.pk and form.instance.image:
                        old_image_path = form.instance.image.path
                        if os.path.isfile(old_image_path):
                            os.remove(old_image_path)
                    form.instance.image = self.request.FILES['image']
                except Exception as img_error:
                    messages.warning(self.request, "There was an issue with the image upload, but the profile was saved.")

            response = super().form_valid(form)
            
            if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'status': 'success',
                    'message': 'Profile updated successfully!',
                    'redirect_url': reverse_lazy('edit-profile') + f'?profile_id={form.instance.id}',
                    'image_url': form.instance.image.url if form.instance.image else None
                })
            
            messages.success(self.request, "Profile saved successfully!")
            return response

        except Exception as e:
            if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'status': 'error',
                    'message': str(e)
                }, status=400)
            messages.error(self.request, f"Error saving profile: {str(e)}")
            return self.form_invalid(form)

    def post(self, request, *args, **kwargs):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' and request.POST.get('delete_profile'):
            try:
                profile_id = request.POST.get('profile_id')
                profile = get_object_or_404(TherapistProfile, id=profile_id)
                
                if profile.image:
                    try:
                        if os.path.isfile(profile.image.path):
                            os.remove(profile.image.path)
                    except Exception as img_del_error:
                        print(f"Error deleting image: {str(img_del_error)}")
                
                profile.delete()

                remaining_profiles = TherapistProfile.objects.filter(
                    username__startswith=self.request.user.username
                ).order_by('profile_order')
                
                for index, profile in enumerate(remaining_profiles, 1):
                    profile.profile_order = index
                    profile.username = self.request.user.username if index == 1 else f"{self.request.user.username}_{index}"
                    profile.save()

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

        return super().post(request, *args, **kwargs)
        

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': 'Create Profile' if self.request.GET.get('new_profile') else 'Edit Profile',
            'therapists': TherapistProfile.objects.filter(
                username__startswith=self.request.user.username
            ).order_by('profile_order'),
            'is_new_profile': bool(self.request.GET.get('new_profile')),
            'media_url': settings.MEDIA_URL
        })

        profile_id = self.request.GET.get('profile_id')
        if profile_id:
            context['selected_profile'] = get_object_or_404(TherapistProfile, id=profile_id)

        return context
    
class CustomAdminLoginView(View):
    template_name = 'admin/custom_login.html'
    
    def get(self, request):
        # If user is already authenticated and is staff, redirect to home
        if request.user.is_authenticated and request.user.is_staff:
            return redirect('home')
        return render(request, self.template_name)
    
    def post(self, request):
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        # Use Django's authenticate function to check credentials
        user = authenticate(request, username=username, password=password)
        
        if user is not None and user.is_staff:
            login(request, user)
            # Redirect to home page where manage and edit sections will be visible
            return redirect('home')
        else:
            messages.error(request, 'Invalid credentials or insufficient permissions')
            return render(request, self.template_name)