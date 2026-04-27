"""
IMAP connection test script.
Run this on PythonAnywhere (or locally) to verify your Gmail App Password works.

Usage:
    python test_imap_connection.py

Requires GMAIL_ADDRESS and GMAIL_APP_PASSWORD to be set in your .env file,
or exported as environment variables.
"""
import sys
import os
import imaplib

# Load .env if present
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

address = os.environ.get('GMAIL_ADDRESS', 'data@thrivemediagroup.co.uk')
app_password = os.environ.get('GMAIL_APP_PASSWORD')

if not app_password:
    print('ERROR: GMAIL_APP_PASSWORD is not set.')
    print('Add it to your .env file or export it as an environment variable.')
    sys.exit(1)

print(f'Testing IMAP connection for {address}...')

try:
    conn = imaplib.IMAP4_SSL('imap.gmail.com', 993)
    conn.login(address, app_password)
    print('  ✓ Login successful')

    status, data = conn.list()
    mailboxes = [item.decode() for item in data if item]
    print(f'  ✓ {len(mailboxes)} mailboxes/labels found')

    # Show user-created labels only
    user_labels = [m for m in mailboxes if '[Gmail]' not in m and '[Google Mail]' not in m and 'INBOX' not in m]
    if user_labels:
        print('\n  User labels found:')
        for lbl in sorted(user_labels):
            # Extract just the label name from the IMAP response
            parts = lbl.split(' "/" ')
            name = parts[-1].strip().strip('"') if len(parts) > 1 else lbl
            print(f'    - {name}')
    else:
        print('  No user-created labels found (you can create them in Gmail).')

    conn.logout()
    print('\n✅ Connection test passed. Your App Password is working correctly.')
    print('   Copy your label names above into Settings → Gmail Labels in the app.')

except imaplib.IMAP4.error as e:
    print(f'\n❌ IMAP authentication error: {e}')
    print('   Check your App Password. Note: this must be a Gmail App Password,')
    print('   not your regular Google account password.')
    sys.exit(1)
except Exception as e:
    print(f'\n❌ Connection error: {e}')
    sys.exit(1)
