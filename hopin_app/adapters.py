# hopin_app/adapters.py

from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.exceptions import ImmediateHttpResponse
from django.http import HttpResponseRedirect
from django.contrib import messages


# Helper class to interrupt allauth flow cleanly
class ImmediateRedirect(ImmediateHttpResponse):
    def __init__(self, redirect_to):
        super().__init__(HttpResponseRedirect(redirect_to))


class RestrictDomainSocialAdapter(DefaultSocialAccountAdapter):

    def pre_social_login(self, request, sociallogin):
        email = sociallogin.account.extra_data.get("email")

        # Only block new signups
        if not sociallogin.is_existing:

            if not email.endswith("@student.aisat.ac.in"):
                messages.error(
                    request,
                    "Only @student.aisat.ac.in accounts are allowed."
                )
                raise ImmediateRedirect("/")
