# accounts/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models
from django_countries.fields import CountryField
from phonenumber_field.modelfields import PhoneNumberField

class CustomUser(AbstractUser):
    COMPANY_ACCOUNT_TYPES = [
        ('prepaid', 'Prepaid'),
        ('postpaid', 'Postpaid'),
        ('corporate', 'Corporate'),
    ]
    
    # Personal Information
    company_account_number = models.CharField(max_length=20, unique=True)
    phone = PhoneNumberField(blank=True, null=True)
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    country = CountryField(blank=True)
    zip_code = models.CharField(max_length=20, blank=True)
    
    # Account Information
    account_type = models.CharField(max_length=10, choices=COMPANY_ACCOUNT_TYPES, default='prepaid')
    email_verified = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    
    # Preferences
    language = models.CharField(max_length=10, default='en', choices=[('en', 'English'), ('es', 'Spanish')])
    timezone = models.CharField(max_length=50, default='UTC')
    date_format = models.CharField(max_length=20, default='MM/DD/YYYY')
    dark_mode = models.BooleanField(default=False)
    
    # Notification Preferences
    email_notifications = models.BooleanField(default=True)
    sms_notifications = models.BooleanField(default=False)
    billing_reminders = models.BooleanField(default=True)
    service_updates = models.BooleanField(default=True)
    promotional_offers = models.BooleanField(default=False)
    
    # Security
    two_factor_enabled = models.BooleanField(default=False)
    last_password_change = models.DateTimeField(auto_now_add=True)
    
    # Timestamps
    date_joined = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-date_joined']
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['company_account_number']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return f"{self.company_account_number} - {self.username}"
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()
    
    @property
    def billing_address(self):
        parts = [self.address]
        if self.city:
            parts.append(self.city)
        if self.state:
            parts.append(self.state)
        if self.zip_code:
            parts.append(self.zip_code)
        if self.country:
            parts.append(str(self.country))
        return ", ".join(parts) if any(parts) else "No address specified"

class UserSession(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='sessions')
    session_key = models.CharField(max_length=40)
    user_agent = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    location = models.CharField(max_length=100, blank=True)
    device_type = models.CharField(max_length=50, blank=True)
    last_activity = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-last_activity']
    
    def __str__(self):
        return f"{self.user} - {self.device_type} - {self.ip_address}"

class LoginHistory(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='login_history')
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    success = models.BooleanField(default=True)
    reason = models.CharField(max_length=100, blank=True)
    
    class Meta:
        ordering = ['-timestamp']
        verbose_name_plural = 'Login histories'
    
    def __str__(self):
        status = "Success" if self.success else f"Failed: {self.reason}"
        return f"{self.user} - {self.timestamp} - {status}"