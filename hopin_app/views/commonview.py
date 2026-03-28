from datetime import datetime
from ..models import trip, riderequest

from django.utils import timezone
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required

ACTIVE_DRIVER_TRIP_STATUSES = ["EMPTY", "ACTIVE", "ONGOING"]
ACTIVE_RIDER_REQUEST_STATUSES = ["PENDING", "ACCEPTED", "HALFCONFIRM", "FULLCONFIRM"]


def get_active_driver_trip(user):
    return trip.objects.filter(
        usercredentials=user,
        status__in=ACTIVE_DRIVER_TRIP_STATUSES
    ).order_by("-id").first()


def get_active_rider_request(user):
    return riderequest.objects.filter(
        rider=user,
        status__in=ACTIVE_RIDER_REQUEST_STATUSES
    ).select_related("trip", "trip__usercredentials").order_by("-id").first()


#clean up expired rides
def cleanup(request):
    unengagedtrips=trip.objects.filter(status="EMPTY")
    now=timezone.localtime()

    for trips in unengagedtrips:
        ridedatetime=datetime.combine(trips.ridedate, trips.ridetime)
        ridedatetime=timezone.make_aware(ridedatetime)

        if ridedatetime < now:
            trips.delete()

    return 0
