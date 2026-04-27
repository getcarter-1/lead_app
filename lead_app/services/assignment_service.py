import logging, random
from datetime import datetime, timezone
from extensions import db
from models.agent_profile import AgentProfile
from models.eligibility import AgentProviderEligibility
from models.system_alert import SystemAlert
from services.alert_service import create_alert

logger = logging.getLogger(__name__)


def assign_lead(lead, monitored_label_id):
    try:
        eligible = (db.session.query(AgentProfile)
                    .join(AgentProviderEligibility,
                          AgentProviderEligibility.agent_profile_id == AgentProfile.id)
                    .filter(AgentProviderEligibility.monitored_gmail_label_id == monitored_label_id,
                            AgentProviderEligibility.is_eligible == True,
                            AgentProfile.is_active_for_distribution == True)
                    .all())
        if not eligible:
            _handle_no_agent(lead, monitored_label_id)
            return None
        scored = [(p.distribution_score, p) for p in eligible]
        min_score = min(s for s, _ in scored)
        candidates = [p for s, p in scored if s == min_score]
        chosen = random.choice(candidates)
        lead.assigned_agent_profile_id = chosen.id
        lead.assigned_agent_name_snapshot = chosen.display_name
        lead.assigned_at = datetime.now(timezone.utc)
        logger.info(f'Lead {lead.id} assigned to {chosen.display_name}')
        return chosen
    except Exception as e:
        logger.error(f'Assignment error: {e}')
        create_alert(SystemAlert.LEAD_ASSIGNMENT_FAILURE, f'Failed to assign lead {lead.id}: {e}',
                     related_lead_id=lead.id)
        return None


def _handle_no_agent(lead, monitored_label_id):
    from models.monitored_label import MonitoredGmailLabel
    label = db.session.get(MonitoredGmailLabel, monitored_label_id)
    label_name = label.provider_display_name if label else str(monitored_label_id)
    lead.assigned_agent_name_snapshot = 'UNASSIGNED'
    create_alert(SystemAlert.NO_ELIGIBLE_AGENT,
                 f'No eligible agent for "{label_name}". Lead {lead.id} stored as unassigned.',
                 severity='warning', related_label=label_name, related_lead_id=lead.id)
