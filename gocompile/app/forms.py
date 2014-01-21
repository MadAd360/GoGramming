activate_this = '/home/pi/application/gocompile.com/bin/activate_this.py'
execfile(activate_this, dict(__file__=activate_this))
from flask.ext.wtf import Form
from wtforms import TextField, BooleanField
from wtforms.validators import Required

class LoginForm(Form):
    user = TextField('Username', validators = [Required()])
    password = TextField('Password', validators = [Required()])
    remember_me = BooleanField('remember_me', default = False)
