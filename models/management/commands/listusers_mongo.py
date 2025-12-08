"""
Management command to list users in MongoDB.
"""
from django.core.management.base import BaseCommand
from models.mongodb import db


class Command(BaseCommand):
    help = 'List all users in MongoDB'
    
    def handle(self, *args, **options):
        users = list(db.users.find())
        
        if not users:
            self.stdout.write(self.style.WARNING('No users found in MongoDB'))
            return
        
        self.stdout.write(self.style.SUCCESS(f'Found {len(users)} user(s) in MongoDB:'))
        self.stdout.write('')
        
        for user in users:
            self.stdout.write(f"ID: {user['_id']}")
            self.stdout.write(f"Username: {user['username']}")
            self.stdout.write(f"Email: {user.get('email', 'N/A')}")
            self.stdout.write(f"Active: {user.get('is_active', True)}")
            self.stdout.write(f"Staff: {user.get('is_staff', False)}")
            self.stdout.write(f"Superuser: {user.get('is_superuser', False)}")
            self.stdout.write(f"Joined: {user.get('date_joined', 'N/A')}")
            self.stdout.write('')
