from datetime import datetime, timezone
from extensions import db


class Lead(db.Model):
    __tablename__ = 'leads'
    id = db.Column(db.Integer, primary_key=True)
    gmail_message_id = db.Column(db.String(255), nullable=True, index=True)
    gmail_thread_id = db.Column(db.String(255), nullable=True)
    monitored_gmail_label_id = db.Column(db.Integer, db.ForeignKey('monitored_gmail_labels.id'), nullable=True)
    provider_display_name = db.Column(db.String(120), nullable=False)
    sender_email = db.Column(db.String(255), nullable=False)
    sender_display_name = db.Column(db.String(255), nullable=True)
    email_subject = db.Column(db.String(500), nullable=True)
    email_body_text = db.Column(db.Text, nullable=True)
    email_received_at = db.Column(db.DateTime(timezone=True), nullable=True)
    processed_at = db.Column(db.DateTime(timezone=True), nullable=True)
    assigned_agent_profile_id = db.Column(db.Integer, db.ForeignKey('agent_profiles.id'), nullable=True)
    assigned_agent_name_snapshot = db.Column(db.String(120), nullable=True)
    assigned_at = db.Column(db.DateTime(timezone=True), nullable=True)
    outcome_option_id = db.Column(db.Integer, db.ForeignKey('outcome_options.id'), nullable=True)
    outcome_text_snapshot = db.Column(db.String(120), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    is_active = db.Column(db.Boolean, nullable=False, default=True, index=True)
    is_complete = db.Column(db.Boolean, nullable=False, default=False)
    is_incomplete = db.Column(db.Boolean, nullable=False, default=False)
    truncation_datetime = db.Column(db.DateTime(timezone=True), nullable=True)
    truncation_batch_id = db.Column(db.Integer, db.ForeignKey('truncation_batches.id'), nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc))
    monitored_label = db.relationship('MonitoredGmailLabel', back_populates='leads')
    assigned_agent = db.relationship('AgentProfile', back_populates='leads',
                                     foreign_keys=[assigned_agent_profile_id])
    outcome_option = db.relationship('OutcomeOption', back_populates='leads')
    truncation_batch = db.relationship('TruncationBatch', back_populates='leads')

    @property
    def has_outcome(self):
        return self.outcome_option_id is not None

    @property
    def display_outcome(self):
        if self.outcome_option and self.outcome_option.is_active:
            return self.outcome_option.name
        return self.outcome_text_snapshot or '—'
