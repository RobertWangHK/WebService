from random import randint
import json

user_dict = {}
user_uploads = {}

def render(url):
    with open(url, "rb") as input:
	a = input.read()
    input.close()
    return a

def check_user(username, password):
    with open("users/user_validation", "rb") as input:
	try:
	    user_dict = json.load(input)
	except:
	    user_dict = {}
    input.close()

    if username not in user_dict:
	return "not exist"
    elif not user_dict[username][0] == password:
	return "error"
    else:
	return "correct" 

def fetch_email(username):
    with open("users/user_validation", "rb") as input:
	user_dict = json.load(input)
    input.close()
    email_address = user_dict[username][1]
    return email_address
	
def register_user(username, password, email):
    with open("users/user_validation", "r+") as input:
	try:
		user_dict = json.load(input)
	except:
		user_dict = {}
	#check if already register
	input.seek(0)
	if username in user_dict:
	    return "already exist"
	user_dict[username] = [None] *2
	user_dict[username][0] = password
	user_dict[username][1] = email
	json.dump(user_dict, input)
    input.close()
    return "success"

def upload_image_to_file(username, title, content, path):
    return "success"    

def random_with_N_digits(n):
    range_start = 10**(n-1)
    range_end = (10**n)-1
    return randint(range_start, range_end)



