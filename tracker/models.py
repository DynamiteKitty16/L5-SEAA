from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    manager = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='managed_employees')

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
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Pending')
    manager = models.ForeignKey(User, related_name='manager', on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return f"{self.user.username} - {self.leave_type} - {self.start_date} to {self.end_date}"

    def clean(self):
        # Check if the leave request date is in the past
        if self.date < timezone.now().date():
            raise ValidationError('You cannot request leave for a past date.')

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
