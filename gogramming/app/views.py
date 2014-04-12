from flask import render_template, flash, redirect, session, url_for, request, g, make_response, jsonify, Response, abort
from flask.ext.login import login_user, logout_user, current_user, login_required
from app import app, db, lm, mail
from forms import LoginForm, CreateForm, AddForm, ShareForm, CommitForm, PushForm, PullForm, ChangeForm, ForgotUserForm, ForgotForm, ForgotResetForm, CopyForm, CompileForm
from models import User, Rpstry, File, Language, Error, ROLE_USER, ROLE_ADMIN
import os
import crypt
import subprocess
from fcntl import fcntl, F_GETFL, F_SETFL
from os import O_NONBLOCK, read
import random
import datetime
import settings
from passlib.hash import sha256_crypt
from app import language_loader
import time
from plugins import *
import re
from flask.ext.mail import Message
from config import ADMINS
from itsdangerous import URLSafeSerializer, BadSignature
from dulwich.repo import Repo
from plugins import *
import sys

process = []


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html', title="Page Not Found"), 404

@lm.user_loader
def load_user(id):
    return User.query.get(int(id))

@app.before_request
def before_request():
    g.user = current_user


def classesinmodule(module):
    md = module.__dict__
    return [
        md[c] for c in md if (
            isinstance(md[c], type) and md[c].__module__ == module.__name__ and issubclass(md[c], language.Language)
        )
    ]

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

def allsubdirectories(user, parentpath, prefix, basepath):
    available = []
    path = basepath + "/" + parentpath
    for sub in os.listdir(path):
	subpath = path + "/" + sub
       	if os.path.isdir(subpath) and not sub == ".git":
	    childpath = parentpath + "/" + sub
	    display = prefix + sub
	    available.extend([(childpath,display)])
	    available.extend(allsubdirectories(user, childpath, prefix + "-", basepath))

    return available


def menusetup(user):
    form = AddForm()
    available = []
    localrepopath = settings.WORKING_DIR + user.nickname
    for sub in os.listdir(localrepopath):
	subpath = localrepopath + "/" + sub
        if os.path.isdir(subpath):
           available.extend([(sub,sub)])
	   available.extend(allsubdirectories(user, sub, "|-", localrepopath))
    form.location.choices = available

    types = [("None","Other"), ("mkdir","Directory")]
    languages = Language.query.all()
    for lang in languages:
	types.extend([(lang.filetype,"." + lang.filetype)])
    form.type.choices = types
    
    if request.form.get('bar', None) == 'Add':
        if form.validate_on_submit():
	    userlocation = form.location.data	     
	    locationpath = settings.WORKING_DIR + user.nickname + "/" + userlocation
	    if os.path.isdir(locationpath):
		filepath = locationpath + "/" + form.filename.data
		if form.type.data == "mkdir":
		    if not os.path.isdir(filepath):
			p1 = subprocess.Popen(["sudo", "mkdir", filepath])
                	p1.wait()
			flash('New Directory Created', 'success')
		    else:
		    	flash('Directory already exists', 'error')    
		else:
		    if not form.type.data == "None":
		    	filepath = filepath + "." + form.type.data
        	    if not os.path.exists(filepath):
            	    	open(filepath, 'a').close()
		    	repository = userlocation.split("/")[0]
            	    	myrepo = user.repos.filter_by(repourl= "/" + repository + "/" ).first()
			filename = form.filename.data
            	    	if not form.type.data == "None":
				filename = form.filename.data + "." + form.type.data
			f = File(filename=filename, path=userlocation, type="txt", repo=myrepo)
			
			flash("Created file " + filename + " in " + userlocation, 'success')
            	    	db.session.add(f)
            	    	db.session.commit()
		    else:
			flash('File or directory already exists', 'error')
        else:
	    flash('Name of new file or directory must not have spaces or slashes', 'error')
    cleanprocess()
    return form

def sharesetup(user):
    form = ShareForm()
    if request.form.get('bar', None) == 'Share/Unshare':
    	if form.validate_on_submit():
    	    shareuser = form.shareuser.data
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
		        exactuser = re.compile("^" + shareuser + ":(.)*$")
		        if not exactuser.match(line):
		    	    f.write(line)
	            f.close()
	            db.session.delete(currentRepo)
	            db.session.commit()
		    flash("Unshared with: " + shareuser, 'info')
        else:
	    flash("User does not exist", 'error')
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
	    message = request.form['commitmessage']
    	    if message != "":
	    	p1 = subprocess.Popen(["sudo", "git", "add", "-A"], cwd=settings.WORKING_DIR + user.nickname + repo, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    	    	p1.wait()
	    	author = "--author=\'" + user.nickname + " <" + user.email + ">\'"
	    	p2 = subprocess.Popen(["sudo", "git", "commit", "-m", message, author], cwd=settings.WORKING_DIR + user.nickname + repo, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
	    	p2.wait()
	    	output = p2.stdout.read()
	    	if "nothing to commit" in output:
		    flash("Nothing to commit", 'error')
	    	else:
	    	    displayname = repo.replace("/",'')
	    	    flash("Commiting to \'" + displayname + "\'", 'info')
	    else:
	        flash("Commit message cannot be blank", 'error')
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
	    p1 = subprocess.Popen(["sudo", "git", "pull", "origin", "master"], cwd=settings.WORKING_DIR + user.nickname + repo, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
	    p1.wait()
    	    output = p1.stdout.read()
            if "CONFLICT" in output:
                flash("There are conflicts: Please fix these and commit changes", 'error')
            elif "up-to-date" in output:
		flash("Nothing to pull", 'error')
	    elif "unmerged" in output:
		flash("Must fix conflicts and commit changes before pulling", 'error')
	    else:
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
	    p1 = subprocess.Popen(["sudo", "git", "push", "origin", "master"], cwd=settings.WORKING_DIR + user.nickname + repo, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            p1.wait()
	    output = p1.stdout.read()
            if "[rejected]" in output:
                flash("There are conflicts: Please pull, fix, and commit changes", 'error')
            elif "up-to-date" in output:
                flash("Nothing to push", 'error')
            else:
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

    dbrepo = user.repos.filter_by(repourl="/"+activerepo+"/").first()
    if dbrepo is None:
	abort(404)	
    dbfiles = dbrepo.files    
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

def getFolderHeading(filepath, includeActive):
    heading=[]
    pathsplit = filepath.split("/")
    length = len(pathsplit)
    if includeActive:
        for i in range(0, length):
            foldername = pathsplit[i]
            subpath= foldername
            restpath = ""
            if i is not 0:
                for j in range(0, i):
                    if restpath == "":
                        restpath = pathsplit[j]
                    else:
                        restpath = restpath + "/" + pathsplit[j]
                subpath = restpath + "/" + subpath
            active = False
            if i == length - 1:
                active = True
            heading.append( {
                'foldername': foldername ,
                'folderpath': subpath,
                'active': active
	    } )
    else:
	for i in range(0, length - 1):
            foldername = pathsplit[i]
            subpath= foldername
            restpath = ""
            if i is not 0:
                for j in range(0, i):
                    if restpath == "":
                        restpath = pathsplit[j]
                    else:
                        restpath = restpath + "/" + pathsplit[j]
                subpath = restpath + "/" + subpath
	    heading.append( {
                'foldername': foldername ,
                'folderpath': subpath
            } )
    return heading

@app.route('/help/', methods = ['GET'])
def help():
    user = g.user
    return render_template('help.html', title='Help', user=user.nickname)

def copysetup(user):
    form = CopyForm()

    available = []
    userrepopath = settings.WORKING_DIR + user.nickname
    for sub in os.listdir(userrepopath):
        subpath = userrepopath + "/" + sub
        if os.path.isdir(subpath):
            available.extend([(sub,sub)])
            available.extend(allsubdirectories(user, sub, "|-", userrepopath))
    form.copydirs.choices = available
    return form

@app.route('/edit/<path:filepath>/', methods = ['GET', 'POST'])
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

    name = os.path.split(path)[1]
    tail = os.path.split(path)[0]

    lang = None
    type = None
    plainname = ""
    filelist = name.split('.')
    if len(filelist) > 1:
        type = filelist[len(filelist) - 1]
        lang = Language.query.filter_by(filetype=type).first()
	plainname = filelist[0]
 
    compileform = CompileForm()
    options = []
    currentfilepath = ""
    if lang is not None:
        if lang.additiondir:
	    currentfilepath = os.path.split(tail)[0]
	    sub = os.path.split(tail)[1]
            subpath = currentfilepath + "/" + sub
            if os.path.isdir(subpath):
                options.extend([(sub,sub)])
                options.extend(allsubdirectories(user, sub, "|-", currentfilepath))
        else:
	    currentfilepath = tail
            for sub in os.listdir(currentfilepath):
                subpath = currentfilepath + "/" + sub
	        sublist = sub.split('.')
	        if sublist[len(sublist) - 1] == type and subpath != path:
                    if os.path.isfile(subpath):
                        options.extend([(sub,sub)])

    compileform.options.choices = options

    copyform = copysetup(user)

    if  os.path.isfile(path):
	output = ""

	if request.method == 'POST':
	    if request.form.get('btn', None) == 'Copy':
		newdir = copyform.copydirs.data
		fullnewdir = settings.WORKING_DIR + user.nickname + "/" + newdir
		if os.path.exists(fullnewdir + "/" + name):
		    flash("File cannot be copied, file or folder with same name already exists", 'error')
		else:
		    os.system("sudo cp " + path + " " + fullnewdir)
		    flash(name + " has been copied to " + newdir, 'success')
		return redirect(url_for('edit', filepath = newdir + "/" + name))
	    if request.form.get('btn', None) == 'Move':
		newdir = copyform.copydirs.data
		fullnewdir = settings.WORKING_DIR + user.nickname + "/" + newdir
                if os.path.exists(fullnewdir + "/" + name):
                    flash("File cannot be moved, file or folder with same name already exists", 'error')
                else:
                    os.system("sudo mv " + path + " " + fullnewdir)
	            flash(name + " has been moved to " + newdir, 'success')
		return redirect(url_for('edit', filepath = newdir + "/" + name))
	    if request.form.get('btn', None) == 'Save':
		open(path, 'w').write(request.form['newcontent'])
                if lang is not None:
			if lang.interpreted:
			    binary = path.replace('local','bin', 1)
			    bintail = os.path.split(binary)[0]
			    if not os.path.exists(bintail):
				os.makedirs(bintail)
			    command = "cp " + path + " " + binary  
			    os.system(command)
		else:
			    binary = path.replace('local','bin', 1)
                            bintail = os.path.split(binary)[0]
                            if not os.path.exists(bintail):
                                os.makedirs(bintail)
                            command = "cp " + path + " " + binary
                            os.system(command)
		flash("File has been saved", 'success')
	    if request.form.get('btn', None) == 'Delete':
		deletetail = os.path.split(filepath)[0]
                f = File.query.filter_by(filename=name, path=deletetail).first()
		if f is not None:
			db.session.delete(f)
			db.session.commit()
		os.system("sudo rm " + path)
		flash("File has been deleted", 'success')
		return redirect(url_for('index'))
	    if request.form.get('btn', None) == 'Compile':
		open(path, 'w').write(request.form['newcontent'])
       	 	if lang is not None:
			module = sys.modules[lang.modulename]
        		languages = classesinmodule(module)
			command = None
			selected = compileform.options.data
			additional = []
			if not selected:
			    additonal = None
			else:
			    for option in selected:
				additional.append(currentfilepath + "/" + option)

			location = tail

			file = open(path, "r")
			lines = file.readlines()
			file.close()

			filename = name

			if type == 'java':
                       	    file = open(path, "r")
                    	    javacode = file.read()
                    	    file.close()
                    	    package = re.search('package([\n\t ])*([^;]*);', javacode)
                    	    if package is not None:
				statedpackage = package.group(2)
				if statedpackage == os.path.split(tail)[1]:
				    location = os.path.split(tail)[0]
				    additional.append(location) 
				    filename = os.path.split(tail)[1] + "/" + name
				else:
				    flash("Incorrect package name in file", 'error')
				    return redirect(url_for('edit', filepath=filepath))

			binary = location.replace('local','bin',1)
			if not os.path.isdir(binary):
			    os.makedirs(binary)


			if type == 'c':
			    main = re.compile("(.)*int([\t ])*main(.)*")
			    mainvoid = re.compile("(.)*int([\t ])*main(.)*\(([\t ])*void([\t ])*\)(.)*")
			    mainall = re.compile("(.)*int([\t ])*main(.)*\(([\t ])*void([\t ])*\){(.)*")
			    voidend = re.compile("(.)*\(([\t ])*void([\t ])*\){(.)*")
			    justvoid = re.compile("(.)*\(([\t ])*void([\t ])*\)(.)*")
			    i = 0
			    contents = list(lines)
			    voidfound = False
			    mainfound = False
			    while i < len(lines):
				line = lines[i]
				if voidfound and "{" in line:
				    contents.insert(i + 1, 'setvbuf(stdout, (char *) NULL, _IOLBF, 0);\n')
                                    break
				if mainfound and justvoid.match(line):
                                    voidfound = True
				if mainfound and voidend.match(line):
                                    contents.insert(i + 1, 'setvbuf(stdout, (char *) NULL, _IOLBF, 0);\n')
                                    break
			        if mainall.match(line):
				    contents.insert(i + 1, 'setvbuf(stdout, (char *) NULL, _IOLBF, 0);\n')
				    break
			        elif mainvoid.match(line):
				    voidfound = True
				elif main.match(line):
				    mainfound = True
				i = i + 1		
			
			    f = open(path, "w")
			    contents = "".join(contents)
			    f.write(contents)
			    f.close()


			for language in languages:
			    prog = language()
			    if prog.getType() == type:
				command = prog.getCompile(filename, binary, additional, plainname)
				break
			
			args = command.split()

			if lang.additiondir:
                            if additional is not None:
			    	other = ""
                	    	for line in additional:
                    		    other = other + line + ":"
                            p = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd=location, env={'CLASSPATH': ".:" + other})
			else:
			    p = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd=location) 
			p.wait()

			if type == 'c':
			    f = open(path, "w")
                            lines = "".join(lines)
                            f.write(lines)
                            f.close()

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
			    flash("Compilation Failed: Errors can be viewed below editor", 'error')
			else:
			    flash("Compilation Succeeded", 'success')

            if request.form.get('btn', None) == 'Favourite':
		favtail = os.path.split(filepath)[0]
                repository = favtail.split("/")[0]
                myrepo = user.repos.filter_by(repourl= "/" + repository + "/" ).first()
                f = File(filename=name, path=favtail, type="txt", repo=myrepo)
		current = myrepo.files.filter_by(filename=name, path=favtail).first()
                if f is not None and current is None:
                    db.session.add(f)
                    db.session.commit()


	syntax = "javascript"
        if lang is not None:
                syntax = lang.syntax

	existing = user.errors.filter_by(path=tail,filename=name).first()
	if existing is not None:
	    output = existing.message
	interpreted = True
        if lang is not None:
		if lang.interpreted == False:
		    interpreted = False  
	lines = open(path, 'r').readlines()
	mergeline = re.compile("^<<<<<<< HEAD")	
	endline = re.compile("^>>>>>>> ([a-zA-Z0-9])*")
	startmerge = False
	merge = False
	for line in lines:
	    if mergeline.match(line):
		startmerge = True
	    if startmerge:
		if endline.match(line):
		    merge = True 
	
	if lang is None:
	    text = open(path, 'r').read()
            file = {
                'filename': name ,
                'filepath': filepath,
                'content': text,
                'syntax': syntax,
                'interpreted': interpreted,
                'merge': False,
                'includedir': True
            }
	elif merge:
	    currenttext = ""
	    repotext = ""
	    currentmerge = True
	    repomerge = True
	    switchline = re.compile("^=======")
	    for line in lines:
		if mergeline.match(line):
		    repomerge = False
		elif switchline.match(line):		    
		    repomerge = True
		    currentmerge = False
		elif endline.match(line):
		    currentmerge = True
		else:
		    if currentmerge:
			currenttext = currenttext + line
		    if repomerge: 
			repotext = repotext + line
            file = {
                'filename': name ,
                'filepath': filepath,
                'content': currenttext,
		'mergecontent': repotext,
                'syntax': syntax,
                'interpreted': interpreted,
                'merge': True,
		'includedir': lang.additiondir
            }
	else:
	    text = open(path, 'r').read()	
	    file = {
            	'filename': name ,
	    	'filepath': filepath,
            	'content': text,
	    	'syntax': syntax,
	    	'interpreted': interpreted,
		'merge': False,
		'includedir': lang.additiondir
            }
	
	heading = getFolderHeading(filepath, True)
	    
    	return render_template("edit.html",
            title = 'Edit',
            user = user,
            form = form,
	    shareform = shareform,
            commitform = commitform,
            pushform = pushform,
            pullform = pullform,
	    copyform = copyform,
	    compileform = compileform,
	    file = file,
	    dirs = dirs,
	    output = output,
	    heading = heading)

    abort(404)


def inner(proc):
    	flags = fcntl(proc.stdout, F_GETFL)
        fcntl(proc.stdout, F_SETFL, flags | O_NONBLOCK)
        while True:
	    try:
        	yield read(proc.stdout.fileno(), 1024)
    	    except OSError:
            	yield None


@app.route('/run/<path:filepath>', methods = ['GET', 'POST'])
@login_required
def run(filepath):
    global process
    user = g.user
    name = os.path.split(filepath)[1]
    tail = os.path.split(filepath)[0]
    templist = name.split('.')
    filename = templist[0]

    path = settings.WORKING_DIR + user.nickname + "/" + filepath

    if  os.path.isfile(path): 
        if len(templist) > 1:
            filetype = templist[len(templist) - 1]
            lang = Language.query.filter_by(filetype=filetype).first()
    	    if lang is not None:
    		location = settings.WORKING_DIR + user.nickname + "/" + tail
		if filetype == 'java':
		    file = open(path, "r")
                    lines = file.read()
                    file.close()
		    package = re.search('package([\n\t ])*([^;]*);', lines)
		    if package is not None:
			filename = package.group(2) + "/" + filename
			location = settings.WORKING_DIR + user.nickname + "/" + os.path.split(tail)[0]
		location = location.replace('local','bin',1)
		if os.path.isdir(location):
		    module = sys.modules[lang.modulename]
                    languages = classesinmodule(module)
                    command = None
                    for lang in languages:
                        prog = lang()
                        if prog.getType() == filetype:
                            command = prog.getRun(filename)
                            break
    		    args = command.split()
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
		else:
		    flash("File could not be found. This may be because it has not yet been compiled" ,'error')
                    return redirect(url_for('edit', filepath=filepath))
    	    else:
		flash("Cannot run as file type not supported" ,'error')
		return redirect(url_for('edit', filepath=filepath))
	else:
	    flash("Cannot run as file type not supported" ,'error')
            return redirect(url_for('edit', filepath=filepath))
        return render_template('run.html', title='Run', heading=name, processid=fullid)
    abort(404)

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
	user = User(nickname=newuser, password=sha256_crypt.encrypt(form.password.data), email=form.email.data, role=ROLE_USER)
	db.session.add(user)
	db.session.commit()
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
	flash("User created and activation email sent")
	return redirect(url_for('login'))
    return render_template('createAccount.html',
        title = 'Create New Account',
        form = form)



@app.route('/view/<path:filepath>/', methods = ['GET', 'POST'])
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

    folderpath = settings.WORKING_DIR + user.nickname + "/" + filepath

    copyform = copysetup(user)

    if request.method == 'POST':
        foldername = os.path.split(filepath)[1]
	if request.form.get('viewbar', None) == 'Copy':
            if "/" in filepath:
                newdir = copyform.copydirs.data
                fullnewdir = settings.WORKING_DIR + user.nickname + "/" + newdir
                if os.path.exists(fullnewdir + "/" + foldername):
                    flash("Folder cannot be copied, folder with same name already exists", 'error')
                elif newdir == filepath:
		    flash("This is the current folder and the folder has therefore not been copied", 'error')
		else:
                    os.system("sudo cp -r " + folderpath + " " + fullnewdir)
                    flash(foldername + " has been copied to " + newdir, 'success')
                    return redirect(url_for('view', filepath = newdir + "/" + foldername))
            else:
                flash("Cannot copy base repository file", 'error')
	if request.form.get('viewbar', None) == 'Move':
	    if "/" in filepath:
                newdir = copyform.copydirs.data
                fullnewdir = settings.WORKING_DIR + user.nickname + "/" + newdir
                if os.path.exists(fullnewdir + "/" + foldername):
                    flash("Folder cannot be moved, folder with same name already exists", 'error')
                elif newdir == filepath:
                    flash("This is the current folder and the folder has therefore not been moved", 'error')
                else:
                    os.system("sudo mv " + folderpath + " " + fullnewdir)
                    flash(foldername + " has been moved to " + newdir, 'success')
                    return redirect(url_for('view', filepath = newdir + "/" + foldername))
            else:
	    	flash("Cannot move base repository file", 'error')
	if request.form.get('viewbar', None) == 'Delete':
            if "/" in filepath:
                os.system("sudo rm -r " + folderpath)
                flash("Folder has been deleted", 'success')
                return redirect(url_for('index'))
            else:
                flash("Cannot delete base repository file", 'error')
	value = request.form.get('add', None)
        if value is not None:
                name = os.path.split(value)[1]
                tail = os.path.split(value)[0]
		repository = tail.split("/")[0]
                myrepo = user.repos.filter_by(repourl= "/" + repository + "/" ).first()
                f = File(filename=name, path=tail, type="txt", repo=myrepo)
                current = myrepo.files.filter_by(filename=name, path=tail).first()
                if f is not None and current is None:
		    db.session.add(f)
		    db.session.commit()


    if os.path.isdir(folderpath):
    	for sub in os.listdir(folderpath):
	    fullpath = folderpath + "/" + sub
            if os.path.isfile(fullpath):
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

	heading = getFolderHeading(filepath, True)
    	return render_template("view.html",
            title = 'View',
            user = user,
            form = form,
	    shareform = shareform,
	    commitform = commitform,
	    pushform = pushform,
	    pullform = pullform,
	    copyform = copyform,
            dirs =  dirs,
            files = files,
	    heading = heading)

    abort(404)


@app.route('/passwordchange/', methods = ['GET', 'POST'])
@login_required
def changepass():
    user = g.user
    form = ChangeForm()
    if form.validate_on_submit():
	user.password=sha256_crypt.encrypt(form.password.data)

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

@app.route('/forgotusername/', methods = ['GET', 'POST'])
def forgotusername():
    form = ForgotUserForm()
    if form.validate_on_submit():
        user = form.user
        msg = Message('Password Reset', sender = ADMINS[0], recipients = [user.email])
        msg.body = "Your username is: " + user.nickname + " (Remember case matters)"
	mail.send(msg)
        flash('Username Email Sent')
        return redirect(url_for('login'))
    return render_template('forgotUsername.html',
        title = 'Forgot Username',
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
	user.password=sha256_crypt.encrypt(form.password.data)

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

