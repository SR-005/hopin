import requests
from django.conf import settings


def sendemail(subject, message, recipient_email):
    api_key=settings.BREVO_API_KEY

    response=requests.post(
        settings.BREVO_API_URL,
        headers={
            "accept": "application/json",
            "api-key": api_key,
            "content-type": "application/json",
        },
        json={
            "sender": {
                "name":settings.DEFAULT_FROM_NAME,
                "email":settings.DEFAULT_FROM_EMAIL,
            },
            "to": [{"email":recipient_email}],
            "subject":subject,
            "textContent":message,
        },
        timeout=settings.BREVO_API_TIMEOUT,
    )
    if not response.ok:
        raise ValueError(
            f"Brevo API error {response.status_code}: {response.text}"
        )

