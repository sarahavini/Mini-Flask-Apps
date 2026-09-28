#only model classes go in this file. this file doesnt make the db or add to it

from app import db
from flask_login import UserMixin

class ToolsLibrary(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    tool_name = db.Column(db.String(100), index=True)
    tool_description = db.Column(db.String(200), index=True)
    tool_condition = db.Column(db.String(100), index = True)
    tool_available = db.Column(db.Boolean, index=True)
    #link each tool to a user id
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    checked_out_to = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    
class Users(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key = True)
    user_name = db.Column(db.String, index=True, unique=True)
    email = db.Column(db.String, index=True, unique=True)
    password_hash = db.Column(db.String)

    #add a one to many relationship to the tools table
    #the model the relationship is with is ToolsLibrary
    #a .owner attribute is added to ToolsLibrary
    tools = db.relationship(
        'ToolsLibrary', 
        foreign_keys='[ToolsLibrary.owner_id]',
        primaryjoin='Users.id==ToolsLibrary.owner_id',
        backref='owner',
        lazy = True, 
        cascade = "all, delete-orphan"
        )
    checked_out_tools=db.relationship(
        'ToolsLibrary', 
        foreign_keys='[ToolsLibrary.checked_out_to]',
        primaryjoin='Users.id==ToolsLibrary.checked_out_to',
        backref='borrower', 
        lazy=True,cascade="all, delete-orphan"
        )
