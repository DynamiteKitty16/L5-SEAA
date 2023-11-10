from django.contrib import admin
from .models import UserProfile, AttendanceRecord, LeaveRequest

# Register models.
admin.site.register(UserProfile)
admin.site.register(AttendanceRecord)
admin.site.register(LeaveRequest)
