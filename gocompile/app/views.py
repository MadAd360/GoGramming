from flask import render_template, flash, redirect, session, url_for, request, g, make_response, jsonify, Response, stream_with_context
from flask.ext.login import login_user, logout_user, current_user, login_required
from app import app, db, lm
from forms import LoginForm, CreateForm, AddForm
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


process = None
testvar = []


def stream_template(template_name, **context):
    app.update_template_context(context)
    t = app.jinja_env.get_template(template_name)
    rv = t.stream(context)
    #rv.enable_buffering(5)
    return rv

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
			f = File(filename=form.filename.data, path=userlocation, type="txt", repo=myrepo)
            	    	if not form.type.data == "None":
				f = File(filename=form.filename.data + "." + form.type.data, path=userlocation, type="txt", repo=myrepo)

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
		#languages = Language.query.all()
		#for lang in languages:
                    #db.session.delete(lang)
		#db.session.commit()
		flash(language_loader.loadLanguages('plugins'))


@app.route('/', methods = ['GET', 'POST'])
@app.route('/index', methods = ['GET', 'POST'])
@login_required
def index():
    user = g.user
    form = menusetup(user)
    dirs = getfolders(user)
	
    dbfiles = user.repos.filter_by().first().files    
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
	    text = open(filepath, 'r').read()
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
			args.append("-d")
			args.append(binary)
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
	    #if request.form.get('btn', None) == 'Run':


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
	#if os.path.exists(errorpath):
	#    errorfile = open(errorpath, 'r+')
	#    output = errorfile.read()
        text = open(path, 'r').read()
	file = {
            'filename': name ,
            'content': text,
	    'syntax': syntax
        }
    	return Response(render_template("edit.html",
            title = 'Edit',
            user = user,
            form = form,
	    file = file,
	    dirs = dirs,
	    output = output))

    return redirect(url_for('index'))

def inner(proc):
    	flags = fcntl(proc.stdout, F_GETFL)
        fcntl(proc.stdout, F_SETFL, flags | O_NONBLOCK)
        #yield 'Error: \n'
        while True:
	    #time.sleep(1)
	    try:
        	yield read(process.stdout.fileno(), 1024),
    	    except OSError:
        # the os throws an exception if there is no data
            	yield ''
            	#break
	#for line in iter(process.stdout.readline,''):
            #time.sleep(5)
            #if line != '':
                #yield line

@app.route('/run', methods = ['GET', 'POST'])
@login_required
def run():
    global process
    global testvar
    testvar = []
    user = g.user
    location = settings.WORKING_DIR + user.nickname + "/myRepo/"
    text = "java runTest"
    #text = "javac "+ settings.WORKING_DIR + user.nickname + "/myRepo/hats.java"
    location = location.replace('local','bin')
    args = text.split()
    process = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, stdin=subprocess.PIPE, cwd=location)
    #process = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, stdin=subprocess.PIPE)
    #input = "test input"

    #process.stdin.write(input)
    #process.stdin.flush()
    def test():
        for i, c in enumerate("hello"*10):
            time.sleep(.1)  # an artificial delay
            yield i, c
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
    #p.communicate(input="testinginput")
    #env = Environment(loader=FileSystemLoader('templates'))
    #tmpl = env.get_template('run.html')    
    #return Response(tmpl.generate(output="test", title='Run'))
    #return Response(inner(), mimetype='text/html')
    #return Response(stream_with_context(output()))
    #g.run = inner(process)
    obj = type('obj', (object,), {'name' : g.user.nickname,  'out': inner(process)})
    testvar.append(obj)
    #testvar = inner(process)
    #session['run'] = inner(process)
    return Response(stream_template('run.html', title='Run'))
    #return Response(stream_template('run.html', output=temp, title='Run'))
    #return Response(stream_template('run.html', title='Run'))
    #return Response(output(), direct_passthrough=True)
    #return Response(output(), mimetype="text/event-stream")	

@app.route('/kill_process', methods = ['GET'])
@login_required
def killProcess():
        global process
        global testvar
	process.terminate()
        #process.stdin.write("testing")
        return jsonify(result="Refresh")

@app.route('/get_input/<path:newInput>', methods = ['GET'])
@login_required
def inputrefresh(newInput):
        global process
        global testvar
        process.stdin.write(newInput + "\n")
	#process.stdin.flush()
        return jsonify(result="Refresh")


@app.route('/get_output', methods = ['GET', 'POST'])
@login_required
def outputrefresh():
        #global process
        global testvar
        #process.stdin.write("testing")
	#temp = list(inner())
	#text = ''.join(temp)
        #return Response(inner(), mimetype='text/html')
        try:
	    for gen in testvar:
		if gen.name == g.user.nickname:
		    line = next(gen.out)
		    if line == '':
			return None
	    	    return jsonify(result=line)
       	    return None
	except StopIteration:
	    return None
	    #return jsonify(result='')

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
            dirs =  dirs,
            files = files)

    return redirect(url_for('index'))
