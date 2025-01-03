from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError

class Appointment(models.Model):
    first_name = models.CharField(max_length=100, null=True, blank=True)
    last_name = models.CharField(max_length=100, null=True, blank=True)
    email = models.EmailField(max_length=254, null=True, blank=True)
    phone = models.CharField(max_length=20, null=True, blank=True)
    request = models.TextField(default='No request provided')
    accepted = models.BooleanField(default=False)
    accepted_date = models.DateTimeField(null=True, blank=True)
    meet_link = models.URLField(max_length=500, blank=True, null=True)
    created_at = models.DateTimeField(auto_created=True, default=timezone.now)
    pass

class TherapistProfile(models.Model):
    MAX_PROFILES_PER_USER = 3
    
    username = models.CharField(max_length=100)  # Remove unique=True
    name = models.CharField(max_length=200)
    title = models.CharField(max_length=200)
    location = models.CharField(max_length=200)
    bio = models.TextField()
    image = models.ImageField(upload_to='therapist_profiles/', null=True, blank=True)
    twitter = models.URLField(max_length=200, null=True, blank=True)
    linkedin = models.URLField(max_length=200, null=True, blank=True)
    facebook = models.URLField(max_length=200, null=True, blank=True)
    website = models.URLField(max_length=200, null=True, blank=True)
    profile_order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)  # Changed from auto_created

    def clean(self):
        base_username = self.username.split('_')[0]
        existing_profiles = TherapistProfile.objects.filter(username__startswith=base_username)
        
        if not self.pk:  # Only check on creation
            if existing_profiles.count() >= self.MAX_PROFILES_PER_USER:
                raise ValidationError(f'Maximum limit of {self.MAX_PROFILES_PER_USER} profiles per user has been reached.')

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.username})"

    class Meta:
        ordering = ['profile_order', 'created_at']