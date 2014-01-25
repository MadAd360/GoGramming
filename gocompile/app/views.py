from flask import render_template, flash, redirect, session, url_for, request, g
from flask.ext.login import login_user, logout_user, current_user, login_required
from app import app, db, lm
from forms import LoginForm, CreateForm
from models import User, ROLE_USER, ROLE_ADMIN
import os
import crypt
from git import *

@lm.user_loader
def load_user(id):
    return User.query.get(int(id))

@app.before_request
def before_request():
    g.user = current_user

@app.route('/')
@app.route('/index')
@login_required
def index():
    user = g.user
    posts = [ # fake array of posts
        { 
            'author': { 'nickname': 'John' }, 
            'body': 'Beautiful day in Portland!' 
        },
        { 
            'author': { 'nickname': 'Susan' }, 
            'body': 'The Avengers movie was so cool!' 
        }
    ]
    return render_template("index.html",
        title = 'Home',
        user = user,
        posts = posts)

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
	user = User(nickname=form.username.data, password=form.password.data, email=form.email.data, role=ROLE_USER)
	db.session.add(user)
	db.session.commit()
	newuser = user.nickname
	password = crypt.crypt(user.password,"22")
        os.system("sudo useradd -M -p " + password + " " + newuser)
	os.system("sudo mkdir /srv/local/" + newuser)
        os.system("sudo mkdir /srv/git/" + newuser)
	os.system("sudo chmod 777 /srv/git/" + newuser)
        os.system("sudo chmod 777 /srv/local/" + newuser)
	repo = Repo.init("/srv/git/" + newuser + "/", bare=True)
	working_repo = repo.clone("/srv/local/" + newuser + "/")
	#add user file next to git repo
        return redirect(url_for('login'))
    return render_template('createAccount.html',
        title = 'Create New Account',
        form = form)

