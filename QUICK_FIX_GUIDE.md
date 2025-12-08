# Quick Fix Guide - Login Duplicate Key Error

## ⚡ Quick Steps to Fix Your Login Issue

### 1. Pull the Latest Changes

```bash
cd /home/ubuntu/nexaai
git pull origin master
```

### 2. Check for Duplicate Usernames (Optional)

First, see what duplicates exist without making changes:

```bash
python manage.py fix_username_case --dry-run
```

This will show you which usernames are duplicated and what will be kept/deleted.

### 3. Run the Fix Command

This will:
- Remove duplicate usernames (keeps the oldest account)
- Normalize all usernames to lowercase
- Rebuild the database index with case-insensitive collation

```bash
python manage.py fix_username_case
```

**Important:** The command will keep the **oldest** account for each duplicate username and delete the newer ones. If you have important data in a newer account, you may want to manually merge the data first.

### 4. Restart Your Django Server

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

### 5. Test Your Login

Go to your login page and try logging in with your username (any case will work now).

## ✅ What Was Fixed

1. **Removed Duplicate Users**: If you had "dobbeltop" and "Dobbeltop" as separate accounts, the older one is kept
2. **Custom Login View**: Replaced Django's built-in LoginView with a custom one that works with MongoDB
3. **Case-Insensitive Usernames**: MongoDB now treats "dobbeltop", "Dobbeltop", and "DOBBELTOP" as the same username
4. **Username Normalization**: All usernames are now stored in lowercase

## 🔍 Understanding the Fix

### Why Did This Happen?

The duplicate key error occurred because:
1. You had multiple accounts with the same username in different cases (e.g., "dobbeltop" and "Dobbeltop")
2. MongoDB's index was case-sensitive, so it allowed these as separate users
3. When we tried to add a case-insensitive index, it failed because duplicates already existed

### What the Fix Does

The `fix_username_case` command:
1. **Finds duplicates**: Groups usernames by their lowercase version
2. **Keeps the oldest**: For each duplicate group, keeps the account created first
3. **Deletes newer duplicates**: Removes the duplicate accounts (newer ones)
4. **Normalizes usernames**: Converts all remaining usernames to lowercase
5. **Rebuilds index**: Creates a new case-insensitive unique index

### Which Account Is Kept?

The command keeps accounts in this priority order:
1. **Oldest account** (by `date_joined`)
2. **Superuser accounts** (if multiple with same date)
3. **Staff accounts** (if multiple with same date)

## 📚 More Information

For detailed information about the fix, see:
- `LOGIN_FIX_APPLIED.md` - Complete technical documentation
- `MONGODB_SETUP.md` - MongoDB configuration guide

## ⚠️ Important Notes

### Data Loss Warning

If you have duplicate usernames, **the newer accounts will be deleted**. This includes:
- User profile data
- Any data linked to that user's ID

However, if your application links data by username (not user ID), the data should remain accessible under the kept account.

### Manual Merge (If Needed)

If you need to preserve data from multiple duplicate accounts:

1. Run with `--dry-run` first to see what will be deleted
2. Manually export data from accounts that will be deleted
3. Import that data into the account that will be kept
4. Then run the fix command

## ❓ Troubleshooting

### Still Getting Duplicate Key Errors?

If you still see errors after running the fix:

1. **Check if the command completed successfully**:
   - Look for "✓ FIX COMPLETE!" at the end
   - Check for any error messages

2. **Verify the index was created**:
   ```bash
   python manage.py shell
   ```
   ```python
   from models.mongodb import db
   print(db.users.index_information())
   # Should show username_1 with collation
   ```

3. **Check for remaining duplicates**:
   ```bash
   python manage.py fix_username_case --dry-run
   ```

### MongoDB Connection Issues

If you see connection errors:

1. **Check that MongoDB is running**:
   ```bash
   sudo systemctl status mongod
   ```

2. **Verify connection in `.env` file**:
   ```bash
   cat .env | grep MONGO
   ```

3. **Test connection**:
   ```bash
   python manage.py shell
   ```
   ```python
   from models.mongodb import db
   print(db.users.count_documents({}))
   ```

### Need Help?

If you're still having issues:
1. Check Django logs for detailed error messages
2. Run the fix command again (it's safe to run multiple times)
3. Check the GitHub issues for similar problems

## 🎉 Success!

After applying the fix, you should be able to:
- ✅ Login with any case variation of your username
- ✅ See no duplicate key errors in the logs
- ✅ Create new accounts without issues
- ✅ Have a clean, normalized user database
