from django import forms
from .models import UserProfile, AttendanceRecord, LeaveRequest
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import UserProfile
from django.core.validators import RegexValidator

# Define any regex validators for Django
name_regex = RegexValidator(r'^[a-zA-Z\s]+$', 'Only letters and spaces are allowed.')

# Putting CustomUserCreationForm ahead as UserProfileForm below is a dependency
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


class UserProfileForm(forms.ModelForm):
    first_name = forms.CharField(max_length=30, validators=[name_regex])
    last_name = forms.CharField(max_length=30, validators=[name_regex])
    email = forms.EmailField()

    def clean_email(self):
        email = self.cleaned_data['email']
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("This email address is already in use.")
        return email

    class Meta:
        model = UserProfile
        fields = ['first_name', 'last_name', 'email']

    def save(self, commit=True):
        user_profile = super(UserProfileForm, self).save(commit=False)
        user = user_profile.user
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
            user_profile.save()
        return user_profile
    
class AttendanceRecordForm(forms.ModelForm):
    class Meta:
        model = AttendanceRecord
        fields = '__all__'

class LeaveRequestForm(forms.ModelForm):
    class Meta:
        model = LeaveRequest
        fields = '__all__'
        