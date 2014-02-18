from flask import render_template, flash, redirect, session, url_for, request, g, make_response
from flask.ext.login import login_user, logout_user, current_user, login_required
from app import app, db, lm
from forms import LoginForm, CreateForm, AddForm
from models import User, Post, Rpstry, File, Language, Error, ROLE_USER, ROLE_ADMIN
import os
import crypt
from dulwich.repo import Repo
import subprocess
import random
import datetime
import settings
from passlib.hash import sha512_crypt
import language_loader


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

def getfolders(user):
    path = settings.WORKING_DIR + user.nickname
    dirs = []
    for sub in os.listdir(path):
	subpath = path + "/" + sub
	if os.path.isdir(subpath):
	    within = recurfolders(user, sub, 2)
	    dirs.extend( [
            {
            	'folder': sub ,
		'folderpath': sub,
            	'within': within,
		'right': True
            }])
    return dirs 

def recurfolders(user, userpath, iternum):
    path = settings.WORKING_DIR + user.nickname + "/" + userpath
    dirs = []	    
    for sub in os.listdir(path):
        subpath = path + "/" + sub
        if os.path.isdir(subpath) and not sub == ".git":
	    if iternum == 5:
		iternum = 1
	    rightorient = True
	    if iternum  >= 3:
		rightorient = False
            within = recurfolders(user, userpath + "/" + sub, iternum + 1 )
            dirs.extend( [
            {
                'folder': sub ,
                'folderpath': userpath + "/" + sub,
                'within': within,
		'right': rightorient
            }])
    return dirs

def allsubdirectories(path, prefix):
    available = []
    for sub in os.listdir(path):
	subpath = path + "/" + sub
       	if os.path.isdir(subpath) and not sub == ".git":
	    display = prefix + sub
            available.extend([(subpath,display)])
	    available.extend(allsubdirectories(subpath, prefix + "-"))

    return available


def menusetup(user):
    form = AddForm()
    available = []
    localrepopath = settings.WORKING_DIR + user.nickname
    #for root, dirs, files in os.walk(localrepopath, topdown=True):
	#if '.git' in dirs:
      	    #dirs.remove('.git')
    	#for sub in dirs:
	    #available.extend([(sub,sub)])
    for sub in os.listdir(localrepopath):
	subpath = localrepopath + "/" + sub
        if os.path.isdir(subpath):
           available.extend([(sub,sub)])
	   available.extend(allsubdirectories(subpath, "|-"))
    form.location.choices = available


    if form.validate_on_submit():
	userlocation = form.location.data
	locationpath = settings.WORKING_DIR + user.nickname + "/" + userlocation
	if os.path.isdir(locationpath):
		filepath = locationpath + "/" + form.filename.data
        	if not os.path.isfile(filepath):
            	    open(filepath, 'a').close()
		    repository = userlocation.split("/")[0]
            	    myrepo = user.repos.filter_by(repourl= "/" + repository + "/" ).first()
            	    f = File(filename=form.filename.data, path=userlocation, type="txt", repo=myrepo)

            	    db.session.add(f)
            	    db.session.commit()
    else: menubutton(user)    	

    return form

def menubutton(user):
        if request.method == 'POST':
            if request.form.get('bar', None) == 'Commit':
		p1 = subprocess.Popen(["sudo", "git", "add", "-A"], cwd=settings.WORKING_DIR + user.nickname +"/myRepo/")
        	p1.wait()
        	working_repo = Repo(settings.WORKING_DIR + user.nickname + "/myRepo/")
		working_repo.do_commit("Test commit", committer=user.nickname + "<" + user.email + ">")
            if request.form.get('bar', None) == 'Push':
                p1 = subprocess.Popen(["sudo", "git", "push", "origin", "master"], cwd=settings.WORKING_DIR + user.nickname + "/myRepo/")
                p1.wait()
	    if request.form.get('bar', None) == 'Pull':
                p1 = subprocess.Popen(["sudo", "git", "pull", "origin", "master"], cwd=settings.WORKING_DIR + user.nickname + "/myRepo/")
                p1.wait()
	    if request.form.get('bar', None) == 'Compile':
		languages = Language.query.all()
		for lang in languages:
                    db.session.delete(lang)
		db.session.commit()
		language_loader.loadLanguages('plugins')

@app.route('/', methods = ['GET', 'POST'])
@app.route('/index', methods = ['GET', 'POST'])
@login_required
def index():
    user = g.user
    form = menusetup(user)
    dirs = getfolders(user)
	
    dbfiles = user.repos.filter_by().first().files    
    files = []	
    
    for file in dbfiles:
	name = file.filename
	filepath = settings.WORKING_DIR + user.nickname + "/" + file.path + "/" + name
	if os.path.isfile(filepath):
	    text = open(filepath, 'r').read()
	    files.extend( [
            { 
            	'filename': name , 
            	'content': text 
            }])
	else:
	    db.session.delete(file)
	    db.session.commit()
	
    return render_template("index.html",
        title = 'Home',
        user = user,
	form = form,
	dirs =  dirs,
	files = files)


@app.route('/edit/<path:filepath>', methods = ['GET', 'POST'])
@login_required
def edit(filepath):
    user = g.user
    form =  menusetup(user)
    dirs = getfolders(user)

    path = settings.WORKING_DIR + user.nickname + "/" + filepath	
    

    if  os.path.isfile(path):
	name = os.path.split(path)[1]
	tail = os.path.split(path)[0]
	output = ""

	if request.method == 'POST':
	    if request.form.get('btn', None) == 'Save':
		open(path, 'w').write(request.form['newcontent'])
	    if request.form.get('btn', None) == 'Delete':
                f = File.query.filter_by(filename=name).first()
		db.session.delete(f)
		db.session.commit()
		os.system("sudo rm " + path)
		return redirect(url_for('index'))
	    if request.form.get('btn', None) == 'Compile':
		templist = name.split('.')
		if len(templist) > 1:
		    type = templist[len(templist) - 1]
		    lang = Language.query.filter_by(filetype=type).first()
       	 	    if lang is not None:
			args = lang.compile.split()
			args.append(path)
			#errorfile = open(errorpath, 'w')
			p = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
			p.wait()
			text = ""
			for line in p.stdout:
			    text = text + line
			text = text.replace(settings.WORKING_DIR, '')
			existing = user.errors.filter_by(path=tail,filename=name).first()
			if existing is not None:
			    existing.message = text
			else:
			    error = Error(path=tail,filename=name, message=text, owner=user)
			    db.session.add(error)
			db.session.commit()
			#errorfile.close()	

	
	existing = user.errors.filter_by(path=tail,filename=name).first()
	if existing is not None:
	    output = existing.message
	#if os.path.exists(errorpath):
	#    errorfile = open(errorpath, 'r+')
	#    output = errorfile.read()
        text = open(path, 'r').read()
	file = {
            'filename': name ,
            'content': text
        }
    	return render_template("edit.html",
            title = 'Edit',
            user = user,
            form = form,
	    file = file,
	    dirs = dirs,
	    output = output)

    return redirect(url_for('index'))

	

@app.route('/login', methods = ['GET', 'POST'])
def login():
    if g.user is not None and g.user.is_authenticated():
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
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
	user = User(nickname=newuser, password=sha512_crypt.encrypt(form.password.data), email=form.email.data, role=ROLE_USER)
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
	p = subprocess.Popen(["sudo", "git", "remote", "add", "origin", "file:///" + settings.REMOTE_DIR + newuser + "/"], cwd=settings.WORKING_DIR + newuser + "/myRepo/")
	p.wait()
	open(settings.REMOTE_DIR + newuser + "/.htpasswd", 'a').writelines(newuser + ":" + password + "\n")
	return redirect(url_for('login'))
    return render_template('createAccount.html',
        title = 'Create New Account',
        form = form)


@app.route('/view/<path:filepath>', methods = ['GET', 'POST'])
@login_required
def view(filepath):
    user = g.user
    form = menusetup(user)
    dirs = getfolders(user)

    files = []

    folderpath = settings.WORKING_DIR + user.nickname + "/" + filepath
    if os.path.isdir(folderpath):
    	for sub in os.listdir(folderpath):
	    filepath = folderpath + "/" + sub
            if not os.path.isdir(filepath):
	    	name = sub
            	text = open(filepath, 'r').read()
            	files.extend( [
            	{
            	    'filename': name ,
            	    'content': text
           	 }])


    	return render_template("index.html",
            title = 'View',
            user = user,
            form = form,
            dirs =  dirs,
            files = files)

    return redirect(url_for('index'))
