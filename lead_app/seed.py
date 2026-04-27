"""
Database seeding script.
Run once after flask db upgrade to populate initial data.

Usage:
    FLASK_ENV=production python seed.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from extensions import db
from models.user import User
from models.agent_profile import AgentProfile
from models.outcome_option import OutcomeOption

app = create_app('production')

with app.app_context():
    print('Seeding database...')

    # ── Admin user ───────────────────────────────────────────────────────────
    if not User.query.filter_by(username='admin').first():
        admin = User(
            username='admin',
            email='admin@thrivemediagroup.co.uk',
            display_name='Admin',
            role='admin',
            is_active=True,
        )
        admin.set_password('ChangeMe123!')
        db.session.add(admin)
        db.session.flush()
        print('  ✓ Admin user created (username: admin, password: ChangeMe123!)')
        print('  ⚠  CHANGE THE ADMIN PASSWORD IMMEDIATELY AFTER FIRST LOGIN')
    else:
        print('  - Admin user already exists')

    # ── Test agent ───────────────────────────────────────────────────────────
    if not User.query.filter_by(username='test').first():
        test_user = User(
            username='test',
            email='test@thrivemediagroup.co.uk',
            display_name='Test',
            role='agent',
            is_active=True,
        )
        test_user.set_password('ChangeMe123!')
        db.session.add(test_user)
        db.session.flush()
        profile = AgentProfile(
            user_id=test_user.id,
            display_name='Test',
            balance_integer=0,
            is_active_for_distribution=True,
        )
        db.session.add(profile)
        print('  ✓ Test agent created (username: test, password: ChangeMe123!)')
    else:
        print('  - Test agent already exists')

    # ── Outcome options ───────────────────────────────────────────────────────
    initial_outcomes = ['spam', 'in CRM', 'Good']
    for i, name in enumerate(initial_outcomes):
        if not OutcomeOption.query.filter_by(name=name).first():
            db.session.add(OutcomeOption(name=name, is_active=True, sort_order=i))
            print(f'  ✓ Outcome "{name}" added')
        else:
            print(f'  - Outcome "{name}" already exists')

    db.session.commit()
    print('\nSeed complete.')
