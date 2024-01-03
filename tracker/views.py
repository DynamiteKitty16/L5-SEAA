from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
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
from django.db.models import Case, When, Value, IntegerField, Count
from .leave_utils import get_overlapping_request, update_calendar_event, cancel_overlapping_requests
from django.core import serializers

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
            return render(request, 'tracker/register.html', {'form': form, 'disable_session_timeout': True})
    else:
        form = CustomUserCreationForm()

    return render(request, 'tracker/register.html', {'form': form, 'disable_session_timeout': True})

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

    return render(request, 'tracker/login.html', {'disable_session_timeout': True})

# Custom logout
@login_required
def custom_logout(request):
    logout(request)
    return render(request, 'tracker/logout_success.html')


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

    events = []
    for record in attendance_records:
        is_approved_leave = LeaveRequest.objects.filter(
            user=request.user,
            start_date__lte=record.date,
            end_date__gte=record.date,
            status='Approved'
        ).exists()
        events.append({
            # Convert records to a format suitable for FullCalendar
            'title': record.type,
            'start': record.date.strftime('%Y-%m-%d'),
            'isApprovedLeave': is_approved_leave  # Restricts changing the event if it is an approved leave
        })
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
        
        # Check if the date corresponds to an approved leave
        is_approved_leave = LeaveRequest.objects.filter(
            user=request.user,
            start_date__lte=date,
            end_date__gte=date,
            status='Approved'
        ).exists()

        if is_approved_leave and attendance_type in ['AL', 'NWD', 'FL']:
            # Prevent changing attendance type for approved leaves
            return JsonResponse({'status': 'error', 'message': 'Cannot change attendance for approved leave.'}, status=403)

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

            return redirect('requests')

    # Updated queryset with custom ordering where pending is at the top and then sorted by created date
    user_requests = LeaveRequest.objects.filter(user=request.user).annotate(
        custom_order=Case(
            When(status='Pending', then=Value(1)),
            default=Value(2),
            output_field=IntegerField(),
        )
    ).order_by('custom_order', '-created_at')

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

                # Save the new request WITHOUT updating the calendar
                new_leave_request.save()

        return redirect('manager_self_requests')

    user_requests = LeaveRequest.objects.filter(user=request.user).annotate(
        custom_order=Case(
            When(status='Pending', then=Value(1)),
            default=Value(2),
            output_field=IntegerField(),
        )
    ).order_by('custom_order', '-created_at')

    # Add 'show_buttons' attribute based on the condition
    for req in user_requests:
        req.show_buttons = req.status in ['Pending', 'Approved']

    context = {
        'form': form,
        'user_requests': user_requests,
    }
    return render(request, 'tracker/manager_self_request.html', context)


# Manager view to review requests
@login_required
def manager_dashboard_view(request):
    # Ensure the user is a manager
    if not request.user.userprofile.is_manager:
        return redirect('home_view')

    # Get the list of employees managed by the current user
    managed_users = User.objects.filter(userprofile__manager=request.user.userprofile)

    # Fetch pending leave requests for each managed user
    managed_requests = {}
    for user in managed_users:
        managed_requests[user] = LeaveRequest.objects.filter(user=user).annotate(
            custom_order=Case(
                When(status='Pending', then=Value(1)),
                default=Value(2),
                output_field=IntegerField(),
            )
        ).order_by('custom_order', '-created_at')

    context = {
        'managed_users': managed_users,
        'managed_requests': managed_requests,
    }

    return render(request, 'tracker/manage_requests.html', context)


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


# View for returning the pending leave requests for a selected employee using JSON

from django.http import JsonResponse

@login_required
def get_employee_requests(request, employee_id):
    if not request.user.userprofile.is_manager:
        return JsonResponse({'error': 'Unauthorized'}, status=403)

    try:
        employee = User.objects.get(id=employee_id)
        current_date = timezone.now().date()

        # Fetch all requests for the employee
        all_requests = LeaveRequest.objects.filter(user_id=employee_id)

        # Auto-cancel outdated requests
        outdated_requests = all_requests.filter(start_date__lte=current_date, status='Pending')
        for req in outdated_requests:
            req.status = 'Cancelled'
            req.save()

        # Continue with existing logic
        requests = all_requests.annotate(
            custom_order=Case(
                When(status='Pending', then=Value(1)),
                When(status='Approved', then=Value(2)),
                When(status='Denied', then=Value(3)),
                default=Value(4),
                output_field=IntegerField(),
            )
        ).order_by('custom_order', '-start_date')
        
        # Manually serialize the data
        data = [{
            'id': req.id,
            'leave_type': req.leave_type,
            'start_date': req.start_date.strftime('%Y-%m-%d'),
            'end_date': req.end_date.strftime('%Y-%m-%d'),
            'status': req.status
        } for req in requests]

        return JsonResponse(data, safe=False)
    except User.DoesNotExist:
        return JsonResponse({'error': 'Employee not found'}, status=404)


def approve_leave_request(request, request_id):
    if request.method == 'POST':
        leave_request = LeaveRequest.objects.get(id=request_id)
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

        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error'}, status=400)

# View for denying request
@login_required
@csrf_exempt
def deny_leave_request(request, request_id):
    if request.method == 'POST':
        leave_request = LeaveRequest.objects.get(id=request_id)
        leave_request.status = 'Denied'
        leave_request.save()
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error'}, status=400)

# View for cancelling an approved leave request
@login_required
@csrf_exempt
def cancel_leave_request(request):
    if request.method == 'POST':
        try:
            request_id = int(request.POST.get('request_id'))
        except (TypeError, ValueError):
            return JsonResponse({'status': 'error', 'message': 'Invalid request ID.'}, status=400)

        leave_request = get_object_or_404(LeaveRequest, id=request_id)

        # Check if the user is either the owner of the request or a manager
        if request.user == leave_request.user or request.user.userprofile.is_manager:
            # Allow cancellation for pending requests by the owner or any request by a manager
            if leave_request.status == 'Pending' or request.user.userprofile.is_manager:
                # Store the current status before updating it
                current_status = leave_request.status

                leave_request.status = 'Cancelled'
                leave_request.save()

                # If the user is a manager and the request was approved, delete related attendance records
                if request.user.userprofile.is_manager and current_status == 'Approved':
                    AttendanceRecord.objects.filter(
                        user=leave_request.user, 
                        date__range=[leave_request.start_date, leave_request.end_date]
                    ).delete()

                return JsonResponse({'status': 'success', 'message': 'Leave request cancelled successfully.'})
            else:
                return JsonResponse({'status': 'error', 'message': 'Request status does not allow cancellation.'}, status=403)
        else:
            return JsonResponse({'status': 'error', 'message': 'Unauthorized to cancel this request.'}, status=403)

    return JsonResponse({'status': 'error', 'message': 'Invalid request method.'}, status=400)



# This is used by the manager view due to the issues with having different POST data on the pages
@login_required
def cancel_leave_request_from_manage(request, request_id):
    # Fetch the leave request object
    leave_request = get_object_or_404(LeaveRequest, id=request_id)

    # Check if the user is a manager and authorized to cancel the request
    if request.user.userprofile.is_manager:
        # Check if the request can be cancelled
        if leave_request.status in ['Pending', 'Approved']:
            leave_request.status = 'Cancelled'
            leave_request.save()

            # Remove corresponding AttendanceRecord entries
            AttendanceRecord.objects.filter(user=leave_request.user, date__range=[leave_request.start_date, leave_request.end_date]).delete()

            return JsonResponse({'status': 'success', 'message': 'Leave request cancelled successfully and attendance records deleted.'})
        else:
            return JsonResponse({'status': 'error', 'message': 'Request cannot be cancelled'}, status=400)
    else:
        return JsonResponse({'status': 'error', 'message': 'Unauthorized to cancel this request.'}, status=403)


# View for creating graphs to be used for chart and percentage information for the manager to review staff availability
@login_required
def staff_attendance_view(request):
    # Ensure only managers can access this page
    if not request.user.userprofile.is_manager:
        return redirect('home')

    # Initialize variables
    managed_employees = User.objects.filter(userprofile__manager=request.user.userprofile)
    graph_data = {}

    # Populate graph data for each managed employee
    for employee in managed_employees:
        graph_data[employee.username] = get_graph_data_for_user(employee)

    # Include manager's own data
    graph_data['me'] = get_graph_data_for_user(request.user)

    context = {
        'managed_employees': managed_employees,
        'graph_data': graph_data,
    }
    return render(request, 'tracker/staff_attendance.html', context)

def get_graph_data_for_user(user):
    # Define the current month and year
    current_month = timezone.now().month
    current_year = timezone.now().year

    # Fetch attendance records for the current month
    monthly_records = AttendanceRecord.objects.filter(
        user=user, 
        date__year=current_year, 
        date__month=current_month
    ).values('type').annotate(count=Count('type'))

    # Fetch attendance records for the current year
    yearly_records = AttendanceRecord.objects.filter(
        user=user, 
        date__year=current_year
    ).values('type').annotate(count=Count('type'))

    # Convert querysets to dictionaries for easier manipulation
    monthly_data = {record['type']: record['count'] for record in monthly_records}
    yearly_data = {record['type']: record['count'] for record in yearly_records}

    # Calculate total counts
    total_monthly = sum(monthly_data.values())
    total_yearly = sum(yearly_data.values())

    # Convert counts to percentages
    monthly_percentages = {k: (v / total_monthly * 100) for k, v in monthly_data.items() if total_monthly > 0}
    yearly_percentages = {k: (v / total_yearly * 100) for k, v in yearly_data.items() if total_yearly > 0}

    # Prepare the data for Chart.js
    graph_data = {
        'monthly': {
            'labels': list(monthly_percentages.keys()),
            'data': list(monthly_percentages.values())
        },
        'yearly': {
            'labels': list(yearly_percentages.keys()),
            'data': list(yearly_percentages.values())
        }
    }

    return graph_data

@login_required
def staff_attendance_data(request):
    username = request.GET.get('user')

    # Handle the 'me' option by using the current user's data
    if username == 'me':
        user = request.user
    else:
        user = User.objects.get(username=username)

    graph_data = get_graph_data_for_user(user)
    return JsonResponse(graph_data)


# Help page for user experience
def help_view(request):
    return render(request, 'tracker/help.html')
