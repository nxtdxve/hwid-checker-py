from dotenv import load_dotenv
import wmi
import pymongo
import dns.resolver
import requests
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

dns.resolver.default_resolver = dns.resolver.Resolver(configure=False)
dns.resolver.default_resolver.nameservers = ['8.8.8.8']

load_dotenv()
DB_URI = os.environ.get("DB_URI")
DB_NAME = os.environ.get("DB_NAME")
client = pymongo.MongoClient(DB_URI)

# Obtain the user's HWID using the WMI API
wmi_obj = wmi.WMI()
hwid = wmi_obj.Win32_ComputerSystemProduct()[0].UUID

# Check if the HWID is in the database
db = client[DB_NAME]
users_collection = db['users']
user = users_collection.find_one({"hwid": hwid})
if user is not None:
    # Update last_login field
    users_collection.update_one(
        {"hwid": hwid},
        {"$set": {"last_login": datetime.now()}}
    )

    # Check if the user is disabled
    if user["disabled"]:
        print("Your account is currently disabled.")
    else:
        # Check if the user has expired
        if datetime.now() > user["expiration_date"]:
            # Disable the user and deny access
            users_collection.update_one(
                {"hwid": hwid},
                {"$set": {"disabled": True}}
            )
            print("Your account has expired.")
        else:
            # Print user information
            print(f"Welcome back, {user['username']}!")
            print(f"Country: {user['country']}")
            print(f"IP Address: {user['ip_address']}")
            print(f"Last Login: {user['last_login']}")
else:
    # Prompt the user to enter a serial key
    key = input("Please enter a serial key: ")

    # Check if the key is valid by querying the database
    keys_collection = db['keys']
    key_doc = keys_collection.find_one({"key": key})
    if key_doc is not None:
        if not key_doc["used"]:
            # Prompt the user to enter a username
            username = input("Please enter a username: ")

            # Calculate the expiration date based on the number of days in the key
            days_valid = key_doc["days"]
            registration_date = datetime.now()
            expiration_date = registration_date + timedelta(days=days_valid)

            # Add the HWID, username, and registration date to the user document
            user_doc = {
                "username": username,
                "hwid": hwid,
                "key": key,
                "ip_address": requests.get('https://api.ipify.org').text,
                "country": requests.get('https://ipapi.co/country').text,
                "disabled": False,
                "last_login": datetime.now(),
                "registration_date": registration_date,
                "expiration_date": expiration_date
            }
            users_collection.insert_one(user_doc)
            print("User registered.")

            # Set the "used" field to True in the "keys" collection
            keys_collection.update_one(
                {"key": key},
                {"$set": {"used": True}}
            )
        else:
            print("Invalid serial key.")
    else:
        print("Invalid serial key.")
