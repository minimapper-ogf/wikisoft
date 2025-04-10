import json
from werkzeug.security import generate_password_hash

username = "alice"
password = "securepassword123"

with open("data/users.json", "r") as f:
    users = json.load(f)

users[username] = {
    "password_hash": generate_password_hash(password),
    "role": "admin"
}

with open("data/users.json", "w") as f:
    json.dump(users, f, indent=2)

print(f"User {username} created.")
