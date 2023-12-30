from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from .models import UserProfile, LeaveRequest
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.forms import AuthenticationForm
from tracker.forms import LeaveRequestForm, LeaveRequest
from django.conf import settings
from .forms import CustomUserCreationForm
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from .models import AttendanceRecord
from datetime import datetime, timedelta
from django.views.decorators.csrf import csrf_exempt
from django.core.exceptions import ValidationError
from collections import Counter
from django.db.models import Case, When, Value, IntegerField
from .leave_utils import get_overlapping_request, update_calendar_event, cancel_overlapping_requests

import json

# Home page and required home functions

def get_attendance_counts_for_month(user):
    current_month = timezone.now().month
    current_year = timezone.now().year
    records = AttendanceRecord.objects.filter(
        user=user, 
        date__year=current_year, 
        date__month=current_month
    )
    counts = Counter(record.type for record in records)
    return dict(counts)

# Login and Register

@login_required
def home_view(request):
    attendance_counts = get_attendance_counts_for_month(request.user)
    context = {
        'attendance_counts': json.dumps(attendance_counts),
    }
    return render(request, 'tracker/home.html', context)

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


# Views for FullCalendar

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
    attendance_records = AttendanceRecord.objects.filter(user=request.user)

    # Convert records to a format suitable for FullCalendar
    events = [{'title': record.type, 'start': record.date.strftime('%Y-%m-%d')} for record in attendance_records]

    # Convert the events list to a JSON string
    events_json = json.dumps(events)

    # Function to get the start of the week (Monday)
    def get_start_of_week(date):
        return date - timedelta(days=date.weekday())

    # Calculate the start of the current work week
    start_of_current_week = get_start_of_week(current_date)

    # Start editable date is the Monday of the previous week
    start_editable_date = start_of_current_week - timedelta(weeks=1)

    # End editable date is the Friday of the second week ahead
    end_editable_date = start_of_current_week + timedelta(weeks=2, days=4)

    # Format dates for passing to template
    formatted_start_editable_date = start_editable_date.strftime('%Y-%m-%d')
    formatted_end_editable_date = end_editable_date.strftime('%Y-%m-%d')

    context = {
        'start_date': formatted_start_date,
        'events': events_json,
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

# Create count of items in the AttendanceRecord to be used elsewhere

def get_attendance_counts_for_month(user):
    current_month = timezone.now().month
    current_year = timezone.now().year
    records = AttendanceRecord.objects.filter(
        user=user, 
        date__year=current_year, 
        date__month=current_month
    ).exclude(type='Sick')  # Exclude 'Sick' type

    # Count occurrences of each type
    counts = Counter(record.type for record in records)
    return dict(counts)


# Views to handle requests

@login_required
def requests_view(request):
    form = LeaveRequestForm()  # Define form for GET requests

    if request.method == 'POST':
        form = LeaveRequestForm(request.POST)
        if form.is_valid():
            new_leave_request = form.save(commit=False)
            new_leave_request.user = request.user

            # Cancel overlapping requests
            cancel_overlapping_requests(
                request.user,
                new_leave_request.start_date,
                new_leave_request.end_date
            )

            # Save the new request
            new_leave_request.save()

            # Update calendar event
            update_calendar_event(
                request.user,
                new_leave_request.start_date,
                new_leave_request.end_date,
                new_leave_request.leave_type
            )

            return redirect('requests')

    user_requests = LeaveRequest.objects.filter(user=request.user).annotate(
        custom_order=Case(
            When(status='Pending', then=Value(1)),
            When(status='Approved', then=Value(2)),
            When(status='Cancelled', then=Value(3)),
            When(status='Denied', then=Value(4)),
            default=Value(5),
            output_field=IntegerField(),
        )
    ).order_by('custom_order')

    context = {
        'form': form,
        'user_requests': user_requests,
    }
    return render(request, 'tracker/requests.html', context)


# Similiar view to above but for the Manager self-approval

@login_required
def manager_self_requests_view(request):
    # Ensure the user is a manager
    if not request.user.userprofile.is_manager:
        return redirect('home_view')

    form = LeaveRequestForm()  # Define form for GET requests

    if request.method == 'POST':
        if 'approve_request_id' in request.POST:
            # Handle approval action
            request_id = request.POST.get('approve_request_id')
            leave_request = LeaveRequest.objects.get(id=request_id)
            leave_request.status = 'Approved'
            leave_request.save()

            # Cancel overlapping requests
            cancel_overlapping_requests(
                leave_request.user,
                leave_request.start_date,
                leave_request.end_date
            )

            # Update calendar event
            update_calendar_event(
                leave_request.user,
                leave_request.start_date,
                leave_request.end_date,
                leave_request.leave_type
            )
        else:
            # Handle new leave request submission
            form = LeaveRequestForm(request.POST)
            if form.is_valid():
                new_leave_request = form.save(commit=False)
                new_leave_request.user = request.user
                new_leave_request.manager = request.user.userprofile

                # Cancel overlapping requests
                cancel_overlapping_requests(
                    request.user,
                    new_leave_request.start_date,
                    new_leave_request.end_date
                )

                # Save the new request
                new_leave_request.save()

                # Update calendar event
                update_calendar_event(
                    request.user,
                    new_leave_request.start_date,
                    new_leave_request.end_date,
                    new_leave_request.leave_type
                )

        return redirect('manager_self_requests')

    user_requests = LeaveRequest.objects.filter(user=request.user).annotate(
        custom_order=Case(
            When(status='Pending', then=Value(1)),
            When(status='Approved', then=Value(2)),
            When(status='Cancelled', then=Value(3)),
            When(status='Denied', then=Value(4)),
            default=Value(5),
            output_field=IntegerField(),
        )
    ).order_by('custom_order')

    context = {
        'form': form,
        'user_requests': user_requests,
    }
    return render(request, 'tracker/manager_self_request.html', context)


        
# View to handle cancellation for requests

@login_required
def cancel_leave_request(request):
    if request.method == 'POST':
        request_id = request.POST.get('request_id')
        leave_request = get_object_or_404(LeaveRequest, id=request_id, user=request.user)

        # Check if the request can be cancelled and it's at least one day before the start date
        if leave_request.status in ['Pending', 'Approved'] and timezone.now().date() < leave_request.start_date:
            leave_request.status = 'Cancelled'
            leave_request.save()

            # Remove corresponding AttendanceRecord entries
            AttendanceRecord.objects.filter(user=request.user, date__range=[leave_request.start_date, leave_request.end_date]).delete()

            return JsonResponse({'status': 'success', 'message': 'Leave request cancelled successfully.'})
        else:
            return JsonResponse({'status': 'error', 'message': 'This request cannot be cancelled or it is too late to cancel.'}, status=400)

    return JsonResponse({'status': 'error', 'message': 'Invalid request.'}, status=400)



# Manager view to review requests
@login_required
def manager_dashboard_view(request):
    # Ensure the user is a manager
    if not request.user.userprofile.is_manager:
        return redirect('home_view')

    # Get the list of employees managed by the current user
    employees = UserProfile.objects.filter(manager=request.user.userprofile)

    # Fetch leave requests managed by the current user
    managed_requests = LeaveRequest.objects.filter(manager__user=request.user)

    return render(request, 'tracker/manage_requests.html', {
        'employees': employees,
        'managed_requests': managed_requests
    })


# View for approved requests to be updated in the user (requestor) calendar
@login_required
def approve_request(request, request_id):
    leave_request = get_object_or_404(LeaveRequest, id=request_id)

    if request.user.userprofile.is_manager and (leave_request.user == request.user or leave_request.user.manager == request.user):
        leave_request.status = 'Approved'
        leave_request.save()

        # Update or create AttendanceRecord for each day of the leave
        current_date = leave_request.start_date
        while current_date <= leave_request.end_date:
            AttendanceRecord.objects.update_or_create(
                user=leave_request.user,
                date=current_date,
                defaults={'type': leave_request.leave_type}
            )
            current_date += timedelta(days=1)

        messages.success(request, "Leave request approved and attendance records updated.")
    else:
        messages.error(request, "You do not have permission to approve this request.")

    return redirect('manager_self_requests')
