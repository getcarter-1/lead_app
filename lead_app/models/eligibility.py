from datetime import datetime, timezone
from extensions import db


class AgentProviderEligibility(db.Model):
    __tablename__ = 'agent_provider_eligibilities'
    id = db.Column(db.Integer, primary_key=True)
    agent_profile_id = db.Column(db.Integer, db.ForeignKey('agent_profiles.id'), nullable=False)
    monitored_gmail_label_id = db.Column(db.Integer, db.ForeignKey('monitored_gmail_labels.id'), nullable=False)
    is_eligible = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc))
    __table_args__ = (db.UniqueConstraint('agent_profile_id', 'monitored_gmail_label_id', name='uq_agent_label'),)
    agent_profile = db.relationship('AgentProfile', back_populates='eligibilities')
    monitored_label = db.relationship('MonitoredGmailLabel', back_populates='eligibilities')
