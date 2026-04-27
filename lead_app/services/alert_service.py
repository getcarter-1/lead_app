import logging
from extensions import db
from models.system_alert import SystemAlert

logger = logging.getLogger(__name__)


def create_alert(alert_type, message, severity='error',
                 related_gmail_message_id=None, related_label=None, related_lead_id=None):
    try:
        alert = SystemAlert(alert_type=alert_type, severity=severity, message=message,
                            related_gmail_message_id=related_gmail_message_id,
                            related_label=related_label, related_lead_id=related_lead_id)
        db.session.add(alert)
        db.session.commit()
        logger.warning(f'ALERT [{alert_type}] [{severity}]: {message}')
    except Exception as e:
        logger.error(f'Failed to write alert: {e} | Original: [{alert_type}]: {message}')
