from django.db import models
from django.utils import timezone
import uuid

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
    

    def __str__(self):
        return f"{self.first_name} {self.last_name}"
    
    class Meta:
        ordering = ['-created_at']

class TherapistProfile(models.Model):
    username = models.CharField(max_length=100, unique=True)
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
    created_at = models.DateTimeField(auto_created=True, default=timezone.now)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['profile_order', 'created_at']
