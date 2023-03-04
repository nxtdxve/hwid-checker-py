from flask import Flask, render_template, request, redirect, url_for, jsonify
import pymongo
from datetime import datetime, timedelta
import string
import random
import os
from dotenv import load_dotenv

load_dotenv()
DB_URI = os.environ.get("DB_URI")
DB_NAME = os.environ.get("DB_NAME")
client = pymongo.MongoClient(DB_URI)

app = Flask(__name__)

@app.route('/')
def home():
    db = client[DB_NAME]
    keys_collection = db['keys']
    keys = list(keys_collection.find())

    users_collection = db['users']
    users = list(users_collection.find())

    return render_template('home.html', keys=keys, users=users)

@app.route('/generate_keys', methods=['GET', 'POST'])
def generate_keys():
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
        
        return render_template('generate_keys.html', keys=keys)
    
    return render_template('generate_keys.html')

def generate_key():
    # Define the length of each key
    key_length = 16

    # Define the characters to use when generating keys
    key_chars = string.ascii_lowercase + string.ascii_uppercase + string.digits

    key = ''.join(random.choice(key_chars) for _ in range(key_length))
    key = '-'.join([key[i:i+4] for i in range(0, len(key), 4)])

    return key

@app.route('/delete_key', methods=['POST'])
def delete_key():
    db = client[DB_NAME]
    keys_collection = db['keys']

    key = request.form['key']
    keys_collection.delete_one({"key": key})

    return redirect(url_for('home'))

@app.route('/disable_user', methods=['POST'])
def disable_user():
    db = client[DB_NAME]
    users_collection = db['users']

    hwid = request.form['hwid']
    users_collection.update_one({"hwid": hwid}, {"$set": {"disabled": True}})

    return redirect(url_for('home'))

@app.route('/enable_user', methods=['POST'])
def enable_user():
    db = client[DB_NAME]
    users_collection = db['users']

    hwid = request.form['hwid']
    users_collection.update_one({"hwid": hwid}, {"$set": {"disabled": False}})

    return redirect(url_for('home'))



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



if __name__ == '__main__':
    app.run(debug=True)
