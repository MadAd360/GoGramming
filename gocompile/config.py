WTF_CSRF_ENABLED = True
SECRET_KEY = 'you-will-never-guess'

SQLALCHEMY_DATABASE_URI = "postgresql://postgres:runner6@localhost/gocompiledb"
SQLALCHEMY_MIGRATE_REPO = "/home/pi/application/gocompile/db_repository"

SECURITY_PASSWORD_HASH = 'sha512_crypt'
SECURITY_PASSWORD_SALT = '$2a$16$PnnIgfMwkOjGX4SkHqSOPO'

import os
basedir = os.path.abspath(os.path.dirname(__file__))

