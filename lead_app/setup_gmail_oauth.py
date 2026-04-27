"""
One-time Gmail OAuth 2.0 setup script.
Run this ONCE on your local machine (not on PythonAnywhere) to generate a refresh token.

Steps:
1. Create a Google Cloud project and enable the Gmail API.
2. Create OAuth 2.0 credentials (Desktop app type) and download the JSON.
3. Run: python setup_gmail_oauth.py --credentials /path/to/client_secret.json
4. A browser window will open — log in as data@thrivemediagroup.co.uk and grant access.
5. The script will print your GMAIL_REFRESH_TOKEN — copy it into your .env file.

Requirements: pip install google-auth-oauthlib
"""
import argparse
import json
import sys

try:
    from google_auth_oauthlib.flow import InstalledAppFlow
except ImportError:
    print('ERROR: Run: pip install google-auth-oauthlib')
    sys.exit(1)

SCOPES = ['https://www.googleapis.com/auth/gmail.modify']


def main():
    parser = argparse.ArgumentParser(description='Gmail OAuth setup')
    parser.add_argument('--credentials', required=True,
                        help='Path to downloaded OAuth client_secret JSON file')
    args = parser.parse_args()

    print('Starting OAuth flow — a browser window will open...')
    print('Log in as data@thrivemediagroup.co.uk when prompted.\n')

    flow = InstalledAppFlow.from_client_secrets_file(args.credentials, SCOPES)
    creds = flow.run_local_server(port=0)

    print('\n=== CREDENTIALS — Copy these into your .env file ===\n')
    print(f'GMAIL_CLIENT_ID={creds.client_id}')
    print(f'GMAIL_CLIENT_SECRET={creds.client_secret}')
    print(f'GMAIL_REFRESH_TOKEN={creds.refresh_token}')
    print('\n====================================================')
    print('\nNote: Keep these values secret. Never commit them to version control.')
    print('The refresh token does not expire unless you revoke access in Google Account settings.')


if __name__ == '__main__':
    main()
