from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField


class AddOrganizationForm(FlaskForm):
    org_github_name = StringField(label='Organizations github name:')
    submit = SubmitField(label='Add')