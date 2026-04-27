import os
from flask import Flask
from dotenv import load_dotenv

load_dotenv()


def create_app(config_name=None):
    app = Flask(__name__)
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'production')
    from config import config_map
    app.config.from_object(config_map.get(config_name, config_map['default']))

    from extensions import db, migrate, login_manager, mail, csrf
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    mail.init_app(app)
    csrf.init_app(app)

    with app.app_context():
        from models import user, agent_profile, monitored_label, eligibility  # noqa
        from models import lead, outcome_option, system_alert, truncation_batch  # noqa

    from routes.auth import auth_bp
    from routes.leads import leads_bp
    from routes.admin import admin_bp
    from routes.vault import vault_bp
    from routes.settings import settings_bp
    from routes.alerts import alerts_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(leads_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(vault_bp)
    app.register_blueprint(settings_bp)
    app.register_blueprint(alerts_bp)

    @app.context_processor
    def inject_globals():
        from flask_login import current_user
        unresolved_alerts = 0
        if current_user.is_authenticated and current_user.role in ('manager', 'admin'):
            from models.system_alert import SystemAlert
            unresolved_alerts = SystemAlert.query.filter_by(is_resolved=False).count()
        return dict(unresolved_alerts=unresolved_alerts)

    @app.errorhandler(403)
    def forbidden(e):
        from flask import render_template
        return render_template('errors/403.html'), 403

    @app.errorhandler(404)
    def not_found(e):
        from flask import render_template
        return render_template('errors/404.html'), 404

    return app
