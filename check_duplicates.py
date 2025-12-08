#!/usr/bin/env python
"""
Script to check for duplicate usernames in MongoDB.
Run this to see what duplicates exist before fixing them.
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'nexaai.settings')
django.setup()

from models.mongodb import db
from collections import defaultdict

def check_duplicates():
    """Check for duplicate usernames (case-insensitive)."""
    print("Checking for duplicate usernames...\n")
    
    # Get all users
    users = list(db.users.find({}, {'_id': 1, 'username': 1, 'email': 1, 'date_joined': 1}))
    
    if not users:
        print("No users found in database.")
        return
    
    print(f"Total users in database: {len(users)}\n")
    
    # Group by lowercase username
    username_groups = defaultdict(list)
    for user in users:
        username_lower = user['username'].lower()
        username_groups[username_lower].append(user)
    
    # Find duplicates
    duplicates = {k: v for k, v in username_groups.items() if len(v) > 1}
    
    if not duplicates:
        print("✓ No duplicate usernames found!")
        print("\nAll usernames:")
        for user in users:
            print(f"  - {user['username']} (ID: {user['_id']})")
        return
    
    print(f"⚠ Found {len(duplicates)} duplicate username(s):\n")
    
    for username_lower, user_list in duplicates.items():
        print(f"Username: '{username_lower}' (lowercase)")
        print(f"  Found {len(user_list)} accounts:")
        for user in user_list:
            date_joined = user.get('date_joined', 'Unknown')
            email = user.get('email', 'No email')
            print(f"    - '{user['username']}' (ID: {user['_id']}, Email: {email}, Joined: {date_joined})")
        print()
    
    print("\nRecommendation:")
    print("Run the fix command to merge duplicates:")
    print("  python manage.py fix_username_case --merge-duplicates")

if __name__ == '__main__':
    check_duplicates()
