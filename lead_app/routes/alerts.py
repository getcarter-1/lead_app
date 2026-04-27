from datetime import datetime, timezone
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from extensions import db
from models.system_alert import SystemAlert
from utils.decorators import manager_required

alerts_bp = Blueprint('alerts', __name__, url_prefix='/alerts')


@alerts_bp.route('/')
@login_required
@manager_required
def alerts():
    show_resolved = request.args.get('show_resolved') == '1'
    query = SystemAlert.query
    if not show_resolved:
        query = query.filter_by(is_resolved=False)
    all_alerts = query.order_by(SystemAlert.created_at.desc()).limit(200).all()
    return render_template('alerts/alerts.html', alerts=all_alerts, show_resolved=show_resolved)


@alerts_bp.route('/<int:alert_id>/resolve', methods=['POST'])
@login_required
@manager_required
def resolve_alert(alert_id):
    alert = SystemAlert.query.get_or_404(alert_id)
    alert.is_resolved = True
    alert.resolved_by_user_id = current_user.id
    alert.resolved_at = datetime.now(timezone.utc)
    from extensions import db
    db.session.commit()
    flash('Alert marked as resolved.', 'success')
    return redirect(url_for('alerts.alerts'))


@alerts_bp.route('/badge')
@login_required
def badge():
    count = SystemAlert.query.filter_by(is_resolved=False).count()
    return render_template('partials/alert_badge.html', count=count)
