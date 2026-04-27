import secrets, string
from datetime import datetime, timezone, timedelta
from flask import current_app, url_for
from flask_mail import Message
from extensions import db, mail


def generate_reset_token():
    alpha = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alpha) for _ in range(64))


def send_password_reset_email(user):
    token = generate_reset_token()
    user.reset_token = token
    user.reset_token_expires_at = datetime.now(timezone.utc) + timedelta(
        seconds=current_app.config['PASSWORD_RESET_EXPIRY'])
    db.session.commit()
    reset_url = url_for('auth.reset_password', token=token, _external=True)
    msg = Message(subject='Thrive Lead Manager — Password Reset', recipients=[user.email])
    msg.body = (f'Hi {user.display_name},\n\n'
                f'Reset your password here (valid 1 hour):\n\n{reset_url}\n\n'
                f'If you did not request this, ignore this email.\n\n— Thrive Lead Manager')
    try:
        mail.send(msg)
        return True
    except Exception as e:
        current_app.logger.error(f'Failed to send reset email to {user.email}: {e}')
        return False


def verify_reset_token(token):
    from models.user import User
    if not token:
        return None
    user = User.query.filter_by(reset_token=token, is_active=True).first()
    if not user or not user.reset_token_expires_at:
        return None
    expires = user.reset_token_expires_at
    if expires.tzinfo is None:
        expires = expires.replace(tzinfo=timezone.utc)
    if datetime.now(timezone.utc) > expires:
        return None
    return user


def clear_reset_token(user):
    user.reset_token = None
    user.reset_token_expires_at = None
    db.session.commit()
