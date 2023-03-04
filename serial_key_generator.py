import string
import random
import pymongo
import dns.resolver
import os
from dotenv import load_dotenv

dns.resolver.default_resolver = dns.resolver.Resolver(configure=False)
dns.resolver.default_resolver.nameservers = ['8.8.8.8']

load_dotenv()
DB_URI = os.environ.get("DB_URI")
DB_NAME = os.environ.get("DB_NAME")
client = pymongo.MongoClient(DB_URI)

# Define the number of keys to generate
num_keys = 10

# Define the length of each key
key_length = 16

# Define the characters to use when generating keys
key_chars = string.ascii_uppercase + string.digits

# Define the number of days each key should activate the account for
key_activation_days = 30

# Generate the keys
keys = []
for i in range(num_keys):
    key = ''.join(random.choice(key_chars) for _ in range(key_length))
    key = '-'.join([key[i:i+4] for i in range(0, len(key), 4)])
    key_doc = {
        "key": key,
        "used": False,
        "activation_days": key_activation_days
    }
    keys.append(key)

# Insert the keys into the database
keys_collection = client[DB_NAME]['keys']
for key in keys:
    print(key)
    keys_collection.insert_one({"key": key, "used": False, "activation_days": key_activation_days})

print(f"Successfully generated {num_keys} keys.")
