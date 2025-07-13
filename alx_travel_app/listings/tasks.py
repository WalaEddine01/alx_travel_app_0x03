from celery import shared_task
from django.core.mail import send_mail

@shared_task
def send_booking_confirmation_email(user_email, booking_reference):
    subject = "Booking Confirmation"
    message = f"Your booking with reference {booking_reference} has been confirmed."
    from_email = None  # uses DEFAULT_FROM_EMAIL
    recipient_list = [user_email]

    send_mail(subject, message, from_email, recipient_list)
    return "Email sent"
