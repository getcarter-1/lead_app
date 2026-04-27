import logging
from email.header import decode_header, make_header
from email.utils import parseaddr, parsedate_to_datetime

import html2text

logger = logging.getLogger(__name__)

_html_converter = html2text.HTML2Text()
_html_converter.ignore_links = False
_html_converter.ignore_images = True
_html_converter.body_width = 0


def _decode_header(value):
    """Decode a potentially MIME-encoded header string."""
    if not value:
        return ''
    try:
        return str(make_header(decode_header(value)))
    except Exception:
        return value or ''


def parse_imap_message(msg):
    """
    Parse a standard email.message.Message object (from imaplib) into
    structured fields.

    Returns a dict with:
        sender_email, sender_display_name, email_subject,
        email_body_text, email_received_at
    """
    result = {
        'sender_email': '',
        'sender_display_name': '',
        'email_subject': '',
        'email_body_text': '',
        'email_received_at': None,
    }

    try:
        # Sender
        from_header = msg.get('From', '')
        display_name, addr = parseaddr(from_header)
        result['sender_email'] = addr.lower().strip()
        result['sender_display_name'] = _decode_header(display_name) or addr

        # Subject
        result['email_subject'] = _decode_header(msg.get('Subject', '(no subject)'))

        # Received at — prefer Date header
        date_header = msg.get('Date', '')
        if date_header:
            try:
                result['email_received_at'] = parsedate_to_datetime(date_header)
            except Exception:
                pass

        # Body
        result['email_body_text'] = _extract_body(msg)

    except Exception as e:
        logger.error(f'Error parsing IMAP message: {e}')

    return result


def _extract_body(msg):
    """
    Walk the MIME tree and extract the best available plain-text body.
    Prefers text/plain; falls back to converting text/html.
    """
    plain_parts = []
    html_parts = []

    if msg.is_multipart():
        for part in msg.walk():
            if part.is_multipart():
                continue
            ct = part.get_content_type()
            if ct == 'text/plain':
                plain_parts.append(part)
            elif ct == 'text/html':
                html_parts.append(part)
    else:
        ct = msg.get_content_type()
        if ct == 'text/plain':
            plain_parts.append(msg)
        elif ct == 'text/html':
            html_parts.append(msg)

    if plain_parts:
        return _decode_part(plain_parts[0])

    if html_parts:
        html = _decode_part(html_parts[0])
        return _html_converter.handle(html)

    return ''


def _decode_part(part):
    """Decode a message part's payload to a Python string."""
    charset = part.get_content_charset() or 'utf-8'
    payload = part.get_payload(decode=True)
    if not payload:
        return ''
    try:
        return payload.decode(charset, errors='replace')
    except (LookupError, UnicodeDecodeError):
        return payload.decode('utf-8', errors='replace')
