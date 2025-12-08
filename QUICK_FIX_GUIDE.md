# Quick Fix Guide - Login Duplicate Key Error

## ⚡ Quick Steps to Fix Your Login Issue

### 1. Pull the Latest Changes

```bash
cd /home/ubuntu/nexaai
git pull origin master
```

### 2. Run the Username Normalization Command

This will fix any existing users and rebuild the database index:

```bash
python manage.py fix_username_case
```

### 3. Restart Your Django Server

**If using `runserver`:**
```bash
# Stop the server (Ctrl+C) and restart:
python manage.py runserver
```

**If using systemd/supervisor:**
```bash
sudo systemctl restart nexaai
# or
sudo supervisorctl restart nexaai
```

### 4. Test Your Login

Go to your login page and try logging in with your username (any case will work now).

## ✅ What Was Fixed

1. **Custom Login View**: Replaced Django's built-in LoginView with a custom one that works with MongoDB
2. **Case-Insensitive Usernames**: MongoDB now treats "dobbeltop", "Dobbeltop", and "DOBBELTOP" as the same username
3. **Username Normalization**: All usernames are now stored in lowercase

## 🔍 Verify the Fix

After applying the fix, you should be able to:
- Login with any case variation of your username
- See no duplicate key errors in the logs
- Create new accounts without issues

## 📚 More Information

For detailed information about the fix, see:
- `LOGIN_FIX_APPLIED.md` - Complete technical documentation
- `MONGODB_SETUP.md` - MongoDB configuration guide

## ❓ Still Having Issues?

If you still see errors:

1. Check that MongoDB is running:
   ```bash
   sudo systemctl status mongod
   ```

2. Check Django logs for error messages

3. Try creating a new test user:
   ```bash
   python manage.py createsuperuser_mongo
   ```

4. Verify the index was created:
   ```bash
   python manage.py shell
   ```
   ```python
   from models.mongodb import db
   print(db.users.index_information())
   ```
