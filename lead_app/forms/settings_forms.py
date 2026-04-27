from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, SubmitField
from wtforms.validators import DataRequired, Length


class LabelForm(FlaskForm):
    gmail_label_id = StringField('Gmail Label ID', validators=[DataRequired()])
    gmail_label_path = StringField('Gmail Label Path', validators=[DataRequired(), Length(max=255)])
    provider_display_name = StringField('Provider Display Name', validators=[DataRequired(), Length(max=120)])
    submit = SubmitField('Save')


class OutcomeForm(FlaskForm):
    name = StringField('Outcome Name', validators=[DataRequired(), Length(max=120)])
    submit = SubmitField('Add')
