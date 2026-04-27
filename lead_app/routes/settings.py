from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required
from extensions import db
from models.agent_profile import AgentProfile
from models.monitored_label import MonitoredGmailLabel
from models.eligibility import AgentProviderEligibility
from models.outcome_option import OutcomeOption
from forms.agent_forms import AgentForm
from forms.settings_forms import LabelForm, OutcomeForm
from utils.decorators import manager_required, admin_required

settings_bp = Blueprint('settings', __name__, url_prefix='/settings')


# ── AGENTS ──────────────────────────────────────────────────────────────────

@settings_bp.route('/agents')
@login_required
@manager_required
def agents():
    all_agents = AgentProfile.query.order_by(AgentProfile.display_name).all()
    labels = MonitoredGmailLabel.query.filter_by(is_active=True).all()
    return render_template('settings/agents.html', agents=all_agents, labels=labels)


@settings_bp.route('/agents/new', methods=['GET', 'POST'])
@login_required
@manager_required
def new_agent():
    from models.user import User
    form = AgentForm()
    if form.validate_on_submit():
        if User.query.filter_by(username=form.username.data.strip()).first():
            flash('Username already taken.', 'danger')
        elif not form.password.data:
            flash('Password required for new agent.', 'danger')
        else:
            user = User(username=form.username.data.strip(),
                        email=form.email.data.strip().lower(),
                        display_name=form.display_name.data.strip(),
                        role='agent')
            user.set_password(form.password.data)
            db.session.add(user)
            db.session.flush()
            profile = AgentProfile(user_id=user.id,
                                   display_name=form.display_name.data.strip(),
                                   balance_integer=form.balance_integer.data or 0)
            db.session.add(profile)
            db.session.commit()
            flash(f'Agent {profile.display_name} created.', 'success')
            return redirect(url_for('settings.agents'))
    return render_template('settings/agent_form.html', form=form, title='New Agent')


@settings_bp.route('/agents/<int:agent_id>/edit', methods=['GET', 'POST'])
@login_required
@manager_required
def edit_agent(agent_id):
    profile = AgentProfile.query.get_or_404(agent_id)
    form = AgentForm(obj=profile)
    if form.validate_on_submit():
        profile.display_name = form.display_name.data.strip()
        profile.balance_integer = form.balance_integer.data or 0
        profile.user.display_name = profile.display_name
        if form.password.data:
            profile.user.set_password(form.password.data)
        db.session.commit()
        flash(f'Agent {profile.display_name} updated.', 'success')
        return redirect(url_for('settings.agents'))
    form.username.data = profile.user.username
    form.email.data = profile.user.email
    return render_template('settings/agent_form.html', form=form, agent=profile, title='Edit Agent')


@settings_bp.route('/agents/<int:agent_id>/toggle', methods=['POST'])
@login_required
@manager_required
def toggle_agent(agent_id):
    profile = AgentProfile.query.get_or_404(agent_id)
    profile.is_active_for_distribution = not profile.is_active_for_distribution
    profile.user.is_active = profile.is_active_for_distribution
    db.session.commit()
    status = 'activated' if profile.is_active_for_distribution else 'deactivated'
    flash(f'Agent {profile.display_name} {status}.', 'success')
    return redirect(url_for('settings.agents'))


# ── GMAIL LABELS ─────────────────────────────────────────────────────────────

@settings_bp.route('/labels')
@login_required
@manager_required
def labels():
    all_labels = MonitoredGmailLabel.query.order_by(MonitoredGmailLabel.gmail_label_path).all()
    return render_template('settings/labels.html', labels=all_labels)


@settings_bp.route('/labels/gmail-available')
@login_required
@manager_required
def gmail_available_labels():
    from services.gmail_service import fetch_available_labels
    available = fetch_available_labels()
    return jsonify(available)


@settings_bp.route('/labels/new', methods=['GET', 'POST'])
@login_required
@manager_required
def new_label():
    form = LabelForm()
    if form.validate_on_submit():
        label = MonitoredGmailLabel(
            gmail_label_id=form.gmail_label_id.data.strip(),
            gmail_label_path=form.gmail_label_path.data.strip(),
            provider_display_name=form.provider_display_name.data.strip())
        db.session.add(label)
        db.session.commit()
        flash(f'Label "{label.provider_display_name}" added.', 'success')
        return redirect(url_for('settings.labels'))
    return render_template('settings/label_form.html', form=form, title='Add Gmail Label')


@settings_bp.route('/labels/<int:label_id>/edit', methods=['GET', 'POST'])
@login_required
@manager_required
def edit_label(label_id):
    label = MonitoredGmailLabel.query.get_or_404(label_id)
    form = LabelForm(obj=label)
    if form.validate_on_submit():
        label.gmail_label_id = form.gmail_label_id.data.strip()
        label.gmail_label_path = form.gmail_label_path.data.strip()
        label.provider_display_name = form.provider_display_name.data.strip()
        db.session.commit()
        flash('Label updated.', 'success')
        return redirect(url_for('settings.labels'))
    return render_template('settings/label_form.html', form=form, label=label, title='Edit Label')


@settings_bp.route('/labels/<int:label_id>/toggle', methods=['POST'])
@login_required
@manager_required
def toggle_label(label_id):
    label = MonitoredGmailLabel.query.get_or_404(label_id)
    label.is_active = not label.is_active
    db.session.commit()
    status = 'activated' if label.is_active else 'deactivated'
    flash(f'Label "{label.provider_display_name}" {status}.', 'success')
    return redirect(url_for('settings.labels'))


# ── OUTCOME OPTIONS ───────────────────────────────────────────────────────────

@settings_bp.route('/outcomes')
@login_required
@manager_required
def outcomes():
    all_outcomes = OutcomeOption.query.order_by(OutcomeOption.sort_order, OutcomeOption.name).all()
    form = OutcomeForm()
    return render_template('settings/outcomes.html', outcomes=all_outcomes, form=form)


@settings_bp.route('/outcomes/add', methods=['POST'])
@login_required
@manager_required
def add_outcome():
    form = OutcomeForm()
    if form.validate_on_submit():
        if OutcomeOption.query.filter_by(name=form.name.data.strip()).first():
            flash('An outcome with that name already exists.', 'danger')
        else:
            max_order = db.session.query(db.func.max(OutcomeOption.sort_order)).scalar() or 0
            option = OutcomeOption(name=form.name.data.strip(), sort_order=max_order + 1)
            db.session.add(option)
            db.session.commit()
            flash(f'Outcome "{option.name}" added.', 'success')
    return redirect(url_for('settings.outcomes'))


@settings_bp.route('/outcomes/<int:outcome_id>/toggle', methods=['POST'])
@login_required
@manager_required
def toggle_outcome(outcome_id):
    option = OutcomeOption.query.get_or_404(outcome_id)
    option.is_active = not option.is_active
    db.session.commit()
    return redirect(url_for('settings.outcomes'))


@settings_bp.route('/outcomes/<int:outcome_id>/rename', methods=['POST'])
@login_required
@manager_required
def rename_outcome(outcome_id):
    option = OutcomeOption.query.get_or_404(outcome_id)
    new_name = request.form.get('name', '').strip()
    if new_name:
        option.name = new_name
        db.session.commit()
        flash('Outcome renamed.', 'success')
    return redirect(url_for('settings.outcomes'))


# ── ROUTING MATRIX ───────────────────────────────────────────────────────────

@settings_bp.route('/routing')
@login_required
@manager_required
def routing():
    agents = AgentProfile.query.filter_by(is_active_for_distribution=True).order_by(AgentProfile.display_name).all()
    labels = MonitoredGmailLabel.query.filter_by(is_active=True).order_by(MonitoredGmailLabel.provider_display_name).all()
    # Build eligibility lookup: (agent_id, label_id) -> bool
    eligibilities = AgentProviderEligibility.query.all()
    elig_map = {(e.agent_profile_id, e.monitored_gmail_label_id): e.is_eligible for e in eligibilities}
    return render_template('settings/routing.html', agents=agents, labels=labels, elig_map=elig_map)


@settings_bp.route('/routing/toggle', methods=['POST'])
@login_required
@manager_required
def toggle_routing():
    agent_id = request.form.get('agent_id', type=int)
    label_id = request.form.get('label_id', type=int)
    if not agent_id or not label_id:
        return ('', 400)
    elig = AgentProviderEligibility.query.filter_by(
        agent_profile_id=agent_id, monitored_gmail_label_id=label_id).first()
    if elig:
        elig.is_eligible = not elig.is_eligible
    else:
        elig = AgentProviderEligibility(agent_profile_id=agent_id,
                                        monitored_gmail_label_id=label_id, is_eligible=True)
        db.session.add(elig)
    db.session.commit()
    return ('', 204)
