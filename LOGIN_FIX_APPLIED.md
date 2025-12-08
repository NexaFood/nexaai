# Login Duplicate Key Error - Complete Fix Documentation

## Problem Description

When attempting to login, users encountered this error:

```
Exception Type: DuplicateKeyError
Exception Value: E11000 duplicate key error collection: NexaAI.users index: username_1 
collation: { locale: "en", strength: 2, ... } 
dup key: { username: "CollationKey(...)" }
```

## Root Cause Analysis

The issue had multiple contributing factors:

### 1. Django's Built-in LoginView Incompatibility

The application was using Django's standard `LoginView` which is designed for Django's ORM-based User model, not for custom MongoDB authentication backends. This caused authentication to fail and potentially attempt to create duplicate users.

### 2. Existing Duplicate Usernames

The database contained multiple user accounts with the same username in different cases:
- Example: "dobbeltop" and "Dobbeltop" as separate accounts
- MongoDB's original case-sensitive index allowed these as distinct users

### 3. Case-Sensitive vs Case-Insensitive Mismatch

- **Authentication logic**: Normalized usernames to lowercase before lookup
- **MongoDB index**: Was case-sensitive, treating "dobbeltop" and "Dobbeltop" as different
- **Collation index attempt**: Failed because duplicates already existed in the database

### 4. Authentication Flow Mismatch

The Django LoginView wasn't properly using the custom `MongoDBAuthBackend`, leading to the duplicate key error when trying to apply the case-insensitive index.

## Complete Solution

### Fix 1: Custom Login View (✓ Applied)

**File:** `models/views.py`

Added a custom `login_view()` function that:
- Properly uses the `MongoDBAuthBackend` for authentication
- Normalizes usernames to lowercase before authentication
- Handles errors gracefully with user-friendly messages
- Redirects to the appropriate page after successful login

**Implementation:**
```python
def login_view(request):
    """Custom login view for MongoDB authentication."""
    if request.method == 'GET':
        if request.user.is_authenticated:
            return redirect('/')
        return render(request, 'registration/login.html')
    
    # POST - Handle login
    from django.contrib.auth import authenticate, login
    
    username = request.POST.get('username', '').strip().lower()  # Normalize to lowercase
    password = request.POST.get('password', '')
    
    # Authenticate using MongoDBAuthBackend
    user = authenticate(request, username=username, password=password)
    
    if user is not None:
        login(request, user)
        next_url = request.GET.get('next', '/')
        return redirect(next_url)
    else:
        # Show error message
        ...
```

### Fix 2: Updated URL Configuration (✓ Applied)

**File:** `nexaai/urls.py`

Changed from:
```python
path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
```

To:
```python
path('login/', views.login_view, name='login'),
```

### Fix 3: Duplicate Username Cleanup (✓ Applied)

**File:** `models/management/commands/fix_username_case.py`

Created a comprehensive management command that:

1. **Identifies duplicates**: Groups usernames by lowercase version
2. **Keeps the oldest account**: Prioritizes by:
   - Date joined (oldest first)
   - Superuser status
   - Staff status
3. **Deletes duplicate accounts**: Removes newer duplicate accounts
4. **Normalizes all usernames**: Converts remaining usernames to lowercase
5. **Rebuilds the index**: Creates case-insensitive unique index

**Key features:**
- `--dry-run` flag to preview changes without applying them
- Detailed output showing what will be kept/deleted
- Safe to run multiple times (idempotent)

### Fix 4: Case-Insensitive Username Index (✓ Applied)

**File:** `models/mongodb.py`

Updated the username index creation to use case-insensitive collation:
```python
self.users.create_index(
    [('username', ASCENDING)], 
    unique=True,
    collation={'locale': 'en', 'strength': 2},  # Case-insensitive
    name='username_1'
)
```

**Collation parameters:**
- `locale: 'en'`: English language rules
- `strength: 2`: Case-insensitive comparison (ignores case and accents)

## How to Apply the Fix

### Step 1: Pull the Latest Code

```bash
cd /home/ubuntu/nexaai
git pull origin master
```

### Step 2: Preview Changes (Optional but Recommended)

See what will be changed without making any modifications:

```bash
python manage.py fix_username_case --dry-run
```

This will show:
- Which usernames are duplicated
- Which account will be kept (oldest)
- Which accounts will be deleted (newer duplicates)

### Step 3: Apply the Fix

Run the command to fix duplicates and rebuild the index:

```bash
python manage.py fix_username_case
```

Expected output:
```
======================================================================
Username Duplicate Fix and Normalization
======================================================================
Step 1: Fetching all users from database...
  Found X user(s)

Step 2: Checking for duplicate usernames...
  Found Y duplicate username(s)

Step 3: Resolving duplicates...
  Duplicate: "dobbeltop"
    KEEP: "dobbeltop" (ID: ..., Joined: 2024-01-01)
    DELETE: "Dobbeltop" (ID: ..., Joined: 2024-01-02)
      ✓ Deleted

Step 4: Normalizing all usernames to lowercase...
  ✓ All usernames already lowercase

Step 5: Rebuilding username index with case-insensitive collation...
  ✓ Dropped old username index
  ✓ Created new case-insensitive username index

======================================================================
✓ FIX COMPLETE!

You can now:
  1. Restart your Django server
  2. Login with any case variation of your username
  3. No more duplicate key errors!
======================================================================
```

### Step 4: Restart Django Server

**If using `runserver`:**
```bash
# Stop the server (Ctrl+C) and restart:
python manage.py runserver
```

**If using systemd:**
```bash
sudo systemctl restart nexaai
```

**If using supervisor:**
```bash
sudo supervisorctl restart nexaai
```

### Step 5: Test the Login

1. Navigate to `/login/`
2. Enter your username (any case: "dobbeltop", "Dobbeltop", "DOBBELTOP")
3. Enter your password
4. Click "Login"

You should now be able to login successfully without any duplicate key errors.

## What Changed in the Authentication Flow

### Before (Broken):
```
User enters credentials (e.g., "Dobbeltop")
    ↓
Django LoginView (expects Django ORM User model)
    ↓
Attempts to work with MongoDB User
    ↓
❌ ERROR: Duplicate key or authentication failure
```

### After (Fixed):
```
User enters credentials (e.g., "Dobbeltop")
    ↓
Custom login_view() function
    ↓
Normalizes username to lowercase ("dobbeltop")
    ↓
Calls authenticate() → MongoDBAuthBackend
    ↓
Finds user in MongoDB (case-insensitive)
    ↓
Checks password
    ↓
✓ SUCCESS: User logged in
```

## Data Impact

### What Gets Deleted

When duplicate usernames exist (e.g., "dobbeltop" and "Dobbeltop"):
- The **newer account** is deleted
- The **older account** is kept and normalized to lowercase

### What Gets Preserved

- The oldest account for each username
- All data associated with the kept account:
  - 3D models
  - Printers
  - Print jobs
  - User settings

### Data Linked by User ID

If your application links data by user ID (e.g., `user_id` field in models):
- Data linked to deleted accounts will become orphaned
- You may need to manually reassign this data if important

### Data Linked by Username

If your application links data by username:
- Data should automatically be accessible under the normalized username

## Prevention Measures

To prevent this issue in the future:

### 1. Always Use Lowercase for Usernames
Both signup and login views now normalize usernames to lowercase:
```python
username = request.POST.get('username', '').strip().lower()
```

### 2. Case-Insensitive Index
The MongoDB index now treats usernames case-insensitively:
```python
collation={'locale': 'en', 'strength': 2}
```

### 3. Custom Authentication Views
Using custom views ensures proper integration with MongoDB:
- `login_view()` for login
- `signup()` for registration (already existed)

### 4. Validation in Signup
The signup view checks for existing usernames (case-insensitive):
```python
username = username.lower()
if db.users.find_one({'username': username}):
    errors.append('Username already exists')
```

## Verification Checklist

After applying the fix, verify:

- [ ] Run `python manage.py fix_username_case --dry-run` shows no duplicates
- [ ] Django server restarts without errors
- [ ] Can login with lowercase username
- [ ] Can login with mixed-case username (gets normalized)
- [ ] Cannot create new account with existing username (any case)
- [ ] No duplicate key errors in Django logs
- [ ] MongoDB index shows collation:
  ```bash
  python manage.py shell
  ```
  ```python
  from models.mongodb import db
  print(db.users.index_information())
  # Should show 'collation': {'locale': 'en', 'strength': 2, ...}
  ```

## Troubleshooting

### Issue: Command Fails with "Duplicate Key Error"

**Cause:** The command is trying to create the index before removing duplicates.

**Solution:** The updated command now removes duplicates first, then creates the index. Pull the latest code and try again.

### Issue: "No module named 'django'"

**Cause:** Not running in the correct Python environment.

**Solution:** Activate your virtual environment:
```bash
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows
```

### Issue: Can't Find User After Fix

**Cause:** Your account was deleted as a duplicate.

**Solution:** 
1. Check which account was kept:
   ```bash
   python manage.py listusers_mongo
   ```
2. If needed, create a new account:
   ```bash
   python manage.py createsuperuser_mongo
   ```

### Issue: Still Getting Duplicate Key Errors

**Cause:** Index wasn't rebuilt properly.

**Solution:**
1. Manually drop the index:
   ```bash
   python manage.py shell
   ```
   ```python
   from models.mongodb import db
   db.users.drop_index('username_1')
   ```
2. Run the fix command again:
   ```bash
   python manage.py fix_username_case
   ```

## Additional Notes

### Signup Flow
The signup flow was already correct and continues to work:
- Normalizes username to lowercase
- Checks for existing username (case-insensitive via backend)
- Creates new user in MongoDB
- Redirects to login page

### Authentication Backend
The `MongoDBAuthBackend` in `models/auth_backend.py` was already correct:
- Normalizes username to lowercase during authentication
- Checks password using Django's `check_password()`
- Returns `MongoUser` instance on success

### MongoDB Collections
The fix only affects the `users` collection. Other collections remain unchanged:
- `models_3d` - 3D model data
- `printers` - Printer configurations
- `print_jobs` - Print job history
- `generation_jobs` - Meshy.ai generation tasks

### Safe to Run Multiple Times
The `fix_username_case` command is idempotent and safe to run multiple times:
- If no duplicates exist, it just normalizes and rebuilds the index
- If the index already exists with correct collation, it skips that step
- No data loss if run on an already-fixed database

## Related Files

- `models/views.py` - Custom login view
- `models/auth_backend.py` - MongoDB authentication backend
- `models/mongodb.py` - MongoDB connection and index setup
- `nexaai/urls.py` - URL routing configuration
- `models/management/commands/fix_username_case.py` - Fix command
- `QUICK_FIX_GUIDE.md` - Quick reference guide

## Support

If you encounter any issues after applying this fix:

1. Check the Django logs for detailed error messages
2. Run the fix command with `--dry-run` to see current state
3. Verify MongoDB is running and accessible
4. Check the GitHub issues for similar problems
5. Review `MONGODB_SETUP.md` for MongoDB configuration

For additional help, refer to:
- `MONGODB_SETUP.md` - MongoDB configuration guide
- `FIXES_NEEDED.md` - Other known issues and fixes
- GitHub Issues: https://github.com/NexaFood/nexaai/issues
