from flask.ext.wtf import Form
from wtforms import TextField, BooleanField, PasswordField, SelectField, SelectMultipleField
from wtforms.validators import Required, Email, EqualTo, Regexp
from models import User
import os
import settings
from passlib.hash import sha256_crypt

class LoginForm(Form):
    username = TextField('username', validators = [Required('Username is Required')])
    password = PasswordField('password', validators = [Required('Password is Requied')])
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

	if not user.active:
            self.username.errors.append('User not activated')
            return False
	
        #if not user.check_password(
	if not sha256_crypt.verify(self.password.data, user.password):
            self.password.errors.append('Invalid password')
            return False

        self.user = user
        return True

class CreateForm(Form):
    username = TextField('username', validators = [Required('Username is Required'), Regexp('^[^ ]*$',message='Username must not have spaces')])
    email = TextField('email', validators = [Required('Email is Required'), Email()])
    password = PasswordField('password', validators = [Required('Password is Required')])
    confirm = PasswordField('confirm', validators = [Required('Confirm Password is Required'), EqualTo('password')])

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
    filename = TextField('filename', validators = [Required(), Regexp('^[^ ]*$', message='Filename must not have spaces')])
    location = SelectField('location')
    type = SelectField('type')

    def __init__(self, *args, **kwargs):
        Form.__init__(self, *args, **kwargs)

    def validate(self):
        rv = Form.validate(self)
        if not rv:
            return False

        if ("/" in self.filename.data) or ("\\" in self.filename.data):
            return False

        return True

	
class ShareForm(Form):
    shareuser = TextField('shareuser', validators = [Required()])

    def __init__(self, *args, **kwargs):
        Form.__init__(self, *args, **kwargs)

    def validate(self):
        rv = Form.validate(self)
        if not rv:
            return False

        user = User.query.filter_by(nickname=self.shareuser.data).first()
        if user is None:
            return False

        #user = User.query.filter_by(email=self.email.data).first()
        #if user is not None:
        #    self.username.errors.append('Email already exists')
        #    return False

        return True


class CommitForm(Form):
    repos = SelectField('repos')

class PushForm(Form):
    repos = SelectField('repos')

class PullForm(Form):
    repos = SelectField('repos')

class ChangeForm(Form):
    password = PasswordField('password', validators = [Required('Password is Required')])
    confirm = PasswordField('confirm', validators = [Required('Confirm Password is Required'), EqualTo('password')])

class ForgotResetForm(Form):
    password = PasswordField('password', validators = [Required('Password is Required')])
    confirm = PasswordField('confirm', validators = [Required('Confirm Password is Required'), EqualTo('password')])
    temppassword = PasswordField('temppassword', validators = [Required('Code is Required')])

class ForgotForm(Form):
    email = TextField('email', validators = [Required('Email is Required'), Email()])
    temppassword = PasswordField('temppassword', validators = [Required('Temporary Password is Required')])

    def __init__(self, *args, **kwargs):
        Form.__init__(self, *args, **kwargs)
        self.user = None

    def validate(self):
        # regular validation
        rv = Form.validate(self)
        if not rv:
            return False

        user = User.query.filter_by(email=self.email.data).first()
        if user is None:
            self.email.errors.append('Unknown Email Address')
            return False

	self.user = user
	return True

class ForgotUserForm(Form):
    email = TextField('email', validators = [Required('Email is Required'), Email()])

    def __init__(self, *args, **kwargs):
        Form.__init__(self, *args, **kwargs)
        self.user = None

    def validate(self):
        # regular validation
        rv = Form.validate(self)
        if not rv:
            return False

        user = User.query.filter_by(email=self.email.data).first()
        if user is None:
            self.email.errors.append('Unknown Email Address')
            return False

        self.user = user
        return True

class CopyForm(Form):
    copydirs = SelectField('copydirs')

class CompileForm(Form):
    options = SelectMultipleField('options')
