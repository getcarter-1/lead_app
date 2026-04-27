from datetime import datetime, timezone
from extensions import db


class AgentProfile(db.Model):
    __tablename__ = 'agent_profiles'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    display_name = db.Column(db.String(120), nullable=False)
    balance_integer = db.Column(db.Integer, nullable=False, default=0)
    is_active_for_distribution = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc))
    user = db.relationship('User', back_populates='agent_profile')
    eligibilities = db.relationship('AgentProviderEligibility', back_populates='agent_profile',
                                    cascade='all, delete-orphan')
    leads = db.relationship('Lead', back_populates='assigned_agent',
                            foreign_keys='Lead.assigned_agent_profile_id', lazy='dynamic')

    @property
    def active_lead_count(self):
        from models.lead import Lead
        return Lead.query.filter_by(assigned_agent_profile_id=self.id, is_active=True).count()

    @property
    def distribution_score(self):
        return self.active_lead_count + self.balance_integer

    def is_eligible_for_label(self, monitored_label_id):
        from models.eligibility import AgentProviderEligibility
        elig = AgentProviderEligibility.query.filter_by(
            agent_profile_id=self.id, monitored_gmail_label_id=monitored_label_id, is_eligible=True).first()
        return elig is not None

    def __repr__(self):
        return f'<AgentProfile {self.display_name}>'
