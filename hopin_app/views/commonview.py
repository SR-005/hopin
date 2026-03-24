from datetime import datetime
from ..models import trip

from django.utils import timezone


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