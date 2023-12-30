from .models import LeaveRequest, AttendanceRecord
from django.core.exceptions import ValidationError
from django.db.models import Q
from datetime import timedelta

def create_calendar_event(user, leave_request):
    # Start from the start_date
    current_date = leave_request.start_date

    # Loop until the current_date exceeds the end_date
    while current_date <= leave_request.end_date:
        # Create an AttendanceRecord for each day
        # Skip weekends
        if current_date.weekday() < 5:  # 0-4 are weekdays
            AttendanceRecord.objects.create(
                user=user,
                date=current_date,
                type=leave_request.leave_type
            )

        # Move to the next day
        current_date += timedelta(days=1)

def get_overlapping_request(user, start_date, end_date):
    # Find any overlapping leave requests
    return LeaveRequest.objects.filter(
        user=user,
        start_date__lte=end_date,
        end_date__gte=start_date
    ).first()

def should_update_existing_attendance(user, start_date, end_date, new_leave_type):
    # Check for existing attendance records in the date range
    existing_records = AttendanceRecord.objects.filter(
        user=user,
        date__range=(start_date, end_date)
    )

    # Logic to determine if existing records should be updated
    for record in existing_records:
        if record.type not in ['AL', 'FL', 'NWD']:  # Assuming 'AL' and 'FL' should not be overwritten
            return True
    return False

def cancel_overlapping_requests(user, start_date, end_date):
    overlapping_requests = LeaveRequest.objects.filter(
        user=user,
        start_date__lte=end_date,
        end_date__gte=start_date,
        status__in=['Approved', 'Pending']  # Consider both approved and pending requests 
    )
    for request in overlapping_requests:
        request.status = 'Cancelled'
        request.save()


def update_calendar_event(user, start_date, end_date, new_leave_type):
    for single_date in (start_date + timedelta(n) for n in range((end_date - start_date).days + 1)):
        # Update existing attendance records
        # Skip weekends
        if single_date.weekday() < 5:  # 0-4 are weekdays
            AttendanceRecord.objects.update_or_create(
                user=user,
                date=single_date,
                defaults={'type': new_leave_type}
            )

