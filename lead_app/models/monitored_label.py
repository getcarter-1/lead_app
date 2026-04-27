from datetime import datetime, timezone
from extensions import db


class MonitoredGmailLabel(db.Model):
    __tablename__ = 'monitored_gmail_labels'
    id = db.Column(db.Integer, primary_key=True)
    gmail_label_id = db.Column(db.String(255), nullable=False)
    gmail_label_path = db.Column(db.String(255), nullable=False)
    provider_display_name = db.Column(db.String(120), nullable=False)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc))
    eligibilities = db.relationship('AgentProviderEligibility', back_populates='monitored_label',
                                    cascade='all, delete-orphan')
    leads = db.relationship('Lead', back_populates='monitored_label', lazy='dynamic')

    def __repr__(self):
        return f'<MonitoredGmailLabel {self.gmail_label_path}>'
