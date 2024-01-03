# Availability Tracker

This project is a Django-based web application designed for tracking attendance and managing leave requests. It's structured to provide a user-friendly interface for both employees and managers to handle various aspects of attendance and leave management. The application has been developed using a Django framework and Python 3.10+.

## Features

- **User Authentication**: Custom user authentication system, allowing login with either username or email. These can be dummy emails for the sake of testing the application, however using a real email address will allow the user to use the "forgot password" feature which sends an email for password reset.
- **Attendance Tracking**: Employees can record their attendance, specifying the type of attendance (e.g., Working From Home, In Office, Annual Leave).
- **Leave Management**: Employees can submit leave requests, which managers can approve or deny.
- **Manager Dashboard**: Specialized dashboard for managers to view and manage leave requests.
- **Session Timeout Warning**: Custom middleware for handling session timeouts and inactivity. At 25 minutes the user will be presented with a 'stay logged in button'. After 30 minutes the user will be logged out and redirected to the login page.

## Live Application

The application is hosted and can be accessed at:

- **Main Application**: [https://dynamitekitty16.pythonanywhere.com/](https://dynamitekitty16.pythonanywhere.com/)
- **Admin Dashboard**: [https://dynamitekitty16.pythonanywhere.com/admin/logout/](https://dynamitekitty16.pythonanywhere.com/admin/logout/)

### Admin Access

To access the admin dashboard:

- **Username**: admin
- **Password**: @Pa$$w0rd!

- **Please note:** The admin account should be used responsibly to set user roles and manage the application. Mainly, you need this information so that you can set a user to "is_manager" = true so that they will be able to access manager view, and be available for the drop down manager list under "User profiles".

Axes is also available in the admin section in order to unlock user accounts after 3 attempts.

## Installation and Local Setup
If setup is required in a local environment, please follow this section and the steps below.

1. Clone the repository:
   ```bash
   git clone https://github.com/DynamiteKitty16/L5-SEAA.git

2. Install the required dependencies:
    pip install -r requirements.txt

3. Ensure you are using Python 3.10 and Django 5.0.

4. Set up your database in AttendanceTracker/settings.py. By default, it's configured to use MySQL.

5. Create the database in the virtual environment.
    a. python manage.py makemigrations
    b. python manage.py migrate

6. Run the Django server:
    python manage.py runserver

7. Create a Super User for the Django application:
    python manage.py createsuperuser

8. Access the application through your web browser at 'http://localhost:8000'. 
    Admin can be accessed at 'http://localhost:8000/admin'.

## Known Issues & Areas for Further Development

- **AXES Lockout** Whilst the AXES lockout works, it can be unlocked via the admin or by the user resetting their password, there were issues with configuring the AXES version on PythonAnywhere. For the moment the custom form and view have been removed for the AXES logout. If a user reaches this page, they will have to go back to the login screen and either contact their administrator or use 'forgot password', or wait 1 hour.

- **Manager Notifications** Manager notifications were not set up in this version of the app however it is a planned area of improvement; when a new request is placed to the manager, the manager will receive an email notification to inform them.

- **User Notifications** User notifications were not set up in this version of the app however it is a planned area of improvement; when a manager approves, denies or cancels a request, the user will be notified.

- **Managers to Edit and Delete a Standard Users Whole Calendar** In the event that a user has incorrect information in their yearly calendar that requires ccorrection, a manager will be able to edit the information provided by the user.

## Contact
GitHub: https://github.com/DynamiteKitty16