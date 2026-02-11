from allauth.account.adapter import DefaultAccountAdapter
from django.core.exceptions import ValidationError

class RestrictEmailAdapter(DefaultAccountAdapter):
    def clean_email(self, email):
        if not email.endswith("@student.aisat.ac.in"):
            raise ValidationError(
                "Only @student.aisat.ac.in accounts allowed."
            )
        return email
