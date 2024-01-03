from django import forms
from .models import UserProfile, User, AttendanceRecord, LeaveRequest
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.core.validators import RegexValidator
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from django.contrib.auth.forms import AuthenticationForm
from axes.helpers import is_user_locked_out


# Define any regex validators for Django
name_regex = RegexValidator(r'^[A-Z][a-zA-Z\s]*$', 'First name and last name must start with a capital letter and can only contain letters and spaces.')

class CustomUserCreationForm(UserCreationForm):
    first_name = forms.CharField(max_length=30, validators=[name_regex])
    last_name = forms.CharField(max_length=30, validators=[name_regex])
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ("first_name", "last_name", "email", "password1", "password2")

    def __init__(self, *args, **kwargs):
        super(CustomUserCreationForm, self).__init__(*args, **kwargs)
        # This help texture should display as descriptive text below the field
        self.fields['password1'].help_text = 'Your password must be at least 8 characters long, contain at least one number, one uppercase letter, and one special character.'
        self.fields['password2'].help_text = 'Enter the same password as before, for verification.'

    def clean_email(self):
        email = self.cleaned_data['email']
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("This email address address is already in use.")
        return email
    
    def save(self, commit=True):
        user = super(CustomUserCreationForm, self).save(commit=False)
        first_name = self.cleaned_data['first_name']
        last_name = self.cleaned_data['last_name']
        email = self.cleaned_data['email']

        # Generate username
        # Using the counter to add an incrimental number if the username is the same as one that already exsists
        base_username = f"{first_name}.{last_name}".lower()
        username = base_username
        counter = 1
        while User.objects.filter(username=username).exists():
            username = f"{base_username}{counter}"
            counter += 1

        user.username = username
        user.first_name = first_name
        user.last_name = last_name
        user.email = email

        if commit:
            user.save()
        return user

class UserProfileAdminForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super(UserProfileAdminForm, self).__init__(*args, **kwargs)
        # Restrict manager choices to users who are managers
        manager_user_ids = UserProfile.objects.filter(is_manager=True).values_list('user', flat=True)
        self.fields['manager'].queryset = User.objects.filter(id__in=manager_user_ids)
    
class AttendanceRecordForm(forms.ModelForm):
    class Meta:
        model = AttendanceRecord
        fields = '__all__'

class LeaveRequestForm(forms.ModelForm):
    class Meta:
        model = LeaveRequest
        fields = ['leave_type', 'start_date', 'end_date']

    def __init__(self, *args, **kwargs):
        super(LeaveRequestForm, self).__init__(*args, **kwargs)
        self.fields['start_date'].widget.attrs.update({'autocomplete': 'off'})
        self.fields['end_date'].widget.attrs.update({'autocomplete': 'off'})

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get("start_date")
        end_date = cleaned_data.get("end_date")

        # Check if start_date is a weekend
        if start_date and start_date.weekday() >= 5:  # 5 for Saturday, 6 for Sunday
            self.add_error('start_date', _("Start date cannot be on a weekend."))

        # Check if end_date is a weekend
        if end_date and end_date.weekday() >= 5:  # 5 for Saturday, 6 for Sunday
            self.add_error('end_date', _("End date cannot be on a weekend."))
        
        # Check if end_date is before start_date
        if start_date and end_date and end_date < start_date:
            self.add_error('end_date', _("End date cannot be before the start date."))

        return cleaned_data
    
# Custom form to clean up AXES and make the look more consistent
class CustomAuthenticationForm(AuthenticationForm):
    def clean(self):
        username = self.cleaned_data.get('username')

        if username and is_user_locked_out(self.request, username):
            raise ValidationError(
                "Your account is locked because of too many login attempts. "
                "Try resetting your password or contact your administrator to unlock your account."
            )

        return super().clean()        