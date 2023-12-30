from django.contrib import admin
from .models import UserProfile, User, AttendanceRecord, LeaveRequest
from .forms import UserProfileAdminForm

# Register models.
admin.site.register(AttendanceRecord)
admin.site.register(LeaveRequest)

# Assing users as managers through django interface
@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'manager', 'is_manager']
    list_editable = ['manager']
    search_fields = ['user__username', 'manager__username']

# Ensure only managers show in the manager dropdown
class UserProfileAdmin(admin.ModelAdmin):
    form = UserProfileAdminForm

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "manager":
            kwargs["queryset"] = User.objects.filter(is_manager=True)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

admin.site.register(UserProfile, UserProfileAdmin)
