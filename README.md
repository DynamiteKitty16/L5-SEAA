# L5-SEAA (Level 5 Software Engineer & Agile)
# Availability Tracker

This project is a Django-based web application designed for tracking attendance and managing leave requests. It's structured to provide a user-friendly interface for both employees and managers to handle various aspects of attendance and leave management.

## Features

- **User Authentication**: Custom user authentication system, allowing login with either username or email. These can be dummy emails for the sake of testing the application, however using a real email address will allow the user to use the "forgot password" feature which sends an email for password reset.
- **Attendance Tracking**: Employees can record their attendance, specifying the type of attendance (e.g., Working From Home, In Office, Annual Leave).
- **Leave Management**: Employees can submit leave requests, which managers can approve or deny.
- **Manager Dashboard**: Specialized dashboard for managers to view and manage leave requests.
- **Session Timeout Warning**: Custom middleware for handling session timeouts and inactivity.

## Live Application

The application is hosted and can be accessed at:

- **Main Application**: [https://dynamitekitty16.pythonanywhere.com/](https://dynamitekitty16.pythonanywhere.com/)
- **Admin Dashboard**: [https://dynamitekitty16.pythonanywhere.com/admin/logout/](https://dynamitekitty16.pythonanywhere.com/admin/logout/)

### Admin Access

To access the admin dashboard:

- **Username**: admin
- **Password**: @Pa$$w0rd!

Please note: The admin account should be used responsibly to set user roles and manage the application. Mainly, you need this information so that you can set a user to "is_manager" = true so that they will be able to access manager view, and be available for the drop down manager list under "UserProfiles".

## Installation and Local Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/DynamiteKitty16/L5-SEAA.git
