from datetime import date, time

from django.contrib.auth import get_user_model
from django.test import TestCase

from hopin_app.ml.routeopt import riderdropped
from hopin_app.models import payment, riderequest, trip
from hopin_app.views.locationview import rideend


User=get_user_model()


class RideTrackingFlowTests(TestCase):
    college_latitude=10.050272
    college_longitude=76.329273

    def setUp(self):
        self.driver=User.objects.create_user(
            email="driver@student.aisat.ac.in",
            password="password123"
        )
        self.rider=User.objects.create_user(
            email="rider@student.aisat.ac.in",
            password="password123"
        )

    def create_trip(self, currentlatitude, currentlongitude, has_boarded=True, prefereddirection="to"):
        return trip.objects.create(
            usercredentials=self.driver,
            preferedlocation="Town",
            latitude=10.0010,
            longitude=76.3010,
            distance=8.0,
            routegeometry={
                "type": "LineString",
                "coordinates": [
                    [76.3010, 10.0010],
                    [76.3200, 10.0200],
                    [self.college_longitude, self.college_latitude],
                ],
            },
            prefereddirection=prefereddirection,
            ridedate=date.today(),
            ridetime=time(7, 45),
            currentlatitude=currentlatitude,
            currentlongitude=currentlongitude,
            vehicletype="Bike",
            helmet="yes",
            availableseats=1,
            vehiclenumber="KL01AB1234",
            vehiclemodel="Test Bike",
            price=25.0,
            status="ONGOING",
            has_boarded=has_boarded,
        )

    def test_fullconfirm_rider_is_not_dropped_before_reaching_college(self):
        current_trip=self.create_trip(currentlatitude=10.0012, currentlongitude=76.3012)
        request_record=riderequest.objects.create(
            trip=current_trip,
            rider=self.rider,
            pickuplocation="Town Stop",
            pickuplatitude=10.0012,
            pickuplongitude=76.3012,
            price=25.0,
            status="FULLCONFIRM",
        )

        riderdropped(
            current_trip.currentlatitude,
            current_trip.currentlongitude,
            riderequest.objects.filter(id=request_record.id),
        )

        request_record.refresh_from_db()
        self.assertEqual(request_record.status, "FULLCONFIRM")

    def test_halfconfirm_rider_does_not_complete_trip_before_destination(self):
        current_trip=self.create_trip(currentlatitude=10.0012, currentlongitude=76.3012)
        request_record=riderequest.objects.create(
            trip=current_trip,
            rider=self.rider,
            pickuplocation="Town Stop",
            pickuplatitude=10.0012,
            pickuplongitude=76.3012,
            price=25.0,
            status="HALFCONFIRM",
        )

        rideend(current_trip)

        current_trip.refresh_from_db()
        request_record.refresh_from_db()
        self.assertEqual(current_trip.status, "ONGOING")
        self.assertEqual(request_record.status, "HALFCONFIRM")
        self.assertFalse(payment.objects.filter(requestdetails=request_record).exists())

    def test_ride_does_not_complete_before_boarding(self):
        current_trip=self.create_trip(currentlatitude=10.0012, currentlongitude=76.3012, has_boarded=False)
        request_record=riderequest.objects.create(
            trip=current_trip,
            rider=self.rider,
            pickuplocation="Town Stop",
            pickuplatitude=10.0012,
            pickuplongitude=76.3012,
            price=25.0,
            status="ACCEPTED",
        )

        # Simulate reaching destination without boarding
        current_trip.currentlatitude=self.college_latitude
        current_trip.currentlongitude=self.college_longitude
        current_trip.save()

        rideend(current_trip)

        current_trip.refresh_from_db()
        request_record.refresh_from_db()
        self.assertEqual(current_trip.status, "ONGOING")
        self.assertEqual(request_record.status, "ACCEPTED")
        self.assertFalse(payment.objects.filter(requestdetails=request_record).exists())

    def test_halfconfirm_rider_becomes_dropped_not_confirmed_at_destination(self):
        current_trip=self.create_trip(
            currentlatitude=self.college_latitude,
            currentlongitude=self.college_longitude,
        )
        request_record=riderequest.objects.create(
            trip=current_trip,
            rider=self.rider,
            pickuplocation="Town Stop",
            pickuplatitude=10.0012,
            pickuplongitude=76.3012,
            price=25.0,
            status="HALFCONFIRM",
        )

        rideend(current_trip)

        current_trip.refresh_from_db()
        request_record.refresh_from_db()
        created_payment=payment.objects.filter(requestdetails=request_record).first()

        self.assertEqual(current_trip.status, "COMPLETED")
        self.assertEqual(request_record.status, "DROPPEDNOTCONFIRMED")
        self.assertIsNotNone(created_payment)
        self.assertEqual(created_payment.amount, request_record.price)

    def test_from_ride_completes_after_last_fullconfirm_rider_is_dropped(self):
        current_trip=self.create_trip(
            currentlatitude=10.0300,
            currentlongitude=76.3200,
            prefereddirection="from",
        )
        request_record=riderequest.objects.create(
            trip=current_trip,
            rider=self.rider,
            pickuplocation="Town Stop",
            pickuplatitude=10.0497725,
            pickuplongitude=76.3297076,
            price=25.0,
            status="FULLCONFIRM",
        )

        current_trip.currentlatitude=request_record.pickuplatitude
        current_trip.currentlongitude=request_record.pickuplongitude
        current_trip.save()

        riderdropped(
            current_trip.currentlatitude,
            current_trip.currentlongitude,
            riderequest.objects.filter(id=request_record.id),
        )
        rideend(current_trip)

        current_trip.refresh_from_db()
        request_record.refresh_from_db()
        created_payment=payment.objects.filter(requestdetails=request_record).first()

        self.assertEqual(request_record.status, "DROPPED")
        self.assertEqual(current_trip.status, "COMPLETED")
        self.assertIsNotNone(created_payment)
        self.assertEqual(created_payment.amount, request_record.price)
