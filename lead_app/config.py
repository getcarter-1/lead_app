import os
from datetime import timedelta


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'change-me-in-production')
    BASE_URL = os.environ.get('BASE_URL', 'https://yourusername.pythonanywhere.com')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'postgresql://localhost/lead_management')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {'pool_pre_ping': True, 'pool_recycle': 3600}
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = timedelta(hours=8)
    WTF_CSRF_TIME_LIMIT = 3600

    # Gmail IMAP (for reading inbound lead emails)
    GMAIL_ADDRESS = os.environ.get('GMAIL_ADDRESS', 'data@thrivemediagroup.co.uk')
    GMAIL_APP_PASSWORD = os.environ.get('GMAIL_APP_PASSWORD')
    GMAIL_IMAP_HOST = 'imap.gmail.com'
    GMAIL_IMAP_PORT = 993

    # Flask-Mail / Gmail SMTP (for sending password reset emails)
    # Uses the same address and App Password as IMAP above
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.environ.get('GMAIL_ADDRESS', 'data@thrivemediagroup.co.uk')
    MAIL_PASSWORD = os.environ.get('GMAIL_APP_PASSWORD')
    MAIL_DEFAULT_SENDER = ('Thrive Lead Manager',
                           os.environ.get('GMAIL_ADDRESS', 'data@thrivemediagroup.co.uk'))
    PASSWORD_RESET_EXPIRY = 3600


class DevelopmentConfig(Config):
    DEBUG = True
    SESSION_COOKIE_SECURE = False


class ProductionConfig(Config):
    DEBUG = False


config_map = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': ProductionConfig,
}
