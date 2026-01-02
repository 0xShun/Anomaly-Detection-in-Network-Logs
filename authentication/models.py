from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings


class AdminUser(AbstractUser):
    """Custom admin user model"""
    is_admin = models.BooleanField(default=True)
    last_login_ip = models.GenericIPAddressField(null=True, blank=True)
    login_attempts = models.IntegerField(default=0)
    locked_until = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = 'Admin User'
        verbose_name_plural = 'Admin Users'
    
    def __str__(self):
        return self.username


class UserPreferences(models.Model):
    """User preferences and settings"""
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='preferences')
    
    # Display Settings
    dark_mode = models.BooleanField(default=False)
    compact_view = models.BooleanField(default=False)
    
    # Data Settings
    refresh_interval = models.IntegerField(default=10, help_text="Dashboard refresh interval in seconds")
    items_per_page = models.IntegerField(default=25, help_text="Number of items to display per page")
    timezone = models.CharField(max_length=50, default='UTC')
    
    # Email Notifications
    email_anomalies = models.BooleanField(default=True)
    email_critical = models.BooleanField(default=True)
    email_reports = models.BooleanField(default=False)
    email_updates = models.BooleanField(default=False)
    
    # Browser Notifications
    browser_notifications = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'User Preferences'
        verbose_name_plural = 'User Preferences'
    
    def __str__(self):
        return f"{self.user.username}'s preferences"


# Auto-create UserPreferences when a user is created
@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_preferences(sender, instance, created, **kwargs):
    if created:
        UserPreferences.objects.create(user=instance)


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def save_user_preferences(sender, instance, **kwargs):
    if hasattr(instance, 'preferences'):
        instance.preferences.save()
