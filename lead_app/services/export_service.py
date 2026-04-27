import csv, io
from datetime import datetime, timezone
from models.lead import Lead


def generate_vault_csv(start_date, end_date):
    query = Lead.query
    if start_date:
        start_dt = datetime(start_date.year, start_date.month, start_date.day, 0, 0, 0, tzinfo=timezone.utc)
        query = query.filter(Lead.email_received_at >= start_dt)
    if end_date:
        end_dt = datetime(end_date.year, end_date.month, end_date.day, 23, 59, 59, tzinfo=timezone.utc)
        query = query.filter(Lead.email_received_at <= end_dt)
    leads = query.order_by(Lead.email_received_at.desc()).all()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Lead ID','Provider','Gmail Label Path','Sender Email','Sender Name',
                     'Subject','Email Received (UTC)','Processed (UTC)','Assigned Agent',
                     'Assigned (UTC)','Outcome','Notes','Active','Complete','Incomplete',
                     'Truncation (UTC)','Truncation Batch','Email Body'])
    for lead in leads:
        label_path = lead.monitored_label.gmail_label_path if lead.monitored_label else ''
        writer.writerow([lead.id, lead.provider_display_name, label_path, lead.sender_email,
                         lead.sender_display_name or '', lead.email_subject or '',
                         _fmt(lead.email_received_at), _fmt(lead.processed_at),
                         lead.assigned_agent_name_snapshot or '', _fmt(lead.assigned_at),
                         lead.display_outcome, lead.notes or '',
                         'Yes' if lead.is_active else 'No',
                         'Yes' if lead.is_complete else 'No',
                         'Yes' if lead.is_incomplete else 'No',
                         _fmt(lead.truncation_datetime),
                         lead.truncation_batch.batch_id if lead.truncation_batch else '',
                         lead.email_body_text or ''])
    output.seek(0)
    return output


def _fmt(dt):
    if dt is None:
        return ''
    return dt.astimezone(timezone.utc).strftime('%Y-%m-%d %H:%M:%S') if dt.tzinfo else dt.strftime('%Y-%m-%d %H:%M:%S')
