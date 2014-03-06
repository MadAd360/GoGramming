from flask.ext.wtf import Form
from wtforms import TextField, BooleanField, PasswordField, SelectField
from wtforms.validators import Required, Email, EqualTo, Regexp
from models import User
import os
import settings
from passlib.hash import sha512_crypt

class LoginForm(Form):
    username = TextField('username', validators = [Required()])
    password = PasswordField('password', validators = [Required()])
    remember_me = BooleanField('remember_me', default = False)
    
    def __init__(self, *args, **kwargs):
        Form.__init__(self, *args, **kwargs)
        self.user = None

    def validate(self):
        # regular validation
        rv = Form.validate(self)
        if not rv:
            return False

        user = User.query.filter_by(nickname=self.username.data).first()
        if user is None:
            self.username.errors.append('Unknown username')
            return False

        #if not user.check_password(
	if not sha512_crypt.verify(self.password.data, user.password):
            self.password.errors.append('Invalid password')
            return False

        self.user = user
        return True

class CreateForm(Form):
    username = TextField('username', validators = [Required(), Regexp('^[^ ]*$')])
    email = TextField('email', validators = [Required(), Email()])
    password = PasswordField('password', validators = [Required()])
    confirm = PasswordField('confirm', validators = [Required(), EqualTo('password')])

    def __init__(self, *args, **kwargs):
        Form.__init__(self, *args, **kwargs)
        self.user = None

    def validate(self):
        rv = Form.validate(self)
        if not rv:
            return False

        user = User.query.filter_by(nickname=self.username.data).first()
        if user is not None:
            self.username.errors.append('Username already in use')
            return False
	if ("/" in self.username.data) or ("\\" in self.username.data):
	    self.username.errors.append('Username must not contain slashes')
            return False 

	user = User.query.filter_by(email=self.email.data).first()
        if user is not None:
            self.username.errors.append('Email already exists')
            return False

        self.user = user
        return True

class AddForm(Form):
    filename = TextField('filename', validators = [Required()])
    location = SelectField('location')
    type = SelectField('type')
	
class ShareForm(Form):
    user = TextField('user', validators = [Required()])
