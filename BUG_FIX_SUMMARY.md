# Critical Bug Fix - Login Duplicate Key Error

## The Bug

**Location:** `models/auth_backend.py`, line 94

**Error:** E11000 duplicate key error when trying to login

**Root Cause:** The `MongoUser.save()` method had a logic error that caused it to always try to create a new user instead of updating an existing one.

## The Problem

```python
# BROKEN CODE (line 94):
if hasattr(self, '_id'):
    # Update existing user
else:
    # Create new user - THIS WAS ALWAYS EXECUTED!
```

The bug was checking for `self._id`, but the `MongoUser` class stores the ID as `self.id` (set on line 53):

```python
def __init__(self, user_doc):
    self._doc = user_doc
    self.id = str(user_doc['_id'])  # ← ID is stored as 'id', not '_id'
```

## What Happened During Login

1. User enters credentials and clicks "Login"
2. Authentication succeeds, `MongoUser` object is created
3. Django's session middleware calls `user.save()` to update last_login
4. The `save()` method checks `if hasattr(self, '_id')` → **False** (because it's `self.id`)
5. It goes to the "create new user" branch
6. Tries to insert a new user with the same username
7. **💥 BOOM: E11000 duplicate key error**

## The Fix

```python
# FIXED CODE (line 94):
if self.id:  # Check if user already has an ID (existing user)
    # Update existing user
else:
    # Create new user
```

Now it correctly checks if `self.id` exists, which it always will for authenticated users.

## How to Apply

```bash
cd /home/ubuntu/nexaai
git pull origin master
# Restart your Django server
python manage.py runserver
# or
sudo systemctl restart nexaai
```

## Testing

After applying the fix, you should be able to:
- ✅ Login successfully without errors
- ✅ See no duplicate key errors in logs
- ✅ Login multiple times without issues
- ✅ Session persistence works correctly

## Why This Wasn't Caught Earlier

This bug only manifests when:
1. A user successfully authenticates
2. Django tries to save the user object (to update last_login)
3. The save() method is called on an existing user

It wouldn't occur during:
- User creation (signup) - different code path
- Failed login attempts - no save() call
- Testing without session middleware

## Additional Notes

- No database migration needed
- No data loss
- Fix is backward compatible
- Safe to deploy immediately

## Related Files

- `models/auth_backend.py` - The fixed file
- `models/views.py` - Login view (already correct)
- `nexaai/urls.py` - URL routing (already correct)

---

**Status:** ✅ FIXED and pushed to master branch
**Commit:** ac68582
