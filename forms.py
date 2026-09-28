#this file makes the objects to put on the html forms. The html only renders what you create here

from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, BooleanField, SelectField, PasswordField
from wtforms.validators import DataRequired, Length

class tooldictform(FlaskForm):
    toolname = StringField("Name", validators=[DataRequired()])
    description = StringField("Description", validators=[DataRequired()])
    condition = SelectField("Condition",
                            choices=[("good", "Good"), ("meh", "Meh"), ("bad", "Bad")])
    available = BooleanField("Available", default=True)
    owner = StringField("Owner", validators=[DataRequired()])
    submit = SubmitField("Add Tool")

class userregistrer(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField('Repeat Password', validators=[DataRequired()])
    submit = SubmitField('Register')

