import imaplib
import email
import logging
from datetime import datetime, timezone
from email.header import decode_header, make_header

from flask import current_app

from extensions import db
from models.monitored_label import MonitoredGmailLabel
from models.lead import Lead
from models.system_alert import SystemAlert
from services.email_parser import parse_imap_message
from services.assignment_service import assign_lead
from services.alert_service import create_alert

logger = logging.getLogger(__name__)


def _connect():
    """Open and return an authenticated IMAP SSL connection."""
    host = current_app.config['GMAIL_IMAP_HOST']
    port = current_app.config['GMAIL_IMAP_PORT']
    address = current_app.config['GMAIL_ADDRESS']
    app_password = current_app.config['GMAIL_APP_PASSWORD']

    conn = imaplib.IMAP4_SSL(host, port)
    conn.login(address, app_password)
    return conn


def poll_gmail():
    """
    Main polling function — called every 60 seconds by the scheduler.
    Scans all active monitored IMAP mailboxes for unseen messages.
    """
    logger.info('Starting Gmail IMAP poll...')

    try:
        conn = _connect()
    except imaplib.IMAP4.error as e:
        create_alert(SystemAlert.GMAIL_AUTH_FAILURE,
                     f'Gmail IMAP authentication failed: {e}', severity='critical')
        return
    except Exception as e:
        create_alert(SystemAlert.GMAIL_AUTH_FAILURE,
                     f'Gmail IMAP connection error: {e}', severity='critical')
        return

    try:
        active_labels = MonitoredGmailLabel.query.filter_by(is_active=True).all()
        if not active_labels:
            logger.info('No active monitored labels — nothing to poll')
            return

        for label in active_labels:
            try:
                _process_mailbox(conn, label)
            except Exception as e:
                logger.error(f'Error processing mailbox "{label.gmail_label_path}": {e}')
                create_alert(SystemAlert.GMAIL_POLL_FAILURE,
                             f'Error polling mailbox "{label.gmail_label_path}": {e}',
                             related_label=label.gmail_label_path)
    finally:
        try:
            conn.logout()
        except Exception:
            pass

    logger.info('Gmail IMAP poll complete')


def _process_mailbox(conn, label):
    """Select an IMAP mailbox and process all UNSEEN messages."""
    # Gmail labels are IMAP mailboxes; nested labels use '/' separator.
    # The mailbox name must be quoted if it contains spaces or special chars.
    mailbox_name = _quote_mailbox(label.gmail_label_path)

    status, _ = conn.select(mailbox_name, readonly=False)
    if status != 'OK':
        raise RuntimeError(f'Could not select mailbox "{label.gmail_label_path}"')

    status, data = conn.search(None, 'UNSEEN')
    if status != 'OK':
        raise RuntimeError(f'SEARCH failed for "{label.gmail_label_path}"')

    msg_nums = data[0].split()
    logger.info(f'Mailbox "{label.gmail_label_path}": {len(msg_nums)} unseen messages')

    for num in msg_nums:
        try:
            _process_single_message(conn, label, num)
        except Exception as e:
            logger.error(f'Failed to process message {num} in "{label.gmail_label_path}": {e}')
            create_alert(SystemAlert.EMAIL_PARSE_FAILURE,
                         f'Failed to process message in "{label.gmail_label_path}": {e}',
                         related_label=label.gmail_label_path)
            # Continue to next message — one bad email must not halt the cycle


def _process_single_message(conn, label, msg_num):
    """Fetch, parse, store and mark a single IMAP message."""
    status, msg_data = conn.fetch(msg_num, '(RFC822)')
    if status != 'OK' or not msg_data or msg_data[0] is None:
        raise RuntimeError(f'FETCH failed for message {msg_num}')

    raw_email = msg_data[0][1]
    msg = email.message_from_bytes(raw_email)

    parsed = parse_imap_message(msg)
    now = datetime.now(timezone.utc)

    lead = Lead(
        gmail_message_id=str(msg_num.decode() if isinstance(msg_num, bytes) else msg_num),
        gmail_thread_id=None,          # Not available via IMAP
        monitored_gmail_label_id=label.id,
        provider_display_name=label.provider_display_name,
        sender_email=parsed['sender_email'],
        sender_display_name=parsed['sender_display_name'],
        email_subject=parsed['email_subject'],
        email_body_text=parsed['email_body_text'],
        email_received_at=parsed['email_received_at'],
        processed_at=now,
        is_active=True,
    )

    db.session.add(lead)
    db.session.flush()
    assign_lead(lead, label.id)
    db.session.commit()
    logger.info(f'Lead {lead.id} created from message {msg_num}')

    # Mark as seen (read) — stays in the same mailbox/label
    conn.store(msg_num, '+FLAGS', '\\Seen')
    logger.debug(f'Marked message {msg_num} as Seen')


def _quote_mailbox(name):
    """
    Wrap the mailbox name in double quotes.
    Required for Gmail labels containing spaces, slashes, or special chars.
    """
    # Escape any existing double quotes in the name
    escaped = name.replace('\\', '\\\\').replace('"', '\\\"')
    return f'"{escaped}"'


def fetch_available_labels():
    """
    List all IMAP mailboxes (Gmail labels) in the account.
    Returns a list of dicts: [{id, name}, ...]
    Used by the admin UI when adding a monitored label.
    """
    try:
        conn = _connect()
        status, mailbox_list = conn.list()
        conn.logout()

        if status != 'OK':
            return []

        labels = []
        for item in mailbox_list:
            if item is None:
                continue
            decoded = item.decode('utf-8', errors='replace') if isinstance(item, bytes) else item
            # IMAP LIST response format: (\HasNoChildren) "/" "Label/Name"
            # Extract the mailbox name from the end
            parts = decoded.split(' "/" ')
            if len(parts) < 2:
                parts = decoded.split(' "." ')  # some servers use dot separator
            if len(parts) < 2:
                continue
            name = parts[-1].strip().strip('"')
            # Skip Gmail system folders
            skip_prefixes = ('[Gmail]', '[Google Mail]', 'INBOX')
            if any(name.startswith(p) for p in skip_prefixes):
                continue
            labels.append({'id': name, 'name': name})

        return sorted(labels, key=lambda x: x['name'])

    except Exception as e:
        logger.error(f'Failed to fetch IMAP mailboxes: {e}')
        return []
