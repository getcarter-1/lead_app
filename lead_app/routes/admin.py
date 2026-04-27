from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from extensions import db
from models.user import User
from models.agent_profile import AgentProfile
from forms.agent_forms import UserForm
from utils.decorators import admin_required
from utils.email_utils import send_password_reset_email

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


@admin_bp.route('/users')
@login_required
@admin_required
def users():
    all_users = User.query.order_by(User.display_name).all()
    return render_template('admin/users.html', users=all_users)


@admin_bp.route('/users/new', methods=['GET', 'POST'])
@login_required
@admin_required
def new_user():
    form = UserForm()
    if form.validate_on_submit():
        if User.query.filter_by(username=form.username.data.strip()).first():
            flash('Username already taken.', 'danger')
        elif User.query.filter_by(email=form.email.data.strip().lower()).first():
            flash('Email already registered.', 'danger')
        elif not form.password.data:
            flash('Password is required for new users.', 'danger')
        else:
            user = User(username=form.username.data.strip(),
                        email=form.email.data.strip().lower(),
                        display_name=form.display_name.data.strip(),
                        role=form.role.data)
            user.set_password(form.password.data)
            db.session.add(user)
            db.session.flush()
            if form.role.data == 'agent':
                profile = AgentProfile(user_id=user.id, display_name=form.display_name.data.strip())
                db.session.add(profile)
            db.session.commit()
            flash(f'User {user.display_name} created.', 'success')
            return redirect(url_for('admin.users'))
    return render_template('admin/user_form.html', form=form, title='New User')


@admin_bp.route('/users/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_user(user_id):
    user = User.query.get_or_404(user_id)
    form = UserForm(obj=user)
    if form.validate_on_submit():
        existing_username = User.query.filter_by(username=form.username.data.strip()).first()
        if existing_username and existing_username.id != user.id:
            flash('Username already taken.', 'danger')
        else:
            user.username = form.username.data.strip()
            user.email = form.email.data.strip().lower()
            user.display_name = form.display_name.data.strip()
            old_role = user.role
            user.role = form.role.data
            if form.password.data:
                user.set_password(form.password.data)
            # Create agent profile if role changed to agent
            if user.role == 'agent' and not user.agent_profile:
                profile = AgentProfile(user_id=user.id, display_name=user.display_name)
                db.session.add(profile)
            db.session.commit()
            flash(f'User {user.display_name} updated.', 'success')
            return redirect(url_for('admin.users'))
    return render_template('admin/user_form.html', form=form, user=user, title='Edit User')


@admin_bp.route('/users/<int:user_id>/toggle', methods=['POST'])
@login_required
@admin_required
def toggle_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash('You cannot deactivate your own account.', 'danger')
        return redirect(url_for('admin.users'))
    user.is_active = not user.is_active
    if user.agent_profile:
        user.agent_profile.is_active_for_distribution = user.is_active
    db.session.commit()
    status = 'activated' if user.is_active else 'deactivated'
    flash(f'User {user.display_name} {status}.', 'success')
    return redirect(url_for('admin.users'))


@admin_bp.route('/users/<int:user_id>/reset-password', methods=['POST'])
@login_required
@admin_required
def trigger_password_reset(user_id):
    user = User.query.get_or_404(user_id)
    if send_password_reset_email(user):
        flash(f'Password reset email sent to {user.email}.', 'success')
    else:
        flash('Failed to send reset email. Check mail configuration.', 'danger')
    return redirect(url_for('admin.users'))
