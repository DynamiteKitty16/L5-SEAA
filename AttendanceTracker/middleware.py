from django.contrib.auth import logout
from django.utils import timezone
from django.conf import settings

class InactivityTimeoutMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):

        # Define current time outside of the branch to avoid UnboundLocalErrror
        # # added in a UNIX conversion due to JSON string issue    
        current_time = timezone.now().timestamp()

        # Check if the user is authenticated
        if request.user.is_authenticated:
            # Get the last activity time from the session
            last_activity = request.session.get('last_activity')
            
            # If last_activity is not set, or the user has been inactive for SESSION_COOKIE_AGE seconds
            if not last_activity or (current_time - last_activity) > settings.SESSION_COOKIE_AGE:
                logout(request)  # Log out the user

        # Check if the request is AJAX
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

        # Update last activity time in the session only for non-AJAX requests and exclude
        # the session timeout warning URL
        if not is_ajax and request.path != '/session_timeout_warning/':
            request.session['last_activity'] = current_time

        response = self.get_response(request)
        return response
