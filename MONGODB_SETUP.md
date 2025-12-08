# MongoDB Setup Instructions

## What Changed

NexaAI now uses **MongoDB** instead of SQLite for all data storage using **djongo5**.

## Prerequisites

- MongoDB server (local or MongoDB Atlas)
- Python 3.11+
- Virtual environment

## Setup Steps

### 1. Install Dependencies

```bash
cd /path/to/nexaai
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure MongoDB Connection

Update your `.env` file with MongoDB connection details:

```env
# MongoDB Configuration
MONGO_URI=mongodb://localhost:27017/
# Or for MongoDB Atlas:
# MONGO_URI=mongodb+srv://username:password@cluster.mongodb.net/

MONGO_DB_NAME=nexaai
```

### 3. Run Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

This will create the following MongoDB collections:
- `users` - User accounts
- `models_3d` - 3D model metadata
- `generation_jobs` - Meshy.ai generation tasks
- `printers` - 3D printers and CNC machines
- `print_jobs` - Print history and tracking

### 4. Create Superuser

```bash
python manage.py createsuperuser
```

### 5. Start Server

```bash
python manage.py runserver
```

## New Features

### Printer Management

- **Add/Edit/Delete Printers** - Manage your 3D printers
- **Prusa Support** - Standard 3D printing
- **Snapmaker Support** - Multi-mode (3D Print / CNC / Laser)
- **Mode Switching** - Change Snapmaker modes on the fly
- **Build Volume Tracking** - Ensure models fit your printer
- **Status Monitoring** - Track printer status (idle, printing, offline)
- **Network Printers** - Store IP addresses for network-connected printers

### Access Printer Management

Navigate to: **http://localhost:8000/printers/**

Or click "Printers" in the navigation menu.

## Printer Models

### Printer Fields

- **Name** - Custom name for your printer
- **Type** - Prusa or Snapmaker
- **Model** - Printer model (e.g., "Prusa MK4", "Snapmaker 2.0 A350")
- **Serial Number** - Optional serial number
- **IP Address** - Optional network IP
- **Build Volume** - X, Y, Z dimensions in mm
- **Status** - idle, printing, offline, error
- **Current Mode** - (Snapmaker only) 3D Print, CNC, or Laser

### PrintJob Fields

- **Model** - Link to 3D model
- **Printer** - Link to printer
- **Status** - queued, printing, completed, failed, cancelled
- **Material** - e.g., PLA, ABS, PETG
- **Layer Height** - mm
- **Infill Percentage** - 0-100%
- **Duration** - Estimated and actual time

## Troubleshooting

### MongoDB Connection Error

If you see `ServerSelectionTimeoutError`:

1. **Check MongoDB is running**:
   ```bash
   # On Linux/Mac
   sudo systemctl status mongod
   
   # On Windows
   net start MongoDB
   ```

2. **Verify connection string** in `.env`

3. **For MongoDB Atlas**:
   - Whitelist your IP address
   - Check username/password
   - Ensure cluster is running

### Migration Errors

If migrations fail:

1. **Delete old migrations**:
   ```bash
   rm -rf models/migrations
   mkdir models/migrations
   touch models/migrations/__init__.py
   ```

2. **Run migrations again**:
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

### djongo5 Issues

If you encounter djongo5 errors:

1. **Check Python version** (must be 3.11+)
2. **Reinstall dependencies**:
   ```bash
   pip uninstall djongo5 pymongo
   pip install djongo5==1.3.9 pymongo>=4.0
   ```

## Data Migration (Optional)

If you have existing data in SQLite and want to migrate to MongoDB:

1. **Export data from SQLite** (before switching to MongoDB)
2. **Switch to MongoDB** (follow setup steps above)
3. **Import data** using Django management commands or scripts

Contact support if you need help with data migration.

## Next Steps

- Add your printers at `/printers/add`
- Generate 3D models at `/generate/`
- View model history at `/history/`
- Assign models to compatible printers

## Support

For issues or questions:
- Check GitHub Issues: https://github.com/NexaFood/nexaai/issues
- Review Django + MongoDB docs: https://djongo.readthedocs.io/
