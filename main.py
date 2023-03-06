import wmi
import pymongo
import dns.resolver
import requests
from datetime import datetime, timedelta
import os
import subprocess
import tempfile
import sys
import config

dns.resolver.default_resolver = dns.resolver.Resolver(configure=False)
dns.resolver.default_resolver.nameservers = ['8.8.8.8']

# Check for the latest version on GitHub
url = f"https://api.github.com/repos/{config.REPO_OWNER}/{config.REPO_NAME}/releases/latest"
response = requests.get(url, headers={"Accept": "application/vnd.github.v3+json"})
if response.status_code == 200:
    release_info = response.json()
    latest_version = release_info["tag_name"]

    # Compare the latest version with the current version
    if latest_version != config.VERSION:
        print("A new version is available: ", latest_version)

        download_url = release_info["assets"][0]["browser_download_url"]
        download_path = os.path.join(tempfile.gettempdir(), f"{config.REPO_NAME}.exe")
        print(f"Downloading the new version of {config.REPO_NAME}...")
        subprocess.call(["powershell", "-Command", f"(New-Object System.Net.WebClient).DownloadFile('{download_url}', '{download_path}')"])

        # Replace the current script with the downloaded script if running as an executable
        if getattr(sys, 'frozen', False):
            current_script_path = sys.executable
            os.remove(current_script_path)
            os.rename(download_path, current_script_path)
            # Restart the script with the new version
            print("Update successful. Restarting the script with the new version...")
            os.execv(sys.executable, [sys.executable] + sys.argv)
        else:
            print("Cannot replace the current script when running as a Python script.")
            print("Please manually update the script to the latest version by pulling the newest version from github.")
else:
    print("Failed to get the latest release information.")




DB_URI = config.DB_URI
DB_NAME = config.DB_NAME
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
