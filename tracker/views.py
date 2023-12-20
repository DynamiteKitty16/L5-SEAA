from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.forms import AuthenticationForm
from django.conf import settings
from .forms import CustomUserCreationForm
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.utils import timezone
from .models import AttendanceRecord
from datetime import datetime, timedelta
from django.views.decorators.csrf import csrf_exempt

import json

@login_required
def home(request):
    return render(request, 'tracker/home.html')

def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            user.backend = settings.AUTHENTICATION_BACKENDS[0] # Using the Attendance Tracker authentication
            login(request, user)
            # Redirect to the registration success page
            return redirect('registration_success')
        else:
            # If the form is not valid, render the same page with the form
            # This will include the form errors
            return render(request, 'tracker/register.html', {'form': form})
    else:
        form = CustomUserCreationForm()

    return render(request, 'tracker/register.html', {'form': form})

def registration_success(request):
    return render(request, 'tracker/registration_success.html')

# Set this up as a custom one instead of using Django's inbuilt form function for this as
# Want users to land on the login page but have the option to register.

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect('home')
        else:
            if User.objects.filter(username=username).exists() or User.objects.filter(email=username).exists():
                messages.error(request, "Incorrect password.")
            else:
                messages.error(request, "Account not found with the provided username/email.")

    return render(request, 'tracker/login.html')

# Handle session time out warnings

def session_timeout_warning(request):
    last_activity = request.session.get('last_activity', timezone.now().timestamp())
    current_time = timezone.now().timestamp()
    time_elapsed = current_time - last_activity
    time_left = max(settings.SESSION_COOKIE_AGE - time_elapsed, 0)
    return JsonResponse({'time_left': time_left})

# Add a login button on the timeout response 

@login_required
def extend_session(request):
    request.session.modified = True
    return JsonResponse({'status': 'success'})

@login_required
def calendar(request): 

    # Have not included in my model / forms but user.date_joined is taken from Django default 'User' model   
    registration_date = request.user.date_joined.date()
    current_date = datetime.now().date()
    one_year_ago = current_date - timedelta(days=365)

    # Set the start date for the calendar as the later of the two dates
    start_date = max(registration_date, one_year_ago)

    # Format start_date as a string in format 'YYYY-MM-DD'
    formatted_start_date = start_date.strftime('%Y-%m-%d')

    # Get attendance records for the user
    # For new users this will return empty queryset
    attendance_records = AttendanceRecord.objects.filter(user=request.user, date__range=[start_date, current_date])

    # Convert records to a format suitable for FullCalendar
    events = [{'title': record.type, 'start': record.date} for record in attendance_records]

    # Set the editable dates
    start_editable_date = current_date - timedelta(days=7)  # One week ago
    end_editable_date = current_date + timedelta(days=14)  # Two weeks ahead

    # Format dates for passing to template
    formatted_start_editable_date = start_editable_date.strftime('%Y-%m-%d')
    formatted_end_editable_date = end_editable_date.strftime('%Y-%m-%d')

    context = {
        'start_date': formatted_start_date,
        'events': events,
        'start_editable_date': formatted_start_editable_date,
        'end_editable_date': formatted_end_editable_date,
    }
    return render(request, 'tracker/calendar.html', context)


# View for handling the AJAX and storing of Attendence data records
@csrf_exempt
@login_required
def handle_attendance(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        date_str = data.get('date')
        attendance_type = data.get('type')

        # Validate the data
        try:
            date = datetime.strptime(date_str, '%Y-%m-%d').date()
            if attendance_type not in ['WFH', 'IO', 'BT', 'T']:
                raise ValueError("Invalid attendance type")
        except ValueError as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

        # Create or update the attendance record
        record, created = AttendanceRecord.objects.update_or_create(
            user=request.user,
            date=date,
            defaults={'type': attendance_type}
        )

        # Save the record
        record.save()

        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error'}, status=400)