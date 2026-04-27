from flask_wtf import FlaskForm
from wtforms import DateField, SelectField, TextAreaField, SubmitField, StringField
from wtforms.validators import Optional


class VaultFilterForm(FlaskForm):
    start_date = DateField('From', validators=[Optional()])
    end_date = DateField('To', validators=[Optional()])
    provider = SelectField('Provider', validators=[Optional()], choices=[])
    agent = SelectField('Agent', validators=[Optional()], choices=[])
    submit = SubmitField('Filter')

    class Meta:
        csrf = False  # filter form — GET request, no CSRF needed


class VaultEditForm(FlaskForm):
    outcome_option_id = SelectField('Outcome', coerce=int, validators=[Optional()])
    notes = TextAreaField('Notes', validators=[Optional()])
    submit = SubmitField('Save Changes')
