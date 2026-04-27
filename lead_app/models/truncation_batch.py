from datetime import datetime, timezone
from extensions import db


class TruncationBatch(db.Model):
    __tablename__ = 'truncation_batches'
    id = db.Column(db.Integer, primary_key=True)
    batch_id = db.Column(db.String(50), unique=True, nullable=False)
    batch_month = db.Column(db.Date, nullable=False, index=True)
    started_at = db.Column(db.DateTime(timezone=True), nullable=True)
    completed_at = db.Column(db.DateTime(timezone=True), nullable=True)
    status = db.Column(db.String(20), nullable=False, default='pending')
    leads_truncated_count = db.Column(db.Integer, nullable=False, default=0)
    incomplete_leads_count = db.Column(db.Integer, nullable=False, default=0)
    error_message = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    leads = db.relationship('Lead', back_populates='truncation_batch', lazy='dynamic')
