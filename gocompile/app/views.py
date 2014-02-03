from flask import render_template, flash, redirect, session, url_for, request, g, make_response
from flask.ext.login import login_user, logout_user, current_user, login_required
from app import app, db, lm
from forms import LoginForm, CreateForm, AddForm
from models import User, Post, Rpstry, File, ROLE_USER, ROLE_ADMIN
import os
import crypt
from dulwich.repo import Repo
import subprocess
import random
import datetime
import settings

@lm.user_loader
def load_user(id):
    return User.query.get(int(id))

@app.before_request
def before_request():
    g.user = current_user

def salt():
    letters = 'abcdefghijklmnopqrstuvwxyz' \
              'ABCDEFGHIJKLMNOPQRSTUVWXYZ' \
              '0123456789/.'
    return random.choice(letters) + random.choice(letters)

def menusetup(user):
    form = AddForm()
    available = []
    localrepopath = settings.WORKING_DIR + user.nickname
    for sub in os.listdir(localrepopath):
       if os.path.isdir(localrepopath + "/" + sub):
           available.extend([(sub,sub)])
    form.repository.choices = available

    if form.validate_on_submit():
    	filepath = settings.WORKING_DIR + user.nickname + "/" + form.repository.data + "/" + form.filename.data
        if not os.path.isfile(filepath):
            open(filepath, 'a').close()
            myrepo = user.repos.filter_by(repourl= "/" + form.repository.data + "/" ).first()
            f = File(filename=form.filename.data, type="txt", repo=myrepo)

            db.session.add(f)
            db.session.commit()	

    return form

@app.route('/', methods = ['GET', 'POST'])
@app.route('/index', methods = ['GET', 'POST'])
@login_required
def index():
    user = g.user
    form = menusetup(user)

    dbfiles = user.repos.filter_by().first().files    
    files = []	
    
    for file in dbfiles:
	name = file.filename
	filepath = settings.WORKING_DIR + user.nickname + "/myRepo/" + name 
	text = open(filepath, 'r').read()
	files.extend( [
        { 
            'filename': name , 
            'content': text 
        }])
	
    return render_template("index.html",
        title = 'Home',
        user = user,
	form = form,
	files = files)


@app.route('/edit/<path:filepath>', methods = ['GET', 'POST'])
@login_required
def edit(filepath):
    user = g.user
    form =  menusetup(user)
    
    path = settings.WORKING_DIR + user.nickname + "/" + filepath	
    if  os.path.isfile(path):
	name = os.path.split(path)[1]
        text = open(path, 'r+').read()
        file = {
            'filename': name ,
            'content': text
        }
    	return render_template("edit.html",
            title = 'Edit',
            user = user,
            form = form,
	    file = file)

    return redirect(url_for('index'))

	

@app.route('/login', methods = ['GET', 'POST'])
def login():
    if g.user is not None and g.user.is_authenticated():
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        #session['remember_me'] = form.remember_me.data
	login_user(form.user, form.remember_me.data)
        return redirect(url_for('index'))
    return render_template('login.html', 
        title = 'Sign In',
        form = form)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/create', methods = ['GET', 'POST'])
def create():
    form = CreateForm()
    if form.validate_on_submit():
	newuser = form.username.data
	password = crypt.crypt(form.password.data,salt())
	user = User(nickname=newuser, password=form.password.data, email=form.email.data, role=ROLE_USER)
	db.session.add(user)
	db.session.commit()
        #os.system("sudo useradd -M -p " + password + " " + newuser)
	os.system("sudo mkdir " + settings.WORKING_DIR + newuser)
        os.system("sudo mkdir " + settings.REMOTE_DIR + newuser)
	os.system("sudo mkdir " + settings.WORKING_DIR + newuser + "/myRepo")
	os.system("sudo chmod 777 " + settings.REMOTE_DIR + newuser)
        os.system("sudo chmod 777 " + settings.WORKING_DIR + newuser)
	repo = Repo.init_bare(settings.REMOTE_DIR + newuser + "/")
	newrepo = Rpstry(repourl="/myRepo/", owner=user)
	db.session.add(newrepo)
        db.session.commit()
	working_repo = repo.clone(settings.WORKING_DIR + newuser + newrepo.repourl, False, False, "origin")
	#open(working + newuser + "/myRepo/testFile", 'a').close()
	#p1 = subprocess.Popen(["sudo", "git", "add", "-A"], cwd=working + newuser +"/myRepo/")
	#p1.wait()
	#working_repo.do_commit("The first commit", committer="Jelmer Vernooij <jelmer@samba.org>")
	p = subprocess.Popen(["sudo", "git", "remote", "add", "origin", "file:///" + settings.REMOTE_DIR + newuser + "/"], cwd=settings.WORKING_DIR + newuser + "/myRepo/")
	p.wait()
	open(settings.REMOTE_DIR + newuser + "/.htpasswd", 'a').writelines(newuser + ":" + password + "\n")
	return redirect(url_for('login'))
    return render_template('createAccount.html',
        title = 'Create New Account',
        form = form)

