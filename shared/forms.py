from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, EqualTo, Length

# Admin Forms
class AdminLoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=20)])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class AdminSignupForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=20)])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[
        DataRequired(), EqualTo('password', message='Passwords must match.')
    ])
    submit = SubmitField('Sign Up')

# Driver Forms
class DriverLoginForm(FlaskForm):
    vehicle_no = StringField('Vehicle Number', validators=[DataRequired(), Length(min=6, max=10)])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class DriverSignupForm(FlaskForm):
    vehicle_no = StringField('Vehicle Number', validators=[DataRequired(), Length(min=6, max=10)])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[
        DataRequired(), EqualTo('password', message='Passwords must match.')
    ])
    submit = SubmitField('Sign Up')

# Citizen Forms
class CitizenLoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=20)])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')