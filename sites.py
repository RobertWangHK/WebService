from flask import *
import time
from datetime import datetime
from random import randint
import os
import MySQLdb as mdb
import sys
import requests
import random
from datetime import datetime
import redis
import json
from celery import Celery

from utils import *
from werkzeug import secure_filename
import shutil
import sched
import time
import sendgrid
from sendgrid.helpers.mail import *
from threading import Thread

application = Flask(__name__, static_folder='templates')
application.secret_key = "random_key"

application.config['CELERY_BROKER_URL'] = 'amqp://guest@localhost'
application.config['CELERY_RESULT_BACKEND'] = 'redis://localhost:6379'

celery = Celery(application.name, broker=application.config['CELERY_BROKER_URL'])
celery.conf.update(application.config)

@celery.task
def send_email(address, message):
    sg = sendgrid.SendGridAPIClient(apikey="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")
    from_email = Email("robert93inhk@gmail.com")
    subject = "IERG 4080 Project!"
    to_email = Email(address)
    #content = Content("text/plain", "resize_image_url: " + resize_url + "\n" + "nailed_image_url: " + nail_url)
    #test_message = """<p>Hi! %s <br>How are you?<br>Here is the <a href="http://54.254.200.117:5000/login-register.html">link</a> you wanted.</p>""" % username
    content = Content("text/html", message)
    mail = Mail(from_email, subject, to_email, content)
    response = sg.client.mail.send.post(request_body=mail.get())
    print(response.status_code)
    print(response.body)
    print(response.headers)
    return


@application.route('/<path:filename>')  
def send_file(filename, *kwargs):
    r = redis.Redis(host='localhost',port=6379,db=0)
    new_results = []
    if filename == "home.html":
	if "username" not in session:
	    return render_template("login-register.html")
	username = session["username"]
	cache_home_key = "%s_home" % username
	if r.exists(cache_home_key) == 1:
	    #print "haha"
	    return r.get(cache_home_key)
	try:
            con = mdb.connect('localhost', 'root', 'root', 'ierg4080')
    	    cur = con.cursor()
    	    sql = """select * from %s order by id desc""" % username 
	    cur.execute(sql)
            #con.commit()
	    results = cur.fetchall()
	    for i in range(len(results)):
		lst = list(results[i])
		lst[4] = lst[4].strftime('%Y-%m-%d %H:%M:%S')
		new_results.append(lst)
        except mdb.Error, e:
    	    print "Error %d: %s" % (e.args[0],e.args[1])
    	    sys.exit(1)
        finally:       
            if con:    
                con.close()
	new_homepage = render_template(filename, name = username, list = new_results)
	r.set(cache_home_key, new_homepage)
	return new_homepage
    elif filename == "submit-image.html":
	username = session["username"]
	return render_template(filename, name = username)
    elif filename == "profile.html":
	username = session["username"]
	r = redis.Redis(host='localhost',port=6379,db=0)
	cache_profile_key = "%s_profile" % username
	if r.exists(cache_profile_key) == 1:
	    #print "haha"
	    return r.get(cache_profile_key)
	try:
            con = mdb.connect('localhost', 'root', 'root', 'ierg4080')
    	    cur = con.cursor()
    	    sql = """select * from %s order by id desc""" % username 
	    cur.execute(sql)
            #con.commit()
	    results = cur.fetchall()
	    for i in range(len(results)):
		lst = list(results[i])
		lst[4] = lst[4].strftime('%Y-%m-%d %H:%M:%S')
		new_results.append(lst)
        except mdb.Error, e:
    	    print "Error %d: %s" % (e.args[0],e.args[1])
    	    sys.exit(1)
        finally:       
            if con:    
                con.close()
	new_profilepage = render_template(filename, name = username, list = new_results)
	r.set(cache_profile_key, new_profilepage)
	return new_profilepage
    return render_template(filename)

@application.route('/search', methods = ['POST'])  
def search_image(): 
    new_results = []
    keyword = request.form['search_term']
    username = session["username"]
    r = redis.Redis(host='localhost',port=6379,db=0)
    cache_search_key = "%s_search_%s" % (session["username"], keyword)
    if r.exists(cache_search_key) == 1:
	temp_search = r.get(cache_search_key)
	new_results = json.loads(temp_search)
	return render_template("home.html", name = username, list = new_results)
    try:
        con = mdb.connect('localhost', 'root', 'root', 'ierg4080')
    	cur = con.cursor()
    	sql = """select * from %s where title like '%%%s%%' order by id """ % (username, keyword) 
	cur.execute(sql)
        #con.commit()
	results = cur.fetchall()
	for i in range(len(results)):
	    lst = list(results[i])
	    lst[4] = lst[4].strftime('%Y-%m-%d %H:%M:%S')
	    new_results.append(lst)
    except mdb.Error, e:
    	print "Error %d: %s" % (e.args[0],e.args[1])
    	sys.exit(1)
    finally:       
        if con:    
            con.close()
    r.set(cache_search_key, json.dumps(new_results))
    return render_template("home.html", name = username, list = new_results)
    
@application.route('/image/<path:filename>')
def send_image(filename): 
    return send_from_directory(application.static_folder, filename)

# load the edit image page with pre-filled title and content fields. 
@application.route('/load_edit_page', methods = ['GET'])  
def load_edit_page(**kwargs):
    title = request.args.get('title')
    content = request.args.get('content')
    path = request.args.get('path')
    username = session["username"]
    return render_template("edit-image.html", name = username, title = title, content = content, path = path, **kwargs)

# delete image information 
@application.route('/delete', methods = ['GET'])  
def delete_image(**kwargs):
    path = request.args.get('path')
    username = session["username"]
    try:
        con = mdb.connect('localhost', 'root', 'root', 'ierg4080')
    	cur = con.cursor()
    	sql = """ DELETE FROM %s WHERE path= '%s' """ % (session["username"], path)
	cur.execute(sql)
        con.commit()  
    except mdb.Error, e:
    	print "Error %d: %s" % (e.args[0],e.args[1])
    	sys.exit(1)
    finally:       
        if con:    
            con.close()
    #send email on demand
    test_message = """<p>Hi! %s <br>You have deleted an image<br>Here is the <a href="http://54.254.200.117/home.html">link</a> Click to see</p>""" % session["username"]
    email = fetch_email(session["username"])
    send_email.delay(email, test_message)
    #send_email(email, test_message)
    #update redis cache resutls
    r = redis.Redis(host='localhost',port=6379,db=0)
    cache_home_key = "%s_home" % session["username"]
    cache_profile_key = "%s_profile" % session["username"]
    r.delete(cache_home_key)
    r.delete(cache_profile_key)
    return redirect(url_for('send_file', filename= "home.html"))


# edit image information 
@application.route('/edit', methods = ['POST'])
def edit_image(**kwargs):
    title = request.form['title']
    content = request.form['content']
    path = request.form['path']
    username = session["username"]
    try:
        con = mdb.connect('localhost', 'root', 'root', 'ierg4080')
    	cur = con.cursor()
    	sql = """ UPDATE %s SET title= '%s', content= '%s' WHERE path = '%s' """ % (session["username"], title, content, path)
	cur.execute(sql)
        con.commit()  
    except mdb.Error, e:
    	print "Error %d: %s" % (e.args[0],e.args[1])
    	sys.exit(1)
    finally:       
        if con:    
            con.close()
    #send email on demand
    test_message = """<p>Hi! %s <br>You have editted an image<br>Here is the <a href="http://54.254.200.117/home.html">link</a> Click to see</p>""" % session["username"]
    email = fetch_email(session["username"])
    send_email.delay(email, test_message)
    #update redis cache resutls
    r = redis.Redis(host='localhost',port=6379,db=0)
    cache_home_key = "%s_home" % session["username"]
    cache_profile_key = "%s_profile" % session["username"]
    r.delete(cache_home_key)
    r.delete(cache_profile_key)
    return redirect(url_for('send_file', filename= "home.html"))

# submit new image file 
@application.route('/upload', methods = ['POST'])  
def upload_image(**kwargs):
    title = request.form['title']
    content = request.form['content']
    f = request.files['upload']
    upload_path = "/home/ubuntu/project/templates/user/"+session["username"]+"/upload-image"
    #f.save(secure_filename(f.filename))
    random_num = random_with_N_digits(5)
    dateTime = datetime.utcnow()
    Format_Time = dateTime.strftime('%Y-%m-%d %H:%M:%S')
    image_name = Format_Time + "-" + str(random_num) + ".jpg"
    f.save(os.path.join(upload_path, image_name))
    #store user upload history into database
    #/image/user/test/upload-image/2016-12-16 05:39:51-91818.jpg
    try:
        con = mdb.connect('localhost', 'root', 'root', 'ierg4080')
    	cur = con.cursor()
    	sql = """INSERT INTO %s (path, title, content, submited_at)
	VALUES ('%s', '%s', '%s', '%s')""" % (session["username"], "/image/user/" + session["username"] + "/upload-image/" + image_name, title, content, Format_Time)
	cur.execute(sql)
        con.commit()  
    except mdb.Error, e:
    	print "Error %d: %s" % (e.args[0],e.args[1])
    	sys.exit(1)
    finally:       
        if con:    
            con.close()
    #send email on demand
    test_message = """<p>Hi! %s <br>You have uploaded a new image<br>Here is the <a href="http://54.254.200.117/home.html">link</a> Click to see</p>""" % session["username"]
    email = fetch_email(session["username"])
    send_email.delay(email, test_message)
    #update redis cache resutls
    r = redis.Redis(host='localhost',port=6379,db=0)
    cache_home_key = "%s_home" % session["username"]
    cache_profile_key = "%s_profile" % session["username"]
    r.delete(cache_home_key)
    r.delete(cache_profile_key)
    return redirect(url_for('send_file', filename= "home.html"))

@application.route('/login', methods = ['POST'])  
def login():
    user = request.form['username']
    password = request.form['password']
    #not exist, error, correct
    result = check_user(user, password)
    if result == "not exist":
	return redirect(url_for('send_file', filename= "login-register.html"))
    elif result == "error":
	return redirect(url_for('send_file', filename= "login-register.html"))
    else:
	session["username"] = user
	#thread = Thread(target = periodic_email, args = (email, session["username"]))
        #thread.start()
	return redirect(url_for('send_file', filename= "home.html"))

@application.route('/register', methods = ['POST'])  
def register():
    user = request.form['username']
    password = request.form['password']
    email = request.form['email']
    #already exist, success
    result = register_user(user, password, email)
    if result == "already exist":
	return redirect(url_for('send_file', filename= "login-register.html"))
    else:
	session["username"] = user
	#create specific folders for that user
	user_path = "/home/ubuntu/project/templates/user/"+session["username"]
	if not os.path.isdir(user_path):
   	    os.makedirs(user_path)
	    os.makedirs(user_path + "/profile-image")
	    os.makedirs(user_path + "/upload-image")
	    shutil.copy2('/home/ubuntu/project/templates/default_profile.jpg', user_path + '/profile-image/default_profile.jpg')
	try:
            con = mdb.connect('localhost', 'root', 'root', 'ierg4080')
    	    cur = con.cursor()
    	    sql = """CREATE TABLE %s (
    		id INT(4) UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    		path VARCHAR(128) NOT NULL,
    		title VARCHAR(128) DEFAULT '',
    		content VARCHAR(512) DEFAULT '',
    		submited_at DATETIME,
    		UNIQUE (path)
		)""" % (session["username"])
	    cur.execute(sql)
            con.commit()  
        except mdb.Error, e:
    	    print "Error %d: %s" % (e.args[0],e.args[1])
    	    sys.exit(1)
        finally:       
            if con:    
                con.close()
	return redirect(url_for('send_file', filename= "home.html"))

@application.route('/logout')  
def logout():
    session.pop('username', None)
    return redirect(url_for('send_file', filename= "login-register.html"))

@application.route('/refresh')  
def refresh():
    username = session['username']
    return redirect(url_for('send_file', filename= "home.html"))

if __name__ == "__main__":
    application.run(host='0.0.0.0')
