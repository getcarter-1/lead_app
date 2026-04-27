import logging
from datetime import datetime, timezone, date
from extensions import db
from models.lead import Lead
from models.truncation_batch import TruncationBatch
from models.system_alert import SystemAlert
from services.alert_service import create_alert

logger = logging.getLogger(__name__)


def check_and_run():
    now_utc = datetime.now(timezone.utc)
    if now_utc.day != 1 or now_utc.hour != 1:
        return
    month_start = date(now_utc.year, now_utc.month, 1)
    existing = TruncationBatch.query.filter_by(batch_month=month_start).first()
    if existing:
        return
    logger.info(f'Starting monthly truncation for {month_start}')
    run_truncation(now_utc, month_start)


def run_truncation(now_utc=None, month_start=None):
    if now_utc is None:
        now_utc = datetime.now(timezone.utc)
    if month_start is None:
        month_start = date(now_utc.year, now_utc.month, 1)
    batch_id_str = f'{month_start.strftime("%Y-%m")} Monthly Truncation'
    batch = TruncationBatch(batch_id=batch_id_str, batch_month=month_start,
                            started_at=now_utc, status='pending')
    db.session.add(batch)
    db.session.flush()
    try:
        active_leads = Lead.query.filter_by(is_active=True).all()
        truncated = incomplete = 0
        for lead in active_leads:
            lead.is_active = False
            lead.is_complete = True
            lead.truncation_datetime = now_utc
            lead.truncation_batch_id = batch.id
            if not lead.has_outcome:
                lead.is_incomplete = True
                incomplete += 1
            truncated += 1
        batch.leads_truncated_count = truncated
        batch.incomplete_leads_count = incomplete
        batch.completed_at = datetime.now(timezone.utc)
        batch.status = 'completed'
        db.session.commit()
        logger.info(f'Truncation complete: {truncated} leads, {incomplete} incomplete')
    except Exception as e:
        db.session.rollback()
        batch.status = 'failed'
        batch.error_message = str(e)
        try:
            db.session.commit()
        except Exception:
            pass
        create_alert(SystemAlert.TRUNCATION_FAILURE,
                     f'Monthly truncation failed for {batch_id_str}: {e}', severity='critical')
        raise
