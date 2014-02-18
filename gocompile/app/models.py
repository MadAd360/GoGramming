from app import db

ROLE_USER = 0
ROLE_ADMIN = 1

class User(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    nickname = db.Column(db.String(64), unique = True)
    email = db.Column(db.String(120), unique = True)
    password = db.Column(db.String(120))
    role = db.Column(db.SmallInteger, default = ROLE_USER)
    repos = db.relationship('Rpstry', backref = 'owner', lazy = 'dynamic')
    errors = db.relationship('Error', backref = 'owner', lazy = 'dynamic')

    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return unicode(self.id)

    def check_password(self, input):
	if(self.password == input):
		return True
	return False

    def __repr__(self):
        return '<User %r>' % (self.nickname)

class Post(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    body = db.Column(db.String(140))
    timestamp = db.Column(db.DateTime)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __repr__(self):
        return '<Post %r>' % (self.body)

class Rpstry(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    repourl  = db.Column(db.String(140))
    files = db.relationship('File', backref = 'repo', lazy = 'dynamic')
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __repr__(self):
        return '<Rpstry %r>' % (self.repourl)

class File(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    path = db.Column(db.String(140))
    filename  = db.Column(db.String(140))
    type  = db.Column(db.String(140))
    repo_id = db.Column(db.Integer, db.ForeignKey('rpstry.id'))

    def __repr__(self):
        return '<File %r>' % (self.filename)

class Language(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    filetype  = db.Column(db.String(140), unique = True)
    compile  = db.Column(db.String(140))
    run  = db.Column(db.String(140))
    syntax = db.Column(db.String(140))

    def __repr__(self):
        return '< %r>' % (self.filetype)

class Error(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    path = db.Column(db.String(140))
    filename  = db.Column(db.String(140))
    message  = db.Column(db.Text)
    repo_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __repr__(self):
        return '<Error %r>' % (self.filename)
