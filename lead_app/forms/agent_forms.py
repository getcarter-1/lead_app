from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, BooleanField, SelectField, SubmitField, PasswordField
from wtforms.validators import DataRequired, Optional, NumberRange, Email, Length, EqualTo


class AgentForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=80)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    display_name = StringField('Display Name', validators=[DataRequired(), Length(max=120)])
    password = PasswordField('Password', validators=[Optional(), Length(min=8)])
    confirm_password = PasswordField('Confirm Password',
                                     validators=[Optional(), EqualTo('password', message='Passwords must match')])
    balance_integer = IntegerField('Balance', validators=[Optional(), NumberRange(min=-100, max=100)], default=0)
    submit = SubmitField('Save')


class UserForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=80)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    display_name = StringField('Display Name', validators=[DataRequired()])
    role = SelectField('Role', choices=[('agent', 'Agent'), ('manager', 'Manager'), ('admin', 'Admin')])
    password = PasswordField('Password', validators=[Optional(), Length(min=8)])
    confirm_password = PasswordField('Confirm Password',
                                     validators=[Optional(), EqualTo('password', message='Passwords must match')])
    submit = SubmitField('Save')
