from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.login import LoginManager
from flask.ext.mail import Mail
import os

basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__, static_folder=basedir + '/static')
app.config.from_object('config')
db = SQLAlchemy(app)
lm = LoginManager()
lm.init_app(app)
lm.login_view = 'login'
mail = Mail(app)

from app import views, models

if not app.debug:
    import logging
    from logging import FileHandler
    file_handler = FileHandler("/var/log/flask/errorlog.txt")
    file_handler.setLevel(logging.WARNING)
    app.logger.addHandler(file_handler)
