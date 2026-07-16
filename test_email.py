import django, os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django.setup()
from django.core.mail import send_mail
from django.conf import settings

print("EMAIL_HOST_USER:", settings.EMAIL_HOST_USER)
print("PASSWORD length:", len(settings.EMAIL_HOST_PASSWORD))
print("Sending test email...")

try:
    result = send_mail(
        subject="ARYA AI — OTP Test",
        message="Your test OTP is: 585539\n\nThis is a test email from ARYA AI backend.",
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[settings.EMAIL_HOST_USER],
        fail_silently=False,
    )
    print("SUCCESS — emails sent:", result)
except Exception as e:
    print("ERROR:", type(e).__name__)
    print("Detail:", str(e))
