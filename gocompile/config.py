import os
basedir = os.path.abspath(os.path.dirname(__file__))

WTF_CSRF_ENABLED = True
SECRET_KEY = '$2a$16$PnnI'

SQLALCHEMY_DATABASE_URI = "postgresql://postgres:runner6@localhost/gocompiledb"
SQLALCHEMY_MIGRATE_REPO = basedir + "/db_repository"

SECURITY_PASSWORD_HASH = 'sha512_crypt'
SECURITY_PASSWORD_SALT = '$2a$16$PnnIgfMwkOjGX4SkHqSOPO'

# email server
MAIL_SERVER = 'smtp.googlemail.com'
MAIL_PORT = 465
MAIL_USE_TLS = False
MAIL_USE_SSL = True
MAIL_USERNAME = 'gogramminguk'
MAIL_PASSWORD = 'adminpass24'

# administrator list
ADMINS = ['gogramminguk@gmail.com']


