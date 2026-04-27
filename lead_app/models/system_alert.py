from datetime import datetime, timezone
from extensions import db


class SystemAlert(db.Model):
    __tablename__ = 'system_alerts'
    id = db.Column(db.Integer, primary_key=True)
    alert_type = db.Column(db.String(80), nullable=False, index=True)
    severity = db.Column(db.String(20), nullable=False, default='error')
    message = db.Column(db.Text, nullable=False)
    related_gmail_message_id = db.Column(db.String(255), nullable=True)
    related_label = db.Column(db.String(255), nullable=True)
    related_lead_id = db.Column(db.Integer, db.ForeignKey('leads.id'), nullable=True)
    is_resolved = db.Column(db.Boolean, nullable=False, default=False, index=True)
    resolved_by_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    resolved_at = db.Column(db.DateTime(timezone=True), nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)
    related_lead = db.relationship('Lead', foreign_keys=[related_lead_id])
    resolved_by = db.relationship('User', foreign_keys=[resolved_by_user_id])

    GMAIL_POLL_FAILURE = 'gmail_poll_failure'
    GMAIL_AUTH_FAILURE = 'gmail_auth_failure'
    EMAIL_PARSE_FAILURE = 'email_parse_failure'
    NO_ELIGIBLE_AGENT = 'no_eligible_agent'
    LEAD_ASSIGNMENT_FAILURE = 'lead_assignment_failure'
    TRUNCATION_FAILURE = 'truncation_failure'
    DB_WRITE_FAILURE = 'db_write_failure'
