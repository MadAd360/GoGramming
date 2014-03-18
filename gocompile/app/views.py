from flask import render_template, flash, redirect, session, url_for, request, g, make_response, jsonify, Response, stream_with_context
from flask.ext.login import login_user, logout_user, current_user, login_required
from app import app, db, lm, mail
from forms import LoginForm, CreateForm, AddForm, ShareForm, CommitForm, PushForm, PullForm, ChangeForm, ForgotForm, ForgotResetForm
from models import User, Post, Rpstry, File, Language, Error, ROLE_USER, ROLE_ADMIN
import os
import crypt
from dulwich.repo import Repo
import subprocess
from fcntl import fcntl, F_GETFL, F_SETFL
from os import O_NONBLOCK, read
import random
import datetime
import settings
from passlib.hash import sha512_crypt
from app import language_loader
import time
from plugins import *
import re
from flask.ext.mail import Message
from config import ADMINS
from itsdangerous import URLSafeSerializer, BadSignature


process = []


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

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

def allsubdirectories(user, parentpath, prefix):
    available = []
    path = settings.WORKING_DIR + user.nickname + "/" + parentpath
    for sub in os.listdir(path):
	subpath = path + "/" + sub
       	if os.path.isdir(subpath) and not sub == ".git":
	    childpath = parentpath + "/" + sub
	    display = prefix + sub
            available.extend([(childpath,display)])
	    available.extend(allsubdirectories(user, childpath, prefix + "-"))

    return available


def menusetup(user):
    form = AddForm()
    available = []
    localrepopath = settings.WORKING_DIR + user.nickname
    for sub in os.listdir(localrepopath):
	subpath = localrepopath + "/" + sub
        if os.path.isdir(subpath):
           available.extend([(sub,sub)])
	   available.extend(allsubdirectories(user, sub, "|-"))
    form.location.choices = available

    types = [("None","Other"), ("mkdir","Directory")]
    languages = Language.query.all()
    for lang in languages:
	types.extend([(lang.filetype,"." + lang.filetype)])
    form.type.choices = types

    if form.validate_on_submit():
	userlocation = form.location.data	     
	locationpath = settings.WORKING_DIR + user.nickname + "/" + userlocation
	if os.path.isdir(locationpath):
		filepath = locationpath + "/" + form.filename.data
		if form.type.data == "mkdir":
		    if not os.path.isdir(filepath):
			p1 = subprocess.Popen(["sudo", "mkdir", filepath])
                	p1.wait()    
		else:
		    if not form.type.data == "None":
		    	filepath = filepath + "." + form.type.data
        	    if not os.path.isfile(filepath):
            	    	open(filepath, 'a').close()
		    	repository = userlocation.split("/")[0]
            	    	myrepo = user.repos.filter_by(repourl= "/" + repository + "/" ).first()
			filename = form.filename.data
            	    	if not form.type.data == "None":
				filename = form.filename.data + "." + form.type.data
			f = File(filename=filename, path=userlocation, type="txt", repo=myrepo)
			
			flash("Created file " + filename + " in " + userlocation, 'info')
            	    	db.session.add(f)
            	    	db.session.commit()


    cleanprocess()
    return form

def sharesetup(user):
    form = ShareForm()
    if form.validate_on_submit():
    	shareuser = form.user.data
	if shareuser != user.nickname:
    	    sharepath = settings.WORKING_DIR + shareuser
	    shareuserdb = User.query.filter_by(nickname=shareuser).first()
    	    sharedname = user.nickname + "Repo"
    
    	    currentRepo = shareuserdb.repos.filter_by(repourl="/" + sharedname + "/").first()
    	    if currentRepo is None:
	    	existing = False
    	    	for sub in os.listdir(sharepath):
	            if sub == sharedname:
	    	    	existing = True
    	    	if not existing:
	    	    repo = Repo(settings.REMOTE_DIR + user.nickname)
	    	    os.system("sudo mkdir " + sharepath + "/" + sharedname)
		    working_repo = repo.clone(sharepath + "/" + sharedname , False, False, "origin")
            	    p = subprocess.Popen(["sudo", "git", "remote", "add", "origin", "file:///" + settings.REMOTE_DIR + user.nickname + "/"], cwd=sharepath + "/" + sharedname)
	    	    p.wait()
	    	newrepo = Rpstry(repourl="/" + sharedname + "/", owner=shareuserdb)
            	db.session.add(newrepo)
            	db.session.commit()

	    	password = ''
	    	searchfile = open(settings.REMOTE_DIR + shareuser + "/.htpasswd", "r")
	    	for line in searchfile:
		    exactuser = re.compile("^" + shareuser + ":(.)*$")
                    if exactuser.match(line):
   	            	password = line
	        searchfile.close()
                open(settings.REMOTE_DIR + user.nickname + "/.htpasswd", 'a').writelines(password)
                flash("Shared with: " + shareuser, 'info')
	    else:
	    	searchfile = open(settings.REMOTE_DIR + user.nickname + "/.htpasswd", "r")
	    	lines = searchfile.readlines()
	    	searchfile.close()
	    	f = open(settings.REMOTE_DIR + user.nickname + "/.htpasswd","w")
	    	for line in lines:
		    flash(line)
		    exactuser = re.compile("^" + shareuser + ":(.)*$")
		    if not exactuser.match(line):
                    	#password = line
	            	flash("in")
		    	f.write(line)
	        f.close()
		flash(currentRepo.repourl)
	        db.session.delete(currentRepo)
	        db.session.commit()
		flash("Unshared with: " + shareuser, 'info')
    return form


def commitsetup(user):
    form = CommitForm()
    repos = []
    for rpstry in user.repos.all():
	reponame = rpstry.repourl
	displayname = reponame.replace("/",'')
	repos.extend([(reponame,displayname)])
    form.repos.choices = repos
    if form.validate_on_submit():
	if request.form.get('bar', None) == 'Commit':
            repo = form.repos.data
    	    p1 = subprocess.Popen(["sudo", "git", "add", "-A"], cwd=settings.WORKING_DIR + user.nickname + repo)
    	    p1.wait()
    	    working_repo = Repo(settings.WORKING_DIR + user.nickname + repo)
    	    working_repo.do_commit("Test commit", committer=user.nickname + "<" + user.email + ">")
	    displayname = repo.replace("/",'')
	    flash("Commiting to \"" + displayname + "\"", 'info')
    return form

def pullsetup(user):
    form = PullForm()
    repos = []
    for rpstry in user.repos.all():
        reponame = rpstry.repourl
        displayname = reponame.replace("/",'')
        repos.extend([(reponame,displayname)])
    form.repos.choices = repos
    if form.validate_on_submit():
	if request.form.get('bar', None) == 'Pull':
	    repo = form.repos.data
	    p1 = subprocess.Popen(["sudo", "git", "pull", "origin", "master"], cwd=settings.WORKING_DIR + user.nickname + repo)
	    p1.wait()
    	    displayname = repo.replace("/",'')
	    flash("Pulling from \"" + displayname + "\"", 'info')
    return form

def pushsetup(user):
    form = PushForm()
    repos = []
    for rpstry in user.repos.all():
        reponame = rpstry.repourl
        displayname = reponame.replace("/",'')
        repos.extend([(reponame,displayname)])
    form.repos.choices = repos
    if form.validate_on_submit():
        if request.form.get('bar', None) == 'Push':
	    repo = form.repos.data
	    p1 = subprocess.Popen(["sudo", "git", "push", "origin", "master"], cwd=settings.WORKING_DIR + user.nickname + repo)
            p1.wait()
	    displayname = repo.replace("/",'')
	    flash("Pushing to \"" + displayname + "\"", 'info')
    return form



def cleanprocess():
    global process
    current = datetime.datetime.now()
    for gen in process:
	temptime = current - gen.access
	if temptime.seconds > 10:
	    gen.proc.terminate()
	    process.remove(gen)


def getrepos(user, activerepo):
    repos = []
    for rpstry in user.repos.all():
	reponame = rpstry.repourl.replace("/",'')
	if reponame == activerepo:
	    repos.extend( [
                {
                    'reponame': reponame,
                    'active': True
                }])
	else:
	    repos.extend( [
                {
                    'reponame': reponame,
                    'active': False
                }])
    return repos


@app.route('/index/', methods = ['GET', 'POST'])
@app.route('/index/<activerepo>', methods = ['GET', 'POST'])
@login_required
def index(activerepo=None):
    user = g.user
    form = menusetup(user)
    dirs = getfolders(user)
    shareform = sharesetup(user)
    commitform = commitsetup(user)
    pushform = pushsetup(user)
    pullform = pullsetup(user)
    if activerepo is None:
	activerepo = "myRepo"
	
    dbfiles = user.repos.filter_by(repourl="/"+activerepo+"/").first().files    
    files = []

    if request.method == 'POST':
	    value = request.form.get('remove', None)
            if value is not None:
        	name = os.path.split(value)[1]
        	tail = os.path.split(value)[0]
		f = File.query.filter_by(filename=name, path=tail).first()
		if f is not None:
                	db.session.delete(f)
                	db.session.commit()

    for file in dbfiles:
	name = file.filename
	path = file.path
	filepath = settings.WORKING_DIR + user.nickname + "/" + path + "/" + name
	if os.path.isfile(filepath):
	    syntax = "javascript"
	    templist = name.split('.')
            if len(templist) > 1:
                type = templist[len(templist) - 1]
                lang = Language.query.filter_by(filetype=type).first()
                if lang is not None:
		    syntax = lang.syntax
	    file = open(filepath, 'r')
	    text = file.read()
	    if "/" in path:
		repository = path.split("/")[0]
            	relative = path.replace(repository + "/",'')
	    	files.extend( [
            	{ 
            	    'filename': relative + "/" + name ,
		    'filepath': path + "/" + name, 
            	    'content': text,
		    'syntax': syntax 
            	}])
	    else:
		files.extend( [
                {
                    'filename': name ,
                    'filepath': path + "/" + name,
                    'content': text,
                    'syntax': syntax
                }])
	else:
	    db.session.delete(file)
	    db.session.commit()

    if not files:
        flash("You currently have no files in your favourites section. Create new files or favourite exsting files to view them here.", 'info')
	

	
    return render_template("index.html",
        title = 'Home',
        user = user,
	form = form,
   	shareform = shareform,
	commitform = commitform,
	pushform = pushform,
	pullform = pullform,
	dirs =  dirs,
	files = files,
	repos = getrepos(user, activerepo),
	heading = 'Favourites')


@app.route('/edit/<path:filepath>', methods = ['GET', 'POST'])
@login_required
def edit(filepath):
    user = g.user
    form =  menusetup(user)
    dirs = getfolders(user)
    shareform = sharesetup(user)
    commitform = commitsetup(user)
    pushform = pushsetup(user)
    pullform = pullsetup(user)

    path = settings.WORKING_DIR + user.nickname + "/" + filepath	
    

    if  os.path.isfile(path):
	name = os.path.split(path)[1]
	tail = os.path.split(path)[0]
	output = ""

	if request.method == 'POST':
	    if request.form.get('btn', None) == 'Save':
		open(path, 'w').write(request.form['newcontent'])
		templist = name.split('.')
		if len(templist) > 1:
                    type = templist[len(templist) - 1]
                    lang = Language.query.filter_by(filetype=type).first()
                    if lang is not None:
			if lang.interpreted:
			    binary = path.replace('local','bin')
			    command = "cp " + path + " " + binary  
			    args = command.split()
			    p = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                            p.wait()
	    if request.form.get('btn', None) == 'Delete':
                f = File.query.filter_by(filename=name).first()
		if f is not None:
			db.session.delete(f)
			db.session.commit()
		os.system("sudo rm " + path)
		return redirect(url_for('index'))
	    if request.form.get('btn', None) == 'Compile':
		open(path, 'w').write(request.form['newcontent'])
		templist = name.split('.')
		if len(templist) > 1:
		    type = templist[len(templist) - 1]
		    lang = Language.query.filter_by(filetype=type).first()
       	 	    if lang is not None:
			args = lang.compile.split()
			args.append(path)
			binary = tail.replace('local','bin')
			if not os.path.isdir(binary):
			    os.makedirs(binary)
			if lang.file:
			    binary = binary + "/" + templist[0]
			args.append(lang.location)
			args.append(binary)
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
			if text:
			    flash("Compilation Failed", 'error')
			else:
			    flash("Compilation Succeeded", 'success')


	syntax = "javascript"
        templist = name.split('.')
        if len(templist) > 1:
            type = templist[len(templist) - 1]
            lang = Language.query.filter_by(filetype=type).first()
            if lang is not None:
                syntax = lang.syntax

	existing = user.errors.filter_by(path=tail,filename=name).first()
	if existing is not None:
	    output = existing.message
	interpreted = True
	templist = name.split('.')
        if len(templist) > 1:
            type = templist[len(templist) - 1]
            lang = Language.query.filter_by(filetype=type).first()
            if lang is not None:
		if lang.interpreted == False:
		    interpreted = False  
        text = open(path, 'r').read()
	file = {
            'filename': name ,
	    'filepath': filepath,
            'content': text,
	    'syntax': syntax,
	    'interpreted': interpreted
        }
    	return render_template("edit.html",
            title = 'Edit',
            user = user,
            form = form,
	    shareform = shareform,
            commitform = commitform,
            pushform = pushform,
            pullform = pullform,
	    file = file,
	    dirs = dirs,
	    output = output,
	    heading = filepath)

    abort(404)


def inner(proc):
    	flags = fcntl(proc.stdout, F_GETFL)
        fcntl(proc.stdout, F_SETFL, flags | O_NONBLOCK)
        #yield 'Error: \n'
        while True:
	    #time.sleep(1)
	    try:
        	yield read(proc.stdout.fileno(), 1024),
    	    except OSError:
        # the os throws an exception if there is no data
            	yield None
            	#break
	#for line in iter(process.stdout.readline,''):
            #time.sleep(5)
            #if line != '':
                #yield line

@app.route('/run/<path:filepath>', methods = ['GET', 'POST'])
@login_required
def run(filepath):
    global process
    user = g.user
    name = os.path.split(filepath)[1]
    tail = os.path.split(filepath)[0]
    templist = name.split('.')

    path = settings.WORKING_DIR + user.nickname + "/" + filepath

    if  os.path.isfile(path): 
        if len(templist) > 1:
            filetype = templist[len(templist) - 1]
            lang = Language.query.filter_by(filetype=filetype).first()
    	    if lang is not None:
    		location = settings.WORKING_DIR + user.nickname + "/" + tail
    		text = lang.run + name
		if not lang.includetype:
		    text = lang.run + templist[0]
    #text = "java runTest"
    #text = "javac "+ settings.WORKING_DIR + user.nickname + "/myRepo/hats.java"
    		location = location.replace('local','bin')
    		args = text.split()
		p = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, stdin=subprocess.PIPE, cwd=location)
		time = datetime.datetime.now()
    		id = 1
    		unique = False
    		fullid = fullid = "" + g.user.nickname + str(id)
    		while not unique:
		    unique = True
    		    for gen in process:
            		if gen.name == fullid:
			    id = id + 1
	    		    fullid = "" + g.user.nickname + str(id)
			    unique = False
    		fullid = str(fullid)
    		procobj = type(fullid, (object,), {'name' : fullid,  'out': inner(p), 'proc': p, 'access': time})
    		process.append(procobj)
    #process = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, stdin=subprocess.PIPE)
    #input = "test input"

    #def inner():
    #return Response(inner(), mimetype='text/html')
	#yield 'Error: \n'
	    #if line == '' and child.poll() != None:
		#break
	    #if not input == None:
             #   yield input + '<br/>\n'
	#for line in iter(process.stdout.readline,''):
            #time.sleep(5)
	    #if not input == None:
		#yield input
		#input = None      
	    #if line != '':                 
            	#yield line
	    #time.sleep(1)
	#yield 'first part'
	#yield 'second part'
	#yield p.stdout.readline
        return render_template('run.html', title='Run', heading=name, processid=fullid)
    abort(404)
    #return Response(stream_template('run.html', title='Run'))

@app.route('/kill_process/<processid>', methods = ['GET'])
@login_required
def killProcess(processid):
        global process
	try:
            for gen in process:
                if gen.name == processid:
		    gen.proc.terminate()
		    process.remove(gen)
        except StopIteration:
	    pass

@app.route('/get_input/<processid>', methods = ['GET'])
@login_required
def inputrefresh(processid):
        global process
	newInput = "test"
	newInput = request.args.get('message', '')
	try:
            for gen in process:
                if gen.name == processid:
		    gen.proc.stdin.write(newInput + "\n")
		    return jsonify(result="Refresh")
        except StopIteration:
	    pass

@app.route('/get_output/<processid>', methods = ['GET'])
@login_required
def outputrefresh(processid):
        global process
        try:
	    for gen in process:
		if gen.name == processid:
		    gen.access = datetime.datetime.now()
		    line = next(gen.out)
	    	    if line is not None:
		  	return jsonify(result=line)
       	    return None
	except StopIteration:
	    return None


@app.route('/', methods = ['GET', 'POST'])
@app.route('/login/', methods = ['GET', 'POST'])
def login():
    if g.user is not None and g.user.is_authenticated():
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
	login_user(form.user, form.remember_me.data)
        return redirect(request.args.get('next') or url_for('index'))
    return render_template('login.html', 
        title = 'Sign In',
        form = form)

@app.route('/logout/')
def logout():
    logout_user()
    return redirect(url_for('login'))


def get_serializer(secret_key=None):
    if secret_key is None:
        secret_key = app.secret_key
    return URLSafeSerializer(secret_key)


@app.route('/activate/<payload>')
def activate_user(payload):
    s = get_serializer()
    try:
        code = s.loads(payload)
    except BadSignature:
        abort(404)

    user = User.query.get_or_404(code)
    user.active = True
    db.session.commit()
    flash('User activated')
    return redirect(url_for('login'))



@app.route('/create/', methods = ['GET', 'POST'])
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
	s = get_serializer()
    	payload = s.dumps(user.id)
    	url = url_for('activate_user', payload=payload, _external=True)	
	msg = Message('Confirm Email Address', sender = ADMINS[0], recipients = [user.email])
	msg.body = "Follow this link to activate account: " + url
	mail.send(msg)
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
    shareform = sharesetup(user)
    commitform = commitsetup(user)
    pushform = pushsetup(user)
    pullform = pullsetup(user)

    files = []


    if request.method == 'POST':
            value = request.form.get('add', None)
            if value is not None:
                name = os.path.split(value)[1]
                tail = os.path.split(value)[0]
		repository = tail.split("/")[0]
                myrepo = user.repos.filter_by(repourl= "/" + repository + "/" ).first()
                f = File(filename=name, path=tail, type="txt", repo=myrepo)
                if f is not None:
		    db.session.add(f)
		    db.session.commit()


    folderpath = settings.WORKING_DIR + user.nickname + "/" + filepath
    if os.path.isdir(folderpath):
    	for sub in os.listdir(folderpath):
	    fullpath = folderpath + "/" + sub
            if not os.path.isdir(fullpath):
	    	name = sub
		syntax = "javascript"
        	templist = name.split('.')
        	if len(templist) > 1:
            	    type = templist[len(templist) - 1]
            	    lang = Language.query.filter_by(filetype=type).first()
            	    if lang is not None:
                	syntax = lang.syntax
            	text = open(fullpath, 'r').read()
            	files.extend( [
            	{
            	    'filename': name ,
		    'filepath': filepath + "/" + name,
            	    'content': text,
		    'syntax': syntax
           	 }])


    	return render_template("view.html",
            title = 'View',
            user = user,
            form = form,
	    shareform = shareform,
	    commitform = commitform,
	    pushform = pushform,
	    pullform = pullform,
            dirs =  dirs,
            files = files,
	    heading = filepath)

    abort(404)
    #return redirect(url_for('index'))

@app.route('/passwordchange/', methods = ['GET', 'POST'])
@login_required
def changepass():
    user = g.user
    form = ChangeForm()
    if form.validate_on_submit():
	user.password=sha512_crypt.encrypt(form.password.data)

	password = crypt.crypt(form.password.data,salt())
	repos = user.repos

        userrepo = user.nickname
        searchfile = open(settings.REMOTE_DIR + userrepo + "/.htpasswd", "r")
        lines = searchfile.readlines()
        searchfile.close()
        f = open(settings.REMOTE_DIR + userrepo + "/.htpasswd","w")
        for line in lines:
            exactuser = re.compile("^" + user.nickname + ":(.)*$")
            if not exactuser.match(line):
                f.write(line)
        f.close()

        open(settings.REMOTE_DIR + userrepo + "/.htpasswd", 'a').writelines(user.nickname + ":" + password + "\n")

	for repo in repos:
	    userrepo = re.search('/(.+)Repo/', repo.repourl).group(1)
	    if userrepo != 'my':
	    	searchfile = open(settings.REMOTE_DIR + userrepo + "/.htpasswd", "r")
            	lines = searchfile.readlines()
            	searchfile.close()
            	f = open(settings.REMOTE_DIR + userrepo + "/.htpasswd","w")
            	for line in lines:
                    exactuser = re.compile("^" + user.nickname + ":(.)*$")
                    if not exactuser.match(line):
                    	f.write(line)
                f.close()

	        open(settings.REMOTE_DIR + userrepo + "/.htpasswd", 'a').writelines(user.nickname + ":" + password + "\n")

        db.session.commit()
	return redirect(url_for('index'))
    return render_template('changePassword.html',
        title = 'Change Password',
        form = form)




@app.route('/forgot/', methods = ['GET', 'POST'])
def forgot():
    form = ForgotForm()
    if form.validate_on_submit():
	user = form.user
        s = get_serializer(form.temppassword.data)
        payload = s.dumps(user.id)
        url = url_for('forgotchange', payload=payload, _external=True)
        msg = Message('Password Reset', sender = ADMINS[0], recipients = [user.email])
        msg.body = "Follow this link to reset password: " + url
        mail.send(msg)
        flash('Password Reset Email Sent')
        return redirect(url_for('login'))
    return render_template('forgot.html',
        title = 'Forgot Password',
        form = form)



@app.route('/forgotChange/<payload>', methods = ['GET', 'POST'])
def forgotchange(payload):
    form = ForgotResetForm()
    if form.validate_on_submit():

	s = get_serializer(form.temppassword.data)
    	try:
            code = s.loads(payload)
    	except BadSignature:
            abort(404)

    	user = User.query.get_or_404(code)
	user.password=sha512_crypt.encrypt(form.password.data)

        password = crypt.crypt(form.password.data,salt())
        repos = user.repos

        userrepo = user.nickname
        searchfile = open(settings.REMOTE_DIR + userrepo + "/.htpasswd", "r")
        lines = searchfile.readlines()
        searchfile.close()
        f = open(settings.REMOTE_DIR + userrepo + "/.htpasswd","w")
        for line in lines:
            exactuser = re.compile("^" + user.nickname + ":(.)*$")
            if not exactuser.match(line):
                f.write(line)
        f.close()

        open(settings.REMOTE_DIR + userrepo + "/.htpasswd", 'a').writelines(user.nickname + ":" + password + "\n")

        for repo in repos:
            userrepo = re.search('/(.+)Repo/', repo.repourl).group(1)
            if userrepo != 'my':
                searchfile = open(settings.REMOTE_DIR + userrepo + "/.htpasswd", "r")
                lines = searchfile.readlines()
                searchfile.close()
                f = open(settings.REMOTE_DIR + userrepo + "/.htpasswd","w")
                for line in lines:
                    exactuser = re.compile("^" + user.nickname + ":(.)*$")
                    if not exactuser.match(line):
                        f.write(line)
                f.close()

                open(settings.REMOTE_DIR + userrepo + "/.htpasswd", 'a').writelines(user.nickname + ":" + password + "\n")

        db.session.commit()
	flash('Password Updated')
        return redirect(url_for('login'))
    return render_template('forgotPassword.html',
        title = 'Update Password',
        form = form)

