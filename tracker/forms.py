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
    email = forms.EmailField(required=True)  # Adding an email field

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")
        # password1 and password2 are confirmation of the password not seperate ones

    def save(self, commit=True):
        user = super(CustomUserCreationForm, self).save(commit=False)
        user.email = self.cleaned_data["email"]
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
        fields = ['user', 'manager', 'first_name', 'last_name', 'email']

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
