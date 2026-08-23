# ============================================================
# SafeTrack Notifications Module
# ------------------------------------------------------------
# Sends email notifications via SendGrid when:
#   1. A new emergency alert is created  -> notify admins
#   2. An alert's status changes         -> notify the student
#
# Design notes:
# - Fails "soft": if SendGrid isn't configured or the API call
#   errors, we log it and move on. A notification failure should
#   NEVER block or fail the underlying alert create/update flow —
#   the alert itself is the safety-critical part.
# - Kept as its own module so server.py stays focused on routing.
# ============================================================

import os
import logging
from typing import Optional
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

logger = logging.getLogger(__name__)

SENDGRID_API_KEY = os.environ.get("SENDGRID_API_KEY")
FROM_EMAIL = os.environ.get("NOTIFY_FROM_EMAIL", "alerts@safetrack.app")
ADMIN_NOTIFY_EMAILS = [
    e.strip() for e in os.environ.get("ADMIN_NOTIFY_EMAILS", "").split(",") if e.strip()
]

NOTIFICATIONS_ENABLED = bool(SENDGRID_API_KEY)

if not NOTIFICATIONS_ENABLED:
    logger.warning(
        "SENDGRID_API_KEY not set — email notifications are disabled. "
        "Alerts will still be created/updated normally."
    )


def _send_email(to_email: str, subject: str, content: str) -> bool:
    """Low-level send helper. Returns True on success, False on any failure."""
    if not NOTIFICATIONS_ENABLED:
        logger.info(f"[notifications disabled] Would have sent to {to_email}: {subject}")
        return False

    if not to_email:
        logger.warning("Skipped email send: no recipient address provided")
        return False

    try:
        message = Mail(
            from_email=FROM_EMAIL,
            to_emails=to_email,
            subject=subject,
            plain_text_content=content,
        )
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        response = sg.send(message)
        logger.info(f"Notification email sent to {to_email} (status {response.status_code})")
        return True
    except Exception as e:
        # Notifications must never take down the alert flow.
        logger.error(f"Failed to send notification email to {to_email}: {e}")
        return False


async def notify_new_alert(
    student_name: str,
    student_id: str,
    location: Optional[str],
    message: Optional[str],
    alert_id: str,
    lang: str = "en",
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
) -> None:
    """Notify all configured admin addresses that a new emergency alert was created."""
    if not ADMIN_NOTIFY_EMAILS:
        logger.warning("No ADMIN_NOTIFY_EMAILS configured — skipping new-alert notification")
        return

    subject = f"🆘 New SafeTrack Alert — {student_name} ({student_id})"
    body_lines = [
        f"A new emergency alert has been created.",
        f"",
        f"Student: {student_name} ({student_id})",
        f"Location: {location or 'Not provided'}",
        f"Message: {message or 'No additional message'}",
        f"Alert ID: {alert_id}",
    ]
    if latitude is not None and longitude is not None:
        body_lines.append(
            f"GPS: https://www.google.com/maps?q={latitude},{longitude}"
        )
    body_lines += [
        f"",
        f"Log in to the SafeTrack admin dashboard to respond.",
    ]
    body = "\n".join(body_lines)

    for admin_email in ADMIN_NOTIFY_EMAILS:
        _send_email(admin_email, subject, body)


async def notify_alert_status_change(
    student_email: str,
    student_name: str,
    new_status: str,
    alert_id: str,
    lang: str = "en",
) -> None:
    """Notify the reporting student that their alert's status has changed."""
    status_text = {
        "en": {"resolved": "resolved", "active": "marked active"},
        "bn": {"resolved": "সমাধান হয়েছে", "active": "সক্রিয় চিহ্নিত"},
    }.get(lang, {}).get(new_status, new_status)

    subject = f"SafeTrack Alert Update — {status_text}"
    body = (
        f"Hi {student_name},\n\n"
        f"Your emergency alert (ID: {alert_id}) has been {status_text}.\n\n"
        f"If this is incorrect or you need further help, please contact your "
        f"campus safety office directly.\n\n"
        f"— SafeTrack"
    )
    _send_email(student_email, subject, body)
