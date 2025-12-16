"""
Management command to fix duplicate username issues and normalize usernames to lowercase.
This command will:
1. Find duplicate usernames (case-insensitive)
2. Keep the oldest account and delete duplicates
3. Normalize all usernames to lowercase
4. Drop and recreate the username index with case-insensitive collation

Usage:
    python manage.py fix_username_case
"""
from django.core.management.base import BaseCommand
from models.mongodb import db
from pymongo import ASCENDING
from collections import defaultdict
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Fix duplicate usernames and normalize to lowercase with case-insensitive index'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without making changes',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No changes will be made\n'))
        
        self.stdout.write('='*70)
        self.stdout.write('Username Duplicate Fix and Normalization')
        self.stdout.write('='*70 + '\n')
        
        try:
            # Step 1: Get all users
            self.stdout.write('Step 1: Fetching all users from database...')
            users = list(db.users.find({}, {
                '_id': 1, 
                'username': 1, 
                'email': 1, 
                'date_joined': 1,
                'is_superuser': 1,
                'is_staff': 1
            }))
            
            if not users:
                self.stdout.write(self.style.WARNING('No users found in database'))
                return
            
            self.stdout.write(f'  Found {len(users)} user(s)\n')
            
            # Step 2: Group by lowercase username
            self.stdout.write('Step 2: Checking for duplicate usernames...')
            username_groups = defaultdict(list)
            for user in users:
                username_lower = user['username'].lower()
                username_groups[username_lower].append(user)
            
            # Find duplicates
            duplicates = {k: v for k, v in username_groups.items() if len(v) > 1}
            
            if duplicates:
                self.stdout.write(self.style.WARNING(f'  Found {len(duplicates)} duplicate username(s)'))
                
                # Step 3: Handle duplicates
                self.stdout.write('\nStep 3: Resolving duplicates...')
                for username_lower, user_list in duplicates.items():
                    self.stdout.write(f'\n  Duplicate: "{username_lower}"')
                    
                    # Sort by date_joined (oldest first), then by is_superuser, is_staff
                    user_list.sort(key=lambda u: (
                        u.get('date_joined') or datetime.min,
                        not u.get('is_superuser', False),
                        not u.get('is_staff', False)
                    ))
                    
                    # Keep the first (oldest/most privileged) user
                    keep_user = user_list[0]
                    delete_users = user_list[1:]
                    
                    self.stdout.write(f'    KEEP: "{keep_user["username"]}" (ID: {keep_user["_id"]}, '
                                    f'Joined: {keep_user.get("date_joined", "Unknown")})')
                    
                    for user in delete_users:
                        self.stdout.write(f'    DELETE: "{user["username"]}" (ID: {user["_id"]}, '
                                        f'Joined: {user.get("date_joined", "Unknown")})')
                        
                        if not dry_run:
                            # Delete the duplicate user
                            result = db.users.delete_one({'_id': user['_id']})
                            if result.deleted_count > 0:
                                self.stdout.write(self.style.SUCCESS(f'      ✓ Deleted'))
                            else:
                                self.stdout.write(self.style.ERROR(f'      ✗ Failed to delete'))
                    
                    # Update the kept user to lowercase
                    if keep_user['username'] != username_lower:
                        if not dry_run:
                            db.users.update_one(
                                {'_id': keep_user['_id']},
                                {'$set': {'username': username_lower}}
                            )
                            self.stdout.write(f'    ✓ Normalized to: "{username_lower}"')
            else:
                self.stdout.write('  ✓ No duplicates found\n')
            
            # Step 4: Normalize remaining usernames
            self.stdout.write('\nStep 4: Normalizing all usernames to lowercase...')
            
            # Refresh user list after deleting duplicates
            if not dry_run and duplicates:
                users = list(db.users.find({}, {'_id': 1, 'username': 1}))
            
            normalized_count = 0
            for user in users:
                username = user['username']
                username_lower = username.lower()
                
                if username != username_lower:
                    if not dry_run:
                        db.users.update_one(
                            {'_id': user['_id']},
                            {'$set': {'username': username_lower}}
                        )
                    self.stdout.write(f'  ✓ "{username}" → "{username_lower}"')
                    normalized_count += 1
            
            if normalized_count == 0:
                self.stdout.write('  ✓ All usernames already lowercase')
            else:
                self.stdout.write(f'  ✓ Normalized {normalized_count} username(s)')
            
            # Step 5: Rebuild username index
            self.stdout.write('\nStep 5: Rebuilding username index with case-insensitive collation...')
            
            if not dry_run:
                # Drop existing username index
                try:
                    db.users.drop_index('username_1')
                    self.stdout.write('  ✓ Dropped old username index')
                except Exception as e:
                    self.stdout.write(f'  - Old index not found: {e}')
                
                # Create new case-insensitive unique index
                try:
                    db.users.create_index(
                        [('username', ASCENDING)],
                        unique=True,
                        collation={'locale': 'en', 'strength': 2},
                        name='username_1'
                    )
                    self.stdout.write('  ✓ Created new case-insensitive username index')
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'  ✗ Failed to create index: {e}'))
                    raise
            else:
                self.stdout.write('  (Skipped in dry-run mode)')
            
            # Summary
            self.stdout.write('\n' + '='*70)
            if dry_run:
                self.stdout.write(self.style.WARNING('DRY RUN COMPLETE - No changes were made'))
                self.stdout.write('Run without --dry-run to apply changes')
            else:
                self.stdout.write(self.style.SUCCESS('✓ FIX COMPLETE!'))
                self.stdout.write('\nYou can now:')
                self.stdout.write('  1. Restart your Django server')
                self.stdout.write('  2. Login with any case variation of your username')
                self.stdout.write('  3. No more duplicate key errors!')
            self.stdout.write('='*70)
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'\n✗ Fatal error: {e}'))
            import traceback
            traceback.print_exc()
            raise
