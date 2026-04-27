from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, make_response
from flask_login import login_required
from extensions import db
from models.lead import Lead
from models.outcome_option import OutcomeOption
from models.agent_profile import AgentProfile
from models.monitored_label import MonitoredGmailLabel
from forms.vault_forms import VaultEditForm, VaultFilterForm
from utils.decorators import admin_required
from services.export_service import generate_vault_csv

vault_bp = Blueprint('vault', __name__, url_prefix='/vault')


@vault_bp.route('/')
@login_required
@admin_required
def vault():
    form = VaultFilterForm(request.args)
    providers = db.session.query(Lead.provider_display_name).distinct().all()
    form.provider.choices = [('', 'All Providers')] + [(p[0], p[0]) for p in providers]
    agents = AgentProfile.query.order_by(AgentProfile.display_name).all()
    form.agent.choices = [('', 'All Agents')] + [(str(a.id), a.display_name) for a in agents]

    query = Lead.query
    if form.start_date.data:
        start_dt = datetime(form.start_date.data.year, form.start_date.data.month,
                            form.start_date.data.day)
        query = query.filter(Lead.email_received_at >= start_dt)
    if form.end_date.data:
        from datetime import timedelta
        end_dt = datetime(form.end_date.data.year, form.end_date.data.month,
                          form.end_date.data.day, 23, 59, 59)
        query = query.filter(Lead.email_received_at <= end_dt)
    if request.args.get('provider'):
        query = query.filter(Lead.provider_display_name == request.args['provider'])
    if request.args.get('agent'):
        query = query.filter(Lead.assigned_agent_profile_id == int(request.args['agent']))

    page = request.args.get('page', 1, type=int)
    leads = query.order_by(Lead.email_received_at.desc()).paginate(page=page, per_page=25, error_out=False)
    return render_template('vault/vault.html', form=form, leads=leads)


@vault_bp.route('/<int:lead_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_lead(lead_id):
    lead = Lead.query.get_or_404(lead_id)
    form = VaultEditForm(obj=lead)
    outcomes = OutcomeOption.query.order_by(OutcomeOption.sort_order).all()
    form.outcome_option_id.choices = [(0, '— No outcome —')] + [(o.id, o.name) for o in outcomes]
    if form.validate_on_submit():
        oid = form.outcome_option_id.data
        if oid:
            option = OutcomeOption.query.get(oid)
            lead.outcome_option_id = option.id if option else None
            lead.outcome_text_snapshot = option.name if option else None
        else:
            lead.outcome_option_id = None
            lead.outcome_text_snapshot = None
        lead.notes = form.notes.data or None
        db.session.commit()
        flash('Vault record updated.', 'success')
        return redirect(url_for('vault.vault'))
    return render_template('vault/vault_edit.html', form=form, lead=lead)


@vault_bp.route('/export')
@login_required
@admin_required
def export_csv():
    from datetime import date as date_type
    start_str = request.args.get('start_date')
    end_str = request.args.get('end_date')
    start_date = end_date = None
    try:
        if start_str:
            start_date = datetime.strptime(start_str, '%Y-%m-%d').date()
        if end_str:
            end_date = datetime.strptime(end_str, '%Y-%m-%d').date()
    except ValueError:
        pass
    csv_data = generate_vault_csv(start_date, end_date)
    filename = f'vault_export_{datetime.utcnow().strftime("%Y%m%d_%H%M%S")}.csv'
    response = make_response(csv_data.getvalue())
    response.headers['Content-Disposition'] = f'attachment; filename={filename}'
    response.headers['Content-Type'] = 'text/csv; charset=utf-8'
    return response
