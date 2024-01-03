from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _

# Added custom validators due to workplace having strict password validation needs, trying to replicate as close to business 

class UppercaseValidator:
    def validate(self, password, user=None):
        if not any(char.isupper() for char in password):
            raise ValidationError(
                _("This password must contain at least one uppercase letter."),
                code='password_no_upper',
            )

    def get_help_text(self):
        return _(
            "Your password must contain at least one uppercase letter."
        )

class SpecialCharacterValidator:
    def validate(self, password, user=None):
        if not any(char in "!@#$%^&*()-_=+[]{};:'\",<.>/?\\|`~" for char in password):
            raise ValidationError(
                _("This password must contain at least one special character."),
                code='password_no_special',
            )

    def get_help_text(self):
        return _(
            "Your password must contain at least one special character."
        )

class NumberValidator:
    def validate(self, password, user=None):
        if not any(char.isdigit() for char in password):
            raise ValidationError(
                _("This password must contain at least one number."),
                code='password_no_number',
            )

    def get_help_text(self):
        return _(
            "Your password must contain at least one number."
        )
    
class NoReusePasswordValidator:
    def validate(self, password, user=None):
        if user.check_password(password):
            raise ValidationError(
                _("Your new password cannot be the same as your old password."),
                code='password_no_reuse',
            )

    def get_help_text(self):
        return _("Your new password cannot be the same as your old password.")