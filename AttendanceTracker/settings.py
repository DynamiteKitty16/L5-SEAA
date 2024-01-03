"""
Django settings for AttendanceTracker project.

Generated by 'django-admin startproject' using Django 4.2.7.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.2/ref/settings/
"""

from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-spu%*zlm$y3y69vv*xd2$mxl-a_i%xvdp!g=#($0m4%og0*_^m'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['dynamitekitty16.pythonanywhere.com']


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Bootstrap apps below
    'widget_tweaks',
    # Adding created apps below
    'tracker',
    # App for lockout out of the box
    'axes',
]

# Crispy Forms Settings
CRISPY_TEMPLATE_PACK = 'bootstrap4'

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    # Custom middleware below
    'AttendanceTracker.middleware.InactivityTimeoutMiddleware',
    # Adding Axes to middleware
    'axes.middleware.AxesMiddleware',
]

# Adding in session to handle timeout and sign in

# Set time out to 30 mins
SESSION_COOKIE_AGE = 1800

# TESTING - set time out to 2 mins
# SESSION_COOKIE_AGE = 120

# Update session expiration with every request
SESSION_SAVE_EVERY_REQUEST = True

LOGIN_URL = 'login'

# This is to point at my custom authentication

AUTHENTICATION_BACKENDS = [
    'AttendanceTracker.authentication.EmailOrUsernameModelBackend',
    'django.contrib.auth.backends.ModelBackend',
    'axes.backends.AxesBackend',
]

# django-axes configurations
AXES_FAILURE_LIMIT = 3
AXES_LOCK_OUT_AT_FAILURE = True
AXES_COOLOFF_TIME = 1  # time in hours


ROOT_URLCONF = 'AttendanceTracker.urls'

# Corrected templates pointing as base is not working

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'AttendanceTracker.wsgi.application'


# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases


import os

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'DynamiteKitty16$default',  # PythonAnywhere database name
        'USER': 'DynamiteKitty16',  # PythonAnywhere username
        'PASSWORD': 'Allmight2112!',  # The password set for MySQL on PythonAnywhere
        'HOST': 'DynamiteKitty16.mysql.pythonanywhere-services.com',  # Database host address
        'PORT': '3306',  # Default MySQL port
    }
}

# Email configuration for development - will change in hosting move
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_HOST_USER = 'AvailabilityTrackerProject@gmail.com'
EMAIL_HOST_PASSWORD = 'wddr msst hsyr akvx'
EMAIL_USE_TLS = True


# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 8,
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
    # From below adding custom validators that are in the tracker app folder
    {
        'NAME': 'tracker.custom_validators.UppercaseValidator',
    },
      {
        'NAME': 'tracker.custom_validators.SpecialCharacterValidator',
    },
    {
        'NAME': 'tracker.custom_validators.NumberValidator',
    },
    {
        'NAME': 'tracker.custom_validators.NoReusePasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/4.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/

STATIC_URL = '/static/'
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')


# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
