from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.login import LoginManager

app = Flask(__name__, static_folder='/home/pi/application/gocompile/app/static')
app.config.from_object('config')
db = SQLAlchemy(app)
lm = LoginManager()
lm.init_app(app)
lm.login_view = 'login'

from app import views, models

if not app.debug:
    import logging
    from logging import FileHandler
    file_handler = FileHandler("/var/log/flask/errorlog.txt")
    file_handler.setLevel(logging.WARNING)
    app.logger.addHandler(file_handler)
