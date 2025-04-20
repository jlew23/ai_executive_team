"""
Admin forms for the web dashboard.
"""

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, SelectField, TextAreaField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError

class UserForm(FlaskForm):
    """User form for admin."""
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=50)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[Length(min=8)])
    confirm_password = PasswordField('Confirm Password', validators=[EqualTo('password')])
    is_active = BooleanField('Active')
    roles = SelectField('Role', validators=[DataRequired()])
    submit = SubmitField('Save User')

class RoleForm(FlaskForm):
    """Role form for admin."""
    name = StringField('Role Name', validators=[DataRequired(), Length(min=3, max=50)])
    description = TextAreaField('Description')
    permissions = SelectField('Permissions', validators=[DataRequired()], multiple=True)
    submit = SubmitField('Save Role')
