"""
Management command to delete user from MongoDB.
"""
from django.core.management.base import BaseCommand
from models.mongodb import db


class Command(BaseCommand):
    help = 'Delete a user from MongoDB'
    
    def add_arguments(self, parser):
        parser.add_argument('username', type=str, help='Username to delete')
    
    def handle(self, *args, **options):
        username = options['username']
        
        # Find user
        user = db.users.find_one({'username': username})
        
        if not user:
            self.stdout.write(self.style.ERROR(f'User "{username}" not found'))
            return
        
        # Confirm deletion
        confirm = input(f'Are you sure you want to delete user "{username}"? (yes/no): ')
        
        if confirm.lower() != 'yes':
            self.stdout.write(self.style.WARNING('Deletion cancelled'))
            return
        
        # Delete user
        result = db.users.delete_one({'username': username})
        
        if result.deleted_count > 0:
            self.stdout.write(self.style.SUCCESS(f'User "{username}" deleted successfully'))
        else:
            self.stdout.write(self.style.ERROR('Failed to delete user'))
