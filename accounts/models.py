from django.db import models
from django.contrib.auth.models import AbstractUser
from .constants import ROLE_CHOICES,GENDER
from django.utils import timezone
from datetime import timedelta
import random
# Create your models here.


class User(AbstractUser):
    # extra field add
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=10,choices=ROLE_CHOICES)
    is_email_verified = models.BooleanField(default=False)
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']




class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    image = models.ImageField(upload_to='media/user_images/', null=True, blank=True)
    fullname = models.CharField(max_length=200, null=True, blank=True)
    phone_number = models.CharField(max_length=20, null=True, blank=True)
    gender = models.CharField(max_length=15, choices=GENDER, null=True, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    
    # New fields added as TextField
    bio = models.TextField(null=True, blank=True)  # Bio description
    instagram = models.TextField(null=True, blank=True)  # Instagram profile description/handle
    facebook = models.TextField(null=True, blank=True)  # Facebook profile description/handle
    linkedin = models.TextField(null=True, blank=True)  # LinkedIn profile description/handle
    twitter = models.TextField(null=True, blank=True)  # Twitter profile description/handle
    address = models.TextField(null=True, blank=True)  # Address in text form
    website_link = models.TextField(null=True, blank=True)  # Website link or description

    def __str__(self):
        return (
            f"Profile("
            f"User: {self.user.email}, "
            f"Full Name: {self.fullname}, "
            f"Phone: {self.phone_number}, "
            f"Gender: {self.gender}, "
            f"DOB: {self.date_of_birth}, "
            f"Image: {self.image.url if self.image else 'No image'}, "
            f"Bio: {self.bio}, "
            f"Instagram: {self.instagram}, "
            f"Facebook: {self.facebook}, "
            f"LinkedIn: {self.linkedin}, "
            f"Twitter: {self.twitter}, "
            f"Address: {self.address}, "
            f"Website: {self.website_link}"
            f")"
        )





class EmailVerificationOTP(models.Model):                    # 👈 new
    user        = models.ForeignKey(User, on_delete=models.CASCADE)
    otp         = models.CharField(max_length=4)
    created_at  = models.DateTimeField(auto_now_add=True)
    is_verified = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if not self.otp:
            self.otp = str(random.randint(1000, 9999))
        super().save(*args, **kwargs)

    
    def is_expired(self):
        return timezone.now() > self.created_at + timedelta(minutes=5)

    def __str__(self):
        return f"{self.user.email} - {self.otp}"   



class PasswordResetOTP(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    otp = models.CharField(max_length=4)
    created_at = models.DateTimeField(auto_now_add=True)
    is_verified = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if not self.otp:
            self.otp = str(random.randint(1000, 9999))
        super().save(*args, **kwargs)
    
    def __str__(self):
       return f"{self.user.email} - {self.otp}"   
    




