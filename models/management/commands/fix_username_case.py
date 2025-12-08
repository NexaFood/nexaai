"""
Management command to normalize all usernames to lowercase and rebuild the username index.
This fixes any case-sensitivity issues with existing users.

Usage:
    python manage.py fix_username_case
"""
from django.core.management.base import BaseCommand
from models.mongodb import db
from pymongo import ASCENDING
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Normalize all usernames to lowercase and rebuild username index with case-insensitive collation'

    def handle(self, *args, **options):
        self.stdout.write('Starting username normalization...\n')
        
        try:
            # Get all users
            users = list(db.users.find({}))
            
            if not users:
                self.stdout.write(self.style.WARNING('No users found in database'))
                return
            
            self.stdout.write(f'Found {len(users)} users\n')
            
            # Track changes
            updated_count = 0
            errors = []
            
            # Normalize usernames
            for user in users:
                username = user.get('username', '')
                username_lower = username.lower()
                
                if username != username_lower:
                    try:
                        # Update to lowercase
                        result = db.users.update_one(
                            {'_id': user['_id']},
                            {'$set': {'username': username_lower}}
                        )
                        
                        if result.modified_count > 0:
                            self.stdout.write(f'  ✓ Normalized: "{username}" → "{username_lower}"')
                            updated_count += 1
                        
                    except Exception as e:
                        error_msg = f'Failed to update user "{username}": {e}'
                        self.stdout.write(self.style.ERROR(f'  ✗ {error_msg}'))
                        errors.append(error_msg)
                else:
                    self.stdout.write(f'  - Already lowercase: "{username}"')
            
            # Rebuild username index with case-insensitive collation
            self.stdout.write('\nRebuilding username index...')
            
            try:
                # Drop existing username index
                try:
                    db.users.drop_index('username_1')
                    self.stdout.write('  ✓ Dropped old username index')
                except Exception as e:
                    self.stdout.write(f'  - Old index not found or already dropped: {e}')
                
                # Create new case-insensitive unique index
                db.users.create_index(
                    [('username', ASCENDING)],
                    unique=True,
                    collation={'locale': 'en', 'strength': 2},
                    name='username_1'
                )
                self.stdout.write('  ✓ Created new case-insensitive username index')
                
            except Exception as e:
                error_msg = f'Failed to rebuild index: {e}'
                self.stdout.write(self.style.ERROR(f'  ✗ {error_msg}'))
                errors.append(error_msg)
            
            # Summary
            self.stdout.write('\n' + '='*60)
            self.stdout.write(self.style.SUCCESS(f'✓ Normalization complete!'))
            self.stdout.write(f'  Total users: {len(users)}')
            self.stdout.write(f'  Updated: {updated_count}')
            self.stdout.write(f'  Errors: {len(errors)}')
            
            if errors:
                self.stdout.write('\nErrors encountered:')
                for error in errors:
                    self.stdout.write(f'  - {error}')
            
            self.stdout.write('\n' + '='*60)
            self.stdout.write(self.style.SUCCESS('Username normalization finished successfully!'))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'\nFatal error: {e}'))
            raise
