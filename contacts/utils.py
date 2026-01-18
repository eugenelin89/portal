from django.conf import settings
from django.core.mail import send_mail
from django.urls import reverse


def send_contact_request_email(request, contact_request):
    if request is None:
        return
    player_email = getattr(contact_request.player, "email", "")
    if not player_email:
        return

    requests_url = request.build_absolute_uri(reverse("player_requests"))
    send_mail(
        "New contact request",
        (
            "You have a new contact request on the BC Baseball Transfer Portal.\n\n"
            "Please log in to review and respond:\n"
            f"{requests_url}\n"
        ),
        settings.DEFAULT_FROM_EMAIL,
        [player_email],
    )
