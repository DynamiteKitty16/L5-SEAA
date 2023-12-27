"""
URL configuration for AttendanceTracker project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib.auth import views as auth_views
from django.contrib.auth.views import LogoutView
from tracker.views import cancel_leave_request
from tracker.views import requests_view
from django.contrib import admin
from django.urls import path
from tracker import views


urlpatterns = [
    path('admin/', admin.site.urls),
    path('session_timeout_warning/', views.session_timeout_warning, name='session_timeout_warning'),
    path('extend_session/', views.extend_session, name='extend_session'),
    path('password_reset/', auth_views.PasswordResetView.as_view(), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),
    path('', views.login_view, name='login'), # Set up as the first page
    path('home/', views.home_view, name='home'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('register/', views.register, name='register'),
    path('registration_success/', views.registration_success, name='registration_success'),
    path('calendar/', views.calendar, name='calendar'),
    path('handle-attendance/', views.handle_attendance, name='handle_attendance'),
    path('requests/', requests_view, name='requests'),
    path('cancel-request/', cancel_leave_request, name='cancel_leave_request'),
]
