from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from extensions import db
from models.agent_profile import AgentProfile
from models.lead import Lead
from models.outcome_option import OutcomeOption
from forms.lead_forms import LeadUpdateForm

leads_bp = Blueprint('leads', __name__)


@leads_bp.route('/')
@login_required
def index():
    return redirect(url_for('leads.my_leads'))


@leads_bp.route('/my-leads')
@login_required
def my_leads():
    agent = None
    agent_leads = []
    if current_user.agent_profile:
        agent = current_user.agent_profile
        agent_leads = (Lead.query
                       .filter_by(assigned_agent_profile_id=agent.id, is_active=True)
                       .order_by(Lead.email_received_at.desc())
                       .all())
    outcomes = OutcomeOption.query.filter_by(is_active=True).order_by(OutcomeOption.sort_order).all()
    return render_template('leads/my_leads.html', agent=agent, agent_leads=agent_leads, outcomes=outcomes)


@leads_bp.route('/dashboard')
@login_required
def dashboard():
    agents = AgentProfile.query.order_by(AgentProfile.display_name).all()
    selected_id = request.args.get('agent_id', type=int)
    selected_agent = None
    selected_leads = []
    if selected_id:
        selected_agent = AgentProfile.query.get_or_404(selected_id)
        selected_leads = (Lead.query
                          .filter_by(assigned_agent_profile_id=selected_id, is_active=True)
                          .order_by(Lead.email_received_at.desc())
                          .all())
    elif agents:
        selected_agent = agents[0]
        selected_leads = (Lead.query
                          .filter_by(assigned_agent_profile_id=selected_agent.id, is_active=True)
                          .order_by(Lead.email_received_at.desc())
                          .all())
    outcomes = OutcomeOption.query.filter_by(is_active=True).order_by(OutcomeOption.sort_order).all()
    return render_template('leads/dashboard.html', agents=agents,
                           selected_agent=selected_agent, selected_leads=selected_leads,
                           outcomes=outcomes)


@leads_bp.route('/dashboard/agent/<int:agent_id>')
@login_required
def agent_leads_partial(agent_id):
    agent = AgentProfile.query.get_or_404(agent_id)
    agent_leads = (Lead.query
                   .filter_by(assigned_agent_profile_id=agent_id, is_active=True)
                   .order_by(Lead.email_received_at.desc())
                   .all())
    outcomes = OutcomeOption.query.filter_by(is_active=True).order_by(OutcomeOption.sort_order).all()
    return render_template('partials/agent_leads.html', agent=agent,
                           agent_leads=agent_leads, outcomes=outcomes)


@leads_bp.route('/leads/<int:lead_id>/save', methods=['POST'])
@login_required
def save_lead(lead_id):
    lead = Lead.query.get_or_404(lead_id)
    can_edit = _can_edit_lead(lead)
    if not can_edit:
        abort(403)
    # Notes — anyone who can edit may always update
    notes = request.form.get('notes', '').strip()
    lead.notes = notes or None
    # Outcome
    outcome_id = request.form.get('outcome_option_id', type=int)
    if outcome_id:
        # Agents cannot change outcome once set
        if current_user.role == 'agent' and lead.has_outcome:
            pass  # ignore attempt
        else:
            option = OutcomeOption.query.get(outcome_id)
            if option:
                lead.outcome_option_id = option.id
                lead.outcome_text_snapshot = option.name
    elif current_user.is_manager_or_admin:
        lead.outcome_option_id = None
        lead.outcome_text_snapshot = None
    db.session.commit()
    outcomes = OutcomeOption.query.filter_by(is_active=True).order_by(OutcomeOption.sort_order).all()
    return render_template('partials/lead_card.html', lead=lead, outcomes=outcomes)


def _can_edit_lead(lead):
    if not lead.is_active:
        return current_user.is_manager_or_admin
    if current_user.is_manager_or_admin:
        return True
    # Agent can only edit their own lead
    if current_user.agent_profile and lead.assigned_agent_profile_id == current_user.agent_profile.id:
        return True
    return False
