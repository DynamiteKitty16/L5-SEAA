from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.models import User

# Created custom authentication file so that the user can login with username or email address

class EmailOrUsernameModelBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        user = None
        if '@' in username:
            kwargs = {'email': username}
        else:
            kwargs = {'username': username}
        try:
            user = User.objects.get(**kwargs)
        except User.DoesNotExist:
            pass  # User not found, will be handled in the view

        if user and user.check_password(password):
            return user
        return None  # Either user not found or password incorrect
