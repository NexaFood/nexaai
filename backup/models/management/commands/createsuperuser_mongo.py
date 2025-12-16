"""
Management command to create superuser in MongoDB.
"""
from django.core.management.base import BaseCommand
from models.auth_backend import create_user
import getpass


class Command(BaseCommand):
    help = 'Create a superuser in MongoDB'
    
    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Creating superuser in MongoDB...'))
        
        # Get username
        while True:
            username = input('Username: ').strip()
            if username:
                break
            self.stdout.write(self.style.ERROR('Username cannot be empty'))
        
        # Get email
        email = input('Email address (optional): ').strip()
        
        # Get password
        while True:
            password = getpass.getpass('Password: ')
            password2 = getpass.getpass('Password (again): ')
            
            if password != password2:
                self.stdout.write(self.style.ERROR('Passwords do not match'))
                continue
            
            if len(password) < 4:
                self.stdout.write(self.style.ERROR('Password must be at least 4 characters'))
                continue
            
            break
        
        # Create superuser
        try:
            user = create_user(
                username=username,
                email=email,
                password=password,
                is_superuser=True,
                is_staff=True
            )
            
            self.stdout.write(self.style.SUCCESS(f'Superuser "{username}" created successfully in MongoDB!'))
            self.stdout.write(f'User ID: {user.id}')
        
        except ValueError as e:
            self.stdout.write(self.style.ERROR(str(e)))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Failed to create superuser: {e}'))
