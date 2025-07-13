from rest_framework import viewsets
from .models import Listing, Booking
from .serializers import ListingSerializer, BookingSerializer
import requests
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
from .tasks import send_booking_confirmation_email
from .models import Payment
import uuid


class BookingViewSet(viewsets.ModelViewSet):
    queryset = Booking.objects.all()
    serializer_class = BookingSerializer

    def perform_create(self, serializer):
        booking = serializer.save()
        send_booking_confirmation_email.delay(booking.user.email, booking.reference)

class InitiatePaymentView(APIView):
    def post(self, request):
        amount = request.data.get('amount')
        booking_reference = request.data.get('booking_reference')
        email = request.data.get('email')

        tx_ref = str(uuid.uuid4())

        data = {
            "amount": amount,
            "currency": "ETB",
            "email": email,
            "tx_ref": tx_ref,
            "callback_url": "http://yourdomain.com/verify-payment/",
            "return_url": "http://yourdomain.com/payment-success/",
            "customization": {
                "title": "Travel Booking",
                "description": "Payment for booking reference " + booking_reference
            }
        }

        headers = {
            "Authorization": f"Bearer {settings.CHAPA_SECRET_KEY}"
        }

        response = requests.post("https://api.chapa.co/v1/transaction/initialize", json=data, headers=headers)

        if response.status_code == 200:
            res_data = response.json()
            Payment.objects.create(
                booking_reference=booking_reference,
                amount=amount,
                chapa_tx_ref=tx_ref,
                status="Pending"
            )
            return Response({"checkout_url": res_data['data']['checkout_url']})
        else:
            return Response({"error": "Failed to initiate payment"}, status=status.HTTP_400_BAD_REQUEST)

class VerifyPaymentView(APIView):
    def get(self, request, tx_ref):
        headers = {
            "Authorization": f"Bearer {settings.CHAPA_SECRET_KEY}"
        }

        url = f"https://api.chapa.co/v1/transaction/verify/{tx_ref}"
        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            res_data = response.json()
            status_str = res_data['data']['status']
            payment = Payment.objects.get(chapa_tx_ref=tx_ref)
            
            if status_str == "success":
                payment.status = "Completed"
                payment.save()
                # optionally trigger celery task for confirmation email
            else:
                payment.status = "Failed"
                payment.save()

            return Response({"status": payment.status})
        else:
            return Response({"error": "Verification failed"}, status=status.HTTP_400_BAD_REQUEST)

class ListingViewSet(viewsets.ModelViewSet):
    queryset = Listing.objects.all()
    serializer_class = ListingSerializer

class BookingViewSet(viewsets.ModelViewSet):
    queryset = Booking.objects.all()
    serializer_class = BookingSerializer
