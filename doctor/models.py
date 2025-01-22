from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError
import base64
from django.contrib.auth.models import User

class Appointment(models.Model):
    first_name = models.CharField(max_length=100, null=True, blank=True)
    last_name = models.CharField(max_length=100, null=True, blank=True)
    email = models.EmailField(max_length=254, null=True, blank=True)
    phone = models.CharField(max_length=20, null=True, blank=True)
    request = models.TextField(default='No request provided')
    accepted = models.BooleanField(default=False)
    rejected = models.BooleanField(default=False)
    accepted_date = models.DateTimeField(null=True, blank=True)
    meet_link = models.URLField(max_length=500, blank=True, null=True)
    created_at = models.DateTimeField(auto_created=True, default=timezone.now)

class TherapistProfile(models.Model):
    MAX_PROFILES_PER_USER = 3
    
    username = models.CharField(max_length=100)
    name = models.CharField(max_length=200)
    title = models.CharField(max_length=200)
    location = models.CharField(max_length=200)
    bio = models.TextField()
    # Stores image as binary data
    image = models.BinaryField(null=True, blank=True)
    # Stores the image filename
    image_filename = models.CharField(max_length=255, null=True, blank=True)
    # Stores the image MIME type
    image_content_type = models.CharField(max_length=100, null=True, blank=True)
    twitter = models.URLField(max_length=200, null=True, blank=True)
    linkedin = models.URLField(max_length=200, null=True, blank=True)
    facebook = models.URLField(max_length=200, null=True, blank=True)
    website = models.URLField(max_length=200, null=True, blank=True)
    profile_order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def clean(self):
        base_username = self.username.split('_')[0]
        existing_profiles = TherapistProfile.objects.filter(username__startswith=base_username)
        
        if not self.pk:  # Only check on creation
            if existing_profiles.count() >= self.MAX_PROFILES_PER_USER:
                raise ValidationError(f'Maximum limit of {self.MAX_PROFILES_PER_USER} profiles per user has been reached.')

    def save(self, *args, **kwargs):
        self.full_clean()
        
        # Ensure image content type has a default value
        if self.image and not self.image_content_type:
            self.image_content_type = 'image/jpeg'
            
        super().save(*args, **kwargs)

    def get_image_base64(self):
        """Return base64 encoded image data for use in templates"""
        try:
            if not self.image:
                return None
                
            # Handle bytes data from BinaryField
            if isinstance(self.image, bytes):
                return base64.b64encode(self.image).decode('utf-8')
            # Handle memoryview data (which Django might return)
            elif isinstance(self.image, memoryview):
                return base64.b64encode(self.image.tobytes()).decode('utf-8')
            else:
                return None
        except Exception as e:
            print(f"Error encoding image: {e}")
            return None

    def __str__(self):
        return f"{self.name} ({self.username})"
    
class Testimonial(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Testimonial by {self.user.username}"

    class Meta:
        ordering = ['created_at']

class AllAppointment(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    request = models.TextField()
    accepted = models.BooleanField(default=False)
    meet_link = models.URLField(blank=True, null=True)

    def __str__(self):
        return f"Appointment by {self.user.username} on {self.created_at}"
