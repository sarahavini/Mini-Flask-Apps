import flask
from flask import Flask, render_template, request, abort, redirect, url_for, flash, jsonify
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from forms import tooldictform, userregistrer
from flask_sqlalchemy import SQLAlchemy

import os
from crew_ai_bot import ask_database

#for logging in / authentication
from flask_login import LoginManager, UserMixin, login_required, login_user, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash

#from app import db
app = Flask(__name__)
app.config['SECRET_KEY'] = 'mysecret'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///myDB.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

#initialize login manager tools
login_manager = LoginManager()
login_manager.init_app(app)

#initialize database so you can import models
db = SQLAlchemy(app)

#have to have db exist to run this
from models import ToolsLibrary, Users

with app.app_context():
    db.create_all()

@login_manager.user_loader
def load_user(id):
    return Users.query.get(int(id))

@app.errorhandler(404)
def not_found(e):
    return render_template('404.html')

@app.route('/', methods = ['GET', 'POST'])
def index():
    if request.method == 'GET':
        #id just browsing to the page display the initial form
        return(render_template('index.html',tools=ToolsLibrary.query.all()))

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/tooldetail/<tool_id>', methods=['GET', 'POST'])
@login_required
def tooldetail(tool_id):
    tool = ToolsLibrary.query.get(tool_id)
    if tool is None:
        abort(404)
    if request.method == 'POST':
        if "checkout_tool" in request.form:
            checkoutstatus = request.form.get('checkout_tool') == "True"
            tool.tool_available = checkoutstatus
            tool.checked_out_to = current_user.id
            db.session.commit()
        elif "checkin_tool" in request.form:
            checkoutstatus = request.form.get('checkin_tool') == "True"
            tool.tool_available = checkoutstatus
            tool.checked_out_to = None
            db.session.commit()     
        return render_template('tool_detail.html', tool=tool)
    return render_template('tool_detail.html', tool=tool)

@app.route('/tool/new', methods = ['GET', 'POST'])
@login_required
def addtool():
    tool_dict_form = tooldictform()
    if tool_dict_form.validate_on_submit():
        form_addition = ToolsLibrary(
                    tool_name=tool_dict_form.toolname.data,
                    tool_description=tool_dict_form.description.data,
                    tool_condition=tool_dict_form.condition.data,
                    tool_available=tool_dict_form.available.data,
                    owner_id=tool_dict_form.owner.data
                )
        db.session.add(form_addition)
        db.session.commit()
        return redirect(url_for('index'))
    return render_template('tool_form.html', template_form = tool_dict_form)

@app.route('/register', methods = ['GET', 'POST'])
def registeruser():
    user_register_form = userregistrer()
    if user_register_form.validate_on_submit():
        username = user_register_form.username.data
        email = user_register_form.email.data
        password = generate_password_hash(user_register_form.password.data)
        if Users.query.filter_by(user_name=username).first():
            return render_template('register_user.html', error='That username or email already exists')
        form_addition = Users(user_name=username, email=email, password_hash = password)
        db.session.add(form_addition)
        db.session.commit()
        return redirect(url_for('loginpage'))
    return render_template('register_user.html', template_form = user_register_form)

@app.route('/loginpage', methods = ['GET', 'POST'])
def loginpage():
    #if submitting the form with information
    if request.method == 'POST':
        username = request.form.get("username")
        password = request.form.get("password")

        user = Users.query.filter_by(user_name = username).first()

        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for('index'))
        else:
            return render_template('login.html', error='Invalid username or password')
    return render_template ('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('loginpage'))

@login_manager.unauthorized_handler
def unauthorized():
    flash("You are not logged in. You must login to view further details")
    return render_template (url_for('index'))

@app.route('/questions')
def questions():
    print("HIT QUESTIONS VIEW")
    return render_template('questions.html')

@app.route("/questions/ask", methods=["POST"])
def questions_ask():
    data = request.get_json(silent=True) or {}
    question = (data.get("question") or request.form.get("question") or "").strip()
    if not question:
        return jsonify(ok=False, answer="Type a question first."), 400
    try:
        return jsonify(ok=True, answer=ask_database(question))
    except Exception as exc:
        return jsonify(ok=False, answer=f"The assistant hit an error: {exc}"), 500