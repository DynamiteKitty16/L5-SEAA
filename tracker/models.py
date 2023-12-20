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
        )
    )

class LeaveRequest(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateField()
    status = models.CharField(
        max_length=2,
        choices=(
            ('P', 'Pending'),
            ('A', 'Approved'),
            ('R', 'Rejected'),
        )
    )

    def clean(self):
        # Check if the leave request date is in the past
        if self.date < timezone.now().date():
            raise ValidationError('You cannot request leave for a past date.')

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
