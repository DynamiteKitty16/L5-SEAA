from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from django.db.models import Q

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    manager = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='managed_employees')
    is_manager = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username} - Manager: {self.manager.user.username if self.manager else 'None'}"

# Signal to create or update UserProfile whenever a User instance is saved
@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)
    else:
        instance.userprofile.save()

class AttendanceRecord(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateField()
    type = models.CharField(
        max_length=3,
        choices=(
            ('WFH', 'Working From Home'),
            ('IO', 'In Office'),
            ('AL', 'Annual Leave'),
            ('S', 'Sick'),
            ('FL', 'Flexi Leave'),
            ('NWD', 'Non Working Day'),
            ('BT', 'Business Travel'),
            ('T', 'Training'),
        ),
        # Ideally want the form to be blank for the user to fill out so set the type, will review for analytics / reporting
        null=True,  # Allows the field to be null
        blank=True,  # Allows the Django admin and own forms to leave this field blank
    )

class LeaveRequest(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Approved', 'Approved'),
        ('Denied', 'Denied'),
        ('Cancellation Pending', 'Cancellation Pending'),  # New status
        ('Cancelled', 'Cancelled'),  # Status for successfully cancelled requests
    ]

    TYPE_CHOICES = [
        ('AL', 'Annual Leave'),
        ('FL', 'Flexi Leave'),
        ('NWD', 'Non Working Day'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    leave_type = models.CharField(max_length=3, choices=TYPE_CHOICES)
    start_date = models.DateField()
    end_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    manager = models.ForeignKey(UserProfile, on_delete=models.SET_NULL, null=True, related_name='leave_requests_to_approve')
    
    # New field to track when the request was created
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.leave_type} - {self.start_date} to {self.end_date}"

    def clean(self):
        # Check if the start date is in the past
        if self.start_date < timezone.now().date():
            raise ValidationError('Start date cannot be in the past.')

        # Check if the end date is before the start date
        if self.end_date < self.start_date:
            raise ValidationError('End date cannot be before the start date.')

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
