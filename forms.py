from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, Length

class RegisterForm(FlaskForm):
    username = StringField(
        "Username",
        validators=[DataRequired(), Length(min=3, max=100)]
    )
    email = StringField(
        "Email",
        validators=[DataRequired(), Email()]
    )
    password = PasswordField(
        "Password",
        validators=[DataRequired(), Length(min=6)]
    )
    submit = SubmitField("Register")

class LoginForm(FlaskForm):
    email = StringField(
        "Email",
        validators=[DataRequired(), Email()]
    )
    password = PasswordField(
        "Password",
        validators=[DataRequired()]
    )
    submit = SubmitField("Login")

class ComplaintForm(FlaskForm):
    title = StringField(
        "Title",
        validators=[DataRequired(), Length(min=5, max=200)]
    )
    description = StringField(
        "Description",
        validators=[DataRequired(), Length(min=10)]
    )
    submit = SubmitField("Submit Complaint")
