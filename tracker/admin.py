from django.contrib import admin
from tracker.models import UserProfile, AttendanceRecord, LeaveRequest

# Register models.
admin.site.register(AttendanceRecord)
admin.site.register(LeaveRequest)

# Assing users as managers through django interface
@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'is_manager']