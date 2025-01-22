from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, HttpResponseRedirect
from django.views.generic.base import TemplateView
from django.core.mail import EmailMessage
from django.conf import settings
from django.contrib import messages
from .models import Appointment
from django.views.generic.list import ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.views.generic import TemplateView
from django.utils.decorators import method_decorator
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
from django.contrib.auth import authenticate, authenticate, login, logout
from django.core.mail import send_mail
from django.views import View
from django.contrib.auth.mixins import UserPassesTestMixin
from .models import Testimonial
from .models import AllAppointment
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
def login_user(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        remember = request.POST.get('remember')

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            if not remember:
                request.session.set_expiry(0)  # Session expires when browser closes
            messages.success(request, 'Login successful!')
            return redirect('home')  # This will redirect to index-2.html
        else:
            messages.error(request, 'Invalid username or password!')
            return redirect('login')

    return render(request, 'signin.html')

def register_user(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')

        # Validation checks
        if password != confirm_password:
            messages.error(request, 'Passwords do not match!')
            return redirect('register')

        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists!')
            return redirect('register')

        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email already registered!')
            return redirect('register')

        # Create new user and log them in
        try:
            user = User.objects.create_user(username=username, email=email, password=password)
            user.save()

            # Authenticate and log in the user
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, 'Registration successful! Welcome!')
                return redirect('home')  # Redirect to index-2.html for authenticated users

        except Exception as e:
            messages.error(request, f'Registration failed: {str(e)}')
            return redirect('register')

    return render(request, 'signin.html') 

def logout_user(request):
    logout(request)
    messages.success(request, 'You have been logged out successfully!')
    return redirect('home')

class HomeTemplateView(TemplateView):
    template_name = "index.html"

    def get_template_names(self):
        if self.request.user.is_authenticated:
            return ["index-2.html"]
        return ["index.html"]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Add therapists ordered by profile_order
        context['therapists'] = TherapistProfile.objects.all().order_by('profile_order')

        if self.request.user.is_authenticated:
            # Get all appointments first to debug
            all_appointments = Appointment.objects.all()
            print(f"Debug: Total appointments in database: {all_appointments.count()}")
            print(f"Debug: All appointments emails: {[apt.email for apt in all_appointments]}")
            print(f"Debug: Current user email: {self.request.user.email}")
            
            # Get user appointments
            user_appointments = Appointment.objects.filter(
                email=self.request.user.email
            ).order_by('-created_at')
            
            print(f"Debug: User appointments found: {user_appointments.count()}")
            print(f"Debug: User appointments data: {list(user_appointments.values())}")
            
            context['user_appointments'] = user_appointments
            
            # For admin users
            if self.request.user.is_staff:
                context['count'] = Appointment.objects.filter(accepted=False).count()

        # Adding all testimonials
        context['testimonials'] = Testimonial.objects.all().order_by('-created_at')

        return context

    def post(self, request):
        # Handle Contact Form Submission (Email Sending)
        name = request.POST.get("name")
        email = request.POST.get("email")
        message = request.POST.get("message")

        if name and email and message:
            email_message = EmailMessage(
                subject=f"{name} from Doctor family.",
                body=message,
                from_email=settings.EMAIL_HOST_USER,
                to=[settings.EMAIL_HOST_USER],
                reply_to=[email]
            )
            email_message.send()
            messages.success(request, "Email has been sent successfully!")
            return HttpResponse("Email has been sent successfully")

        # Handle Testimonial Submission
        testimonial_comment = request.POST.get("testimonial")
        if testimonial_comment and request.user.is_authenticated:
            Testimonial.objects.create(user=request.user, comment=testimonial_comment)
            messages.success(request, "Thank you for your feedback!")
            return redirect("home")

        messages.error(request, "Something went wrong. Please try again.")
        return redirect("home")
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

        messages.add_message(request, messages.SUCCESS, f"Thanks {fname} for making an appointment, our team will reach out ASAP")
        return HttpResponseRedirect(request.path)

class AdminRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_staff

    def handle_no_permission(self):
        messages.error(self.request, "You don't have permission to access this page.")
        return redirect('home')

class ManageAppointmentTemplateView(LoginRequiredMixin, ListView):
    template_name = "manage-appointments.html"
    model = Appointment
    context_object_name = "appointments"
    paginate_by = 3
    
    def generate_meet_link(self):
        meeting_code = str(uuid.uuid4())[:8]
        meet_link = f"https://meet.google.com/{meeting_code}"
        return meet_link
    
    def post(self, request, *args, **kwargs):
        appointment_id = request.POST.get("appointment-id")
        action = request.POST.get("action")
        
        if not appointment_id:
            return super().post(request, *args, **kwargs)
            
        try:
            appointment = Appointment.objects.get(id=appointment_id)
            
            if action == "reject":
                # Update the appointment rejection state
                appointment.accepted = False
                appointment.rejected = True  # Mark as rejected
                appointment.save()
                
                # Render the rejection email template
                data = {
                    "fname": appointment.first_name,
                    "date": appointment.created_at.strftime('%B %d, %Y') if appointment.created_at else "N/A",
                }
                message = get_template('email-reject.html').render(data)
                
                # Send rejection email
                email = EmailMessage(
                    "Appointment Rejection Notification",
                    message,
                    settings.EMAIL_HOST_USER,
                    [appointment.email],
                )
                email.content_subtype = "html"
                email.send()
                
                # Success message
                messages.success(request, f"Appointment rejected for {appointment.first_name}. Notification email sent.")
                return HttpResponseRedirect(request.path)
            
            elif action == "accept":
                date = request.POST.get("date")
                if not date:
                    messages.error(request, "Date is required for accepting appointments")
                    return HttpResponseRedirect(request.path)
                
                try:
                    formatted_date = datetime.datetime.strptime(date, '%Y-%m-%d').strftime('%B %d, %Y')
                except ValueError:
                    messages.error(request, "Invalid date format")
                    return HttpResponseRedirect(request.path)
                
                appointment.accepted = True
                appointment.rejected = False  # Ensure rejection is cleared on acceptance
                appointment.accepted_date = datetime.datetime.now()
                
                # Generate Google Meet link
                meet_link = self.generate_meet_link()
                appointment.meet_link = meet_link
                appointment.save()
                
                data = {
                    "fname": appointment.first_name,
                    "date": formatted_date,
                    "meet_link": meet_link,
                    "time": "9:00 AM",  # You can make this dynamic if needed
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
                
                messages.success(request, f"Appointment accepted for {appointment.first_name}")
                return HttpResponseRedirect(request.path)
            
            else:
                # Handle the original direct acceptance flow
                date = request.POST.get("date")
                if not date:
                    messages.error(request, "Date is required for accepting appointments")
                    return HttpResponseRedirect(request.path)
                
                formatted_date = datetime.datetime.strptime(date, '%Y-%m-%d').strftime('%B %d, %Y')
                
                appointment.accepted = True
                appointment.accepted_date = datetime.datetime.now()
                
                # Generate Google Meet link
                meet_link = self.generate_meet_link()
                appointment.meet_link = meet_link
                appointment.save()
                
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
                
        except Appointment.DoesNotExist:
            messages.error(request, "Appointment not found")
            return HttpResponseRedirect(request.path)
        
        return super().post(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Manage Appointments'
        return context



def reject_appointment(request, appointment_id):
    # Get the appointment object
    appointment = get_object_or_404(Appointment, id=appointment_id)

    # Send rejection email to the user
    send_mail(
        subject="Appointment Rejected",
        message=f"Dear {appointment.first_name},\n\n"
                f"Your appointment on {appointment.date} has been rejected.\n"
                f"Please reschedule and book another appointment as soon as possible.\n\n"
                f"Best regards,\nNelson's Appointment Team",
        from_email=settings.EMAIL_HOST_USER,
        recipient_list=[appointment.email],
        fail_silently=False,
    )

    # Update appointment status if required
    appointment.accepted = False
    appointment.save()

    messages.success(request, "The appointment has been rejected and the user has been notified.")
    return redirect('manage_appointments')

class EditProfileTemplateView(LoginRequiredMixin, UpdateView):
    template_name = 'edit-profile.html'
    model = TherapistProfile
    fields = ['name', 'title', 'location', 'bio', 'twitter', 'linkedin', 'facebook', 'website']
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

            # Handle image upload
            if 'image' in self.request.FILES:
                try:
                    image_file = self.request.FILES['image']
                    form.instance.image = image_file.read()
                    form.instance.image_filename = image_file.name
                    form.instance.image_content_type = image_file.content_type
                except Exception as img_error:
                    messages.warning(self.request, "There was an issue with the image upload, but the profile was saved.")

            response = super().form_valid(form)

            if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'status': 'success',
                    'message': 'Profile updated successfully!',
                    'redirect_url': reverse_lazy('edit-profile') + f'?profile_id={form.instance.id}',
                    'image_url': f'data:{form.instance.image_content_type};base64,{form.instance.get_image_base64()}' if form.instance.image else None
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
        # Handle profile deletion via AJAX
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' and request.POST.get('delete_profile'):
            try:
                profile_id = request.POST.get('profile_id')
                profile = get_object_or_404(TherapistProfile, id=profile_id)
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

        # Handle appointment actions
        appointment_id = request.POST.get("appointment-id")
        action = request.POST.get("action")

        if appointment_id:
            try:
                appointment = Appointment.objects.get(id=appointment_id)

                # Handle rejection
                if action == "reject":
                    appointment.accepted = False
                    appointment.save()
                    messages.success(request, f"Appointment rejected for {appointment.first_name}")
                    return HttpResponseRedirect(request.path)

                # Handle acceptance
                else:
                    date = request.POST.get("date")
                    if date:
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

                        messages.success(request, f"Appointment accepted for {appointment.first_name}")
                    else:
                        messages.error(request, "Date is required for accepting appointments")
                    return HttpResponseRedirect(request.path)

            except Appointment.DoesNotExist:
                messages.error(request, "Appointment not found")
                return HttpResponseRedirect(request.path)

        return super().post(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': 'Create Profile' if self.request.GET.get('new_profile') else 'Edit Profile',
            'therapists': TherapistProfile.objects.filter(
                username__startswith=self.request.user.username
            ).order_by('profile_order'),
            'is_new_profile': bool(self.request.GET.get('new_profile')),
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
        
class AllAppointmentsView(ListView):
    model = AllAppointment
    template_name = "appointments.html"
    context_object_name = "appointments"