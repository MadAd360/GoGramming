from flask import render_template, flash, redirect, session, url_for, request, g
from flask.ext.login import login_user, logout_user, current_user, login_required
from app import app, db, lm
from forms import LoginForm, CreateForm, AddForm
from models import User, Post, ROLE_USER, ROLE_ADMIN
import os
import crypt
from dulwich.repo import Repo
import subprocess
import random
import datetime

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

@app.route('/', methods = ['GET', 'POST'])
@app.route('/index', methods = ['GET', 'POST'])
@login_required
def index():
    user = g.user
    working = "/mnt/usb/local/"

    form = AddForm()
     
    if form.validate_on_submit():
	filepath = working + user.nickname + "/myRepo/" + form.filename.data
	if not os.path.isfile(filepath):
	    open(filepath, 'a').close()
            text = open(filepath, 'r').read()
	    p = Post(body=text, timestamp=datetime.datetime.utcnow(), author=user) 
	    db.session.add(p)
	    db.session.commit()

    files = [ # fake array of posts
        { 
            'filename': 'totesfake', 
            'content': 'Beautiful day in Portland!' 
        }
    ]
    return render_template("index.html",
        title = 'Home',
        user = user,
	form = form,
	files = files)

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
    working = "/mnt/usb/local/"
    remote = "/mnt/usb/git/"
    if form.validate_on_submit():
	newuser = form.username.data
	password = crypt.crypt(form.password.data,salt())
	user = User(nickname=newuser, password=form.password.data, email=form.email.data, role=ROLE_USER)
	db.session.add(user)
	db.session.commit()
        os.system("sudo useradd -M -p " + password + " " + newuser)
	os.system("sudo mkdir " + working + newuser)
        os.system("sudo mkdir " + remote + newuser)
	os.system("sudo mkdir " + working + newuser + "/myRepo")
	os.system("sudo chmod 777 " + remote + newuser)
        os.system("sudo chmod 777 " + working + newuser)
	repo = Repo.init_bare(remote  + newuser + "/")
	working_repo = repo.clone(working + newuser + "/myRepo/", False, False, "origin")
	#open(working + newuser + "/myRepo/testFile", 'a').close()
	#p1 = subprocess.Popen(["sudo", "git", "add", "-A"], cwd=working + newuser +"/myRepo/")
	#p1.wait()
	#working_repo.do_commit("The first commit", committer="Jelmer Vernooij <jelmer@samba.org>")
	p = subprocess.Popen(["sudo", "git", "remote", "add", "origin", "file:////mnt/usb/git/" + newuser + "/"], cwd=working + newuser +"/myRepo/")
	p.wait()
	open(remote + newuser + "/.htpasswd", 'a').writelines(newuser + ":" + password + "\n")
	return redirect(url_for('login'))
    return render_template('createAccount.html',
        title = 'Create New Account',
        form = form)

