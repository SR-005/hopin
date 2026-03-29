"""
Push notification utilities for Hopin app using django-webpush
"""
import json
import logging

from webpush.models import PushInformation
from webpush.utils import send_to_subscription

logger = logging.getLogger(__name__)


def _build_payload(head, body, url="/rider/"):
    return {
        "head": head,
        "body": body,
        "icon": "/static/hopin_app/images/logo.png",
        "url": url,
    }


def _send_notification(user, payload):
    payload_json = json.dumps(payload)
    seen_endpoints = set()
    push_infos = (
        PushInformation.objects.filter(user=user)
        .select_related("subscription")
        .order_by("-id")
    )

    for push_info in push_infos:
        subscription = push_info.subscription
        endpoint = getattr(subscription, "endpoint", "")

        if not endpoint or endpoint in seen_endpoints:
            continue

        seen_endpoints.add(endpoint)

        try:
            send_to_subscription(subscription, payload_json, ttl=1000)
        except Exception:
            logger.exception(
                "Error sending notification to user %s for subscription %s",
                user.id,
                getattr(subscription, "id", "unknown"),
            )


def _send_notification_to_users(users, payload):
    for user in users:
        _send_notification(user, payload)


def send_request_accepted_notification(rider):
    """
    Send push notification to rider when their ride request is accepted
    """
    payload = _build_payload(
        head="Request Accepted!",
        body="Your ride request has been accepted by the driver.",
    )
    _send_notification(rider, payload)


def send_request_rejected_notification(rider):
    """
    Send push notification to rider when their ride request is rejected
    """
    payload = _build_payload(
        head="Request Rejected",
        body="Unfortunately, your ride request has been rejected.",
    )
    _send_notification(rider, payload)


def send_trip_deleted_notification(riders_list):
    """
    Send push notification to all riders when a trip they requested is deleted
    
    Args:
        riders_list: QuerySet or list of User objects
    """
    payload = _build_payload(
        head="Trip Cancelled",
        body="The ride you requested has been cancelled by the driver.",
    )
    _send_notification_to_users(riders_list, payload)


def send_generic_notification(user, title, body):
    """
    Send a generic push notification to a user
    
    Args:
        user: User object
        title: Notification title
        body: Notification body
    """
    payload = _build_payload(head=title, body=body)
    _send_notification(user, payload)


def send_new_ride_request_notification(driver, rider):
    payload = _build_payload(
        head="New Ride Request",
        body=f"{rider.first_name or rider.email} requested a seat on your ride.",
        url="/driver/",
    )
    _send_notification(driver, payload)


def send_request_cancelled_notification(driver, rider):
    payload = _build_payload(
        head="Request Cancelled",
        body=f"{rider.first_name or rider.email} cancelled their ride request.",
        url="/driver/",
    )
    _send_notification(driver, payload)


def send_ride_started_notification(riders_list):
    payload = _build_payload(
        head="Ride Started",
        body="Your driver has started the ride. Open tracking to follow the trip live.",
    )
    _send_notification_to_users(riders_list, payload)


def send_pickup_confirmed_notification(rider):
    payload = _build_payload(
        head="Pickup Confirmed",
        body="The driver marked you as picked up.",
    )
    _send_notification(rider, payload)


def send_dropoff_notification(rider):
    payload = _build_payload(
        head="Drop-off Confirmed",
        body="Your ride has been marked as completed for your seat.",
    )
    _send_notification(rider, payload)


def send_payment_due_notification(rider, payment_id=None):
    payload = _build_payload(
        head="Payment Pending",
        body="Your ride is complete. Payment is now ready.",
        url=f"/profile/" if payment_id else "/rider/",
    )
    _send_notification(rider, payload)


def send_ride_completed_notification(driver):
    payload = _build_payload(
        head="Ride Completed",
        body="Your trip has been marked as completed.",
        url="/driver/",
    )
    _send_notification(driver, payload)


def send_payment_success_notification(rider, amount):
    payload = _build_payload(
        head="Payment Successful",
        body=f"Your payment of Rs. {amount:.2f} was successful.",
    )
    _send_notification(rider, payload)


def send_payment_received_notification(driver, rider, amount):
    payload = _build_payload(
        head="Payment Received",
        body=f"{rider.first_name or rider.email} paid Rs. {amount:.2f} for the ride.",
        url="/driver/",
    )
    _send_notification(driver, payload)
