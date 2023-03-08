from flask import Flask, render_template, request, redirect, url_for, jsonify, session, flash
import pymongo
import pymongo.helpers
from datetime import datetime, timedelta
import string
import random
import os
from dotenv import load_dotenv
import dns.resolver

dns.resolver.default_resolver = dns.resolver.Resolver(configure=False)
dns.resolver.default_resolver.nameservers = ['8.8.8.8']

load_dotenv()
DB_URI = os.environ.get("DB_URI")
DB_NAME = os.environ.get("DB_NAME")
ADMIN_PANEL_USERNAME = os.environ.get("ADMIN_PANEL_USERNAME")
ADMIN_PANEL_PASSWORD = os.environ.get("ADMIN_PANEL_PASSWORD")
client = pymongo.MongoClient(DB_URI)

app = Flask(__name__)
app.secret_key = os.urandom(24)


@app.route('/')
def home():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    db = client[DB_NAME]
    keys_collection = db['keys']
    keys = list(keys_collection.find())

    users_collection = db['users']
    users = list(users_collection.find())

    return render_template('home.html', keys=keys, users=users)


@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        # Check the submitted credentials against a database of authorized users
        if username == ADMIN_PANEL_USERNAME and password == ADMIN_PANEL_PASSWORD:
            # Set a session variable to indicate that the user is logged in
            session['logged_in'] = True
            return redirect(url_for('home'))
        else:
            error = 'Invalid username or password'
    return render_template('login.html', error=error)


@app.route('/generate_keys', methods=['GET', 'POST'])
def generate_keys():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    db = client[DB_NAME]
    if request.method == 'POST':
        num_keys = int(request.form['num_keys'])
        days_valid = int(request.form['days_valid'])

        # Generate the specified number of keys
        keys_collection = db['keys']
        keys = []
        for i in range(num_keys):
            key = generate_key()
            key_doc = {
                "key": key,
                "days": days_valid,
                "used": False
            }
            keys_collection.insert_one(key_doc)
            keys.append(key)

        return redirect(url_for('keys'))

    # If the request method is GET, show the generate_keys.html page
    return render_template('generate_keys.html')



def generate_key():
    # Define the length of each key
    key_length = 16

    # Define the characters to use when generating keys
    key_chars = string.ascii_uppercase + string.digits

    key = ''.join(random.choice(key_chars) for _ in range(key_length))
    key = '-'.join([key[i:i+4] for i in range(0, len(key), 4)])

    return key


@app.route('/keys')
def keys():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    db = client[DB_NAME]
    keys_collection = db['keys']
    keys = list(keys_collection.find())

    return render_template('keys.html', keys=keys)


@app.route('/users')
def users():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    db = client[DB_NAME]
    users_collection = db['users']
    users = list(users_collection.find())
    return render_template('users.html', users=users)



@app.route('/delete_key', methods=['POST'])
def delete_key():
    db = client[DB_NAME]
    keys_collection = db['keys']

    key = request.form['key']
    keys_collection.delete_one({"key": key})

    return redirect(url_for('keys'))


@app.route('/disable_user', methods=['POST'])
def disable_user():
    db = client[DB_NAME]
    users_collection = db['users']

    hwid = request.form['hwid']
    users_collection.update_one({"hwid": hwid}, {"$set": {"disabled": True}})

    return redirect(url_for('users'))


@app.route('/enable_user', methods=['POST'])
def enable_user():
    db = client[DB_NAME]
    users_collection = db['users']

    hwid = request.form['hwid']
    users_collection.update_one({"hwid": hwid}, {"$set": {"disabled": False}})

    return redirect(url_for('users'))


@app.route('/delete_user', methods=['POST'])
def delete_user():
    db = client[DB_NAME]
    users_collection = db['users']

    hwid = request.form['hwid']
    confirm_username = request.form['confirm_username']

    user = users_collection.find_one({"hwid": hwid})

    if user is not None and user['username'] == confirm_username:
        users_collection.delete_one({"hwid": hwid})
        return jsonify({'success': True, 'message': 'User deleted successfully'})
    else:
        # The username entered for confirmation doesn't match the user's username
        # Show an error message and return error status
        return jsonify({'success': False, 'message': 'Incorrect confirmation username. User was not deleted.'})
    

from flask import jsonify

@app.route('/edit_user', methods=['POST'])
def edit_user():
    db = client[DB_NAME]
    users_collection = db['users']

    hwid = request.form['hwid']
    new_username = request.form['new_username']

    result = users_collection.update_one({'hwid': hwid},
                                          {'$set': {'username': new_username}})

    if result.modified_count == 1:
        return jsonify({'success': True, 'message': 'User edited successfully'})
    else:
        return jsonify({'success': False, 'message': 'User was not edited'})
    

@app.route('/latest_login')
def latest_login():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    db = client[DB_NAME]
    users_collection = db['users']
    latest_user = users_collection.find_one(sort=[('last_login', pymongo.DESCENDING)])
    if latest_user:
        return {'username': latest_user['username'], 'last_login': latest_user['last_login']}
    else:
        return {'username': 'No users found', 'last_login': ''}
    

@app.route('/user/<username>')
def user(username):
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    db = client[DB_NAME]
    users_collection = db['users']
    user = users_collection.find_one({'username': username})
    if user:
        return render_template('user.html', user=user)
    else:
        return 'User not found'


@app.template_filter()
def format_datetime(value, format='%m/%d/%Y, %I:%M:%S %p'):
    timestamp = value.timestamp()
    return datetime.utcfromtimestamp(timestamp).strftime(format)



if __name__ == '__main__':
    app.run(debug=True)
