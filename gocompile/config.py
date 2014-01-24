WTF_CSRF_ENABLED = True
SECRET_KEY = 'you-will-never-guess'

SQLALCHEMY_DATABASE_URI = "postgresql://postgres:runner6@localhost/gocompiledb"
SQLALCHEMY_MIGRATE_REPO = "/home/pi/application/gocompile/db_repository"

import os
basedir = os.path.abspath(os.path.dirname(__file__))

#SQLALCHEMY_DATABASE_URI = 'postgresql:///' + os.path.join(basedir, 'app.db')
#SQLALCHEMY_MIGRATE_REPO = os.path.join(basedir, 'db_repository')
