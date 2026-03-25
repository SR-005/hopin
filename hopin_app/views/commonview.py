from datetime import datetime
from ..models import trip

from django.utils import timezone
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.shortcuts import render
import json
from webpush.models import PushInformation


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


# Register Web Push subscription for notifications
@login_required
@require_http_methods(["POST"])
def register_webpush_subscription(request):
    """
    Endpoint to register Web Push subscription for authenticated user
    Expects POST request with subscription object in body
    """
    try:
        data = json.loads(request.body)
        subscription = data.get('subscription')
        
        if not subscription:
            return JsonResponse({
                'status': 'error',
                'message': 'No subscription provided'
            }, status=400)
        
        # The webpush library handles subscription storage internally
        # Just acknowledge the registration
        return JsonResponse({
            'status': 'success',
            'message': 'Subscription registered successfully'
        })
    except json.JSONDecodeError:
        return JsonResponse({
            'status': 'error',
            'message': 'Invalid JSON'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)


@login_required
def push_debug_page(request):
    return render(request, "push_debug.html")


@login_required
def push_debug_status(request):
    push_infos = PushInformation.objects.filter(user=request.user).select_related("subscription")
    data = []
    for item in push_infos[:5]:
        data.append({
            "id": item.id,
            "endpoint": item.subscription.endpoint[:120],
            "browser": item.subscription.browser,
        })

    return JsonResponse({
        "count": push_infos.count(),
        "items": data,
        "save_information_url": "/save_information",
        "service_worker_url": "/service-worker.js",
    })
