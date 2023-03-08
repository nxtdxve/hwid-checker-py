import os
import subprocess
import sys
import tempfile
from datetime import datetime, timedelta

import dns.resolver
import pymongo
import requests
import wmi

import config

dns.resolver.default_resolver = dns.resolver.Resolver(configure=False)
dns.resolver.default_resolver.nameservers = ['8.8.8.8']


def check_for_updates() -> None:
    """Check for updates on GitHub and prompt the user to update if a new version is available."""
    url = f"https://api.github.com/repos/{config.REPO_OWNER}/{config.REPO_NAME}/releases/latest"
    response = requests.get(url, headers={"Accept": "application/vnd.github.v3+json"})

    if response.status_code == 200:
        release_info = response.json()
        latest_version = release_info["tag_name"]

        if latest_version != config.VERSION:
            print("A new version is available:", latest_version)

            download_url = None
            for asset in release_info["assets"]:
                if asset["name"].endswith(".exe"):
                    download_url = asset["browser_download_url"]
                    break

            if download_url is None:
                print("Could not find a downloadable executable file in the latest release.")
                print("Please manually update the script to the latest version by downloading the newest version.")
                return

            download_path = os.path.join(tempfile.gettempdir(), f"{config.REPO_NAME}.exe")
            print(f"Downloading the new version of {config.REPO_NAME}...")
            subprocess.call(["powershell", "-Command", f"(New-Object System.Net.WebClient).DownloadFile('{download_url}', '{download_path}')"])

            # Replace the current script with the new version and restart the script
            if getattr(sys, 'frozen', False):
                current_script_path = sys.executable
                temp_script_path = os.path.join(tempfile.gettempdir(), f"{config.REPO_NAME}_old.exe")
                os.rename(current_script_path, temp_script_path)
                os.rename(download_path, current_script_path)

                print("Update successful. Restarting the script with the new version...")
                os.execv(sys.executable, [sys.executable] + sys.argv)
                os.remove(temp_script_path)
            else:
                print("Cannot replace the current script when running as a Python script.")
                print("Please manually update the script to the latest version by pulling the newest version from github.")

    else:
        print("Failed to get the latest release information.")


def check_user_authentication() -> None:
    """Check if the user is authenticated and update the user's information if necessary."""
    db_uri = config.DB_URI
    db_name = config.DB_NAME

    client = pymongo.MongoClient(db_uri)
    db = client[db_name]
    users_collection = db["users"]

    # Get the HWID of the computer
    wmi_obj = wmi.WMI()
    hwid = wmi_obj.Win32_ComputerSystemProduct()[0].UUID

    user = users_collection.find_one({"hwid": hwid})

    # If the user exists, update their information
    if user is not None:
        users_collection.update_one(
            {"hwid": hwid},
            {"$set": {"last_login": datetime.now(), 
                      "ip_address": requests.get('https://api.ipify.org').text, 
                      "country": requests.get('https://ipapi.co/country').text}}
        )

        if user["disabled"]:
            print("Your account is currently disabled.")
            if datetime.now() > user["expiration_date"]:
                while True:
                    key = input("Please enter a new serial key or press enter to exit: ")
                    if key == "":
                        sys.exit()
                    key_doc = db['keys'].find_one({"key": key})
                    if key_doc is not None and not key_doc["used"]:
                        days_valid = key_doc["days"]
                        registration_date = datetime.now()
                        expiration_date = registration_date + timedelta(days=days_valid)
                        users_collection.update_one(
                            {"hwid": hwid},
                            {"$set": {"disabled": False, 
                                      "expiration_date": expiration_date, 
                                      "key": key, 
                                      "last_login": datetime.now()}}
                        )
                        db['keys'].update_one(
                            {"key": key},
                            {"$set": {"used": True}}
                        )
                        print("Your account has been reactivated.")
                        break
                    else:
                        print("Invalid serial key.")
        else:
            if datetime.now() > user["expiration_date"]:
                users_collection.update_one(
                    {"hwid": hwid},
                    {"$set": {"disabled": True}}
                )
                print("Your account has expired.")

            else:
                days_left = (user['expiration_date'] - datetime.now()).days
                expiration_date = user['expiration_date'].strftime('%b %d, %Y')
                print(f"Welcome back, {user['username']}!")
                print(f"Your account expires in {days_left} days ({expiration_date}).")
                print("Thank you for using our software.")
                input("Press any key to continue...")


    else:
        key = input("Please enter a serial key: ")

        keys_collection = db['keys']
        key_doc = keys_collection.find_one({"key": key})
        if key_doc is not None:
            if not key_doc["used"]:
                username = input("Please enter a username: ")

                # Calculate the expiration date based on the number of days in the key
                days_valid = key_doc["days"]
                registration_date = datetime.now()
                expiration_date = registration_date + timedelta(days=days_valid)

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

                keys_collection.update_one(
                    {"key": key},
                    {"$set": {"used": True}}
                )
            else:
                print("Invalid serial key.")
        else:
            print("Invalid serial key.")


def main() -> None:
    """Main function"""
    try:
        check_for_updates()
        check_user_authentication()
    except Exception as e:
        print(f"An error occurred: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()