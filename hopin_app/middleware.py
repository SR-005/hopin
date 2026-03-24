from django.http import HttpResponse
from django.urls import reverse
from .models import payment

class PendingPaymentMiddleware:
    def __init__(self, get_response):
        self.get_response=get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            if payment.objects.filter(requestdetails__rider=request.user,status="PENDING").exists():

                if request.path == "/":
                    return self.get_response(request)
                
                allowed_paths=["/login/","/signup/","/logout/","/verifypayment/","/testpay/","/fetchtracking/","/fetchstatus/"
                               ,"/testlocation/","/testtracking/","/updatelocation/"]

                if not any(request.path.startswith(p) for p in allowed_paths):
                    return HttpResponse("Complete pending payment first", status=403)

        return self.get_response(request)