# Login Duplicate Key Error - Fix Applied

## Problem Description

When attempting to login, users encountered this error:

```
Exception Type: DuplicateKeyError
Exception Value: E11000 duplicate key error collection: NexaAI.users index: username_1 dup key: { username: "dobbeltop" }
```

## Root Cause

The issue had multiple contributing factors:

1. **Django's Built-in LoginView**: The application was using Django's standard `LoginView` which is designed for Django's ORM-based User model, not for custom MongoDB authentication backends.

2. **Case-Sensitive Username Index**: MongoDB's unique index on the `username` field was case-sensitive by default, but the authentication logic normalized usernames to lowercase. This created a mismatch.

3. **Authentication Flow Mismatch**: The Django LoginView wasn't properly using the custom `MongoDBAuthBackend`, leading to attempts to create duplicate users during login.

## Fixes Applied

### 1. Custom Login View (✓ Applied)

**File:** `models/views.py`

Added a custom `login_view()` function that:
- Properly uses the `MongoDBAuthBackend` for authentication
- Normalizes usernames to lowercase before authentication
- Handles errors gracefully with user-friendly messages
- Redirects to the appropriate page after successful login

**Key features:**
```python
def login_view(request):
    # Normalize username to lowercase
    username = request.POST.get('username', '').strip().lower()
    
    # Use Django's authenticate() which calls MongoDBAuthBackend
    user = authenticate(request, username=username, password=password)
    
    if user is not None:
        login(request, user)
        return redirect(next_url)
```

### 2. Updated URL Configuration (✓ Applied)

**File:** `nexaai/urls.py`

Changed from:
```python
path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
```

To:
```python
path('login/', views.login_view, name='login'),
```

### 3. Case-Insensitive Username Index (✓ Applied)

**File:** `models/mongodb.py`

Updated the username index to use case-insensitive collation:
```python
self.users.create_index(
    [('username', ASCENDING)], 
    unique=True,
    collation={'locale': 'en', 'strength': 2}  # Case-insensitive
)
```

This ensures MongoDB treats "dobbeltop", "Dobbeltop", and "DOBBELTOP" as the same username.

### 4. Username Normalization Script (✓ Created)

**File:** `models/management/commands/fix_username_case.py`

Created a management command to:
- Normalize all existing usernames to lowercase
- Rebuild the username index with case-insensitive collation
- Provide detailed output of changes made

## How to Apply the Fix

### Step 1: Run the Username Normalization Command

This will fix any existing users with mixed-case usernames:

```bash
cd /home/ubuntu/nexaai
source venv/bin/activate  # If using virtual environment
python manage.py fix_username_case
```

Expected output:
```
Starting username normalization...
Found X users
  ✓ Normalized: "Dobbeltop" → "dobbeltop"
  - Already lowercase: "otheruser"

Rebuilding username index...
  ✓ Dropped old username index
  ✓ Created new case-insensitive username index

============================================================
✓ Normalization complete!
  Total users: X
  Updated: Y
  Errors: 0
============================================================
```

### Step 2: Restart the Django Server

```bash
# If running with runserver
python manage.py runserver

# If using systemd/supervisor, restart the service
sudo systemctl restart nexaai
```

### Step 3: Test the Login

1. Navigate to `/login/`
2. Enter your username (any case: "dobbeltop", "Dobbeltop", "DOBBELTOP")
3. Enter your password
4. Click "Login"

You should now be able to login successfully without any duplicate key errors.

## What Changed in the Authentication Flow

### Before (Broken):
```
User enters credentials
    ↓
Django LoginView (expects Django ORM User model)
    ↓
Attempts to work with MongoDB User
    ↓
❌ ERROR: Duplicate key or authentication failure
```

### After (Fixed):
```
User enters credentials
    ↓
Custom login_view() function
    ↓
Normalizes username to lowercase
    ↓
Calls authenticate() → MongoDBAuthBackend
    ↓
Finds user in MongoDB (case-insensitive)
    ↓
Checks password
    ↓
✓ SUCCESS: User logged in
```

## Prevention

To prevent this issue in the future:

1. **Always use lowercase for usernames**: Both signup and login views now normalize usernames to lowercase
2. **Case-insensitive index**: The MongoDB index now treats usernames case-insensitively
3. **Custom authentication views**: Using custom views ensures proper integration with MongoDB

## Testing Checklist

- [ ] Run `python manage.py fix_username_case`
- [ ] Restart Django server
- [ ] Test login with lowercase username
- [ ] Test login with mixed-case username
- [ ] Test signup with new username
- [ ] Test signup with existing username (should show error)
- [ ] Verify no duplicate key errors in logs

## Additional Notes

### Signup Flow
The signup flow was already correct and continues to work:
- Normalizes username to lowercase
- Checks for existing username
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

## Support

If you encounter any issues after applying this fix:

1. Check the Django logs for error messages
2. Verify MongoDB is running and accessible
3. Ensure the username index was rebuilt successfully
4. Try creating a new test user to verify signup works

For additional help, refer to:
- `MONGODB_SETUP.md` - MongoDB configuration guide
- `FIXES_NEEDED.md` - Other known issues and fixes
