from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField


class AddOrganizationForm(FlaskForm):
    org_github_name = StringField(label='Organizations github name:')
    submit = SubmitField(label='Add')

class JenkinsApiForm(FlaskForm):
    jenkins_url = StringField(label='Jenkins url:')
    submit = SubmitField(label='Set')
