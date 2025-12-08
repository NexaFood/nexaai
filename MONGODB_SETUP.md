# MongoDB Setup Instructions (PyMongo)

## Architecture

NexaAI uses a **hybrid database approach**:

- **SQLite** - Django authentication, sessions, admin panel
- **PyMongo** - All application data (models, printers, jobs)

This gives you the best of both worlds:
- Django's built-in auth system works perfectly
- Full MongoDB power and flexibility for your data
- No djongo compatibility issues

## Prerequisites

- MongoDB server (local or MongoDB Atlas)
- Python 3.10+
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

### 3. Run Django Migrations (for auth/sessions only)

```bash
python manage.py migrate
```

This creates SQLite tables for Django's auth system only.

### 4. Create Superuser

```bash
python manage.py createsuperuser
```

### 5. Start Server

```bash
python manage.py runserver
```

**That's it!** MongoDB collections are created automatically when you first use the app.

## MongoDB Collections

The following collections are created automatically:

- **models_3d** - 3D model metadata
  - user_id, prompt, status, glb_url, etc.
  
- **printers** - 3D printers and CNC machines
  - user_id, name, type, build_volume, status, current_mode
  
- **print_jobs** - Print history and tracking
  - user_id, model_id, printer_id, status, material, duration
  
- **generation_jobs** - Meshy.ai generation tasks
  - model_id, meshy_task_id, status, progress

## How It Works

### MongoDB Connection

The `models/mongodb.py` module provides a singleton MongoDB connection:

```python
from models.mongodb import db

# Access collections
models = db.models.find({'user_id': user_id})
printers = db.printers.find({'status': 'idle'})
```

### Document Schemas

The `models/schemas.py` module defines document structures:

```python
from models.schemas import Model3DSchema, PrinterSchema

# Create documents
model_doc = Model3DSchema.create(
    user_id=1,
    prompt="a modern coffee mug",
    quality="standard"
)

printer_doc = PrinterSchema.create(
    user_id=1,
    name="My Prusa MK4",
    printer_type="prusa",
    model="Prusa MK4",
    build_volume_x=250,
    build_volume_y=210,
    build_volume_z=220
)
```

### Views

All views in `models/views.py` use PyMongo directly:

```python
from models.mongodb import db, to_object_id, doc_to_dict

# Find documents
model = db.models.find_one({'_id': to_object_id(model_id)})

# Insert documents
result = db.models.insert_one(model_doc)
model_id = result.inserted_id

# Update documents
db.models.update_one(
    {'_id': model_id},
    {'$set': {'status': 'completed'}}
)

# Delete documents
db.models.delete_one({'_id': model_id})
```

## Printer Management

### Add Printers

Navigate to: **http://localhost:8000/printers/**

Or click "Printers" in the navigation menu.

### Printer Types

**Prusa (3D Printing Only)**
- Name, model, serial number
- IP address for network printers
- Build volume (X, Y, Z in mm)
- Status: idle, printing, offline, error

**Snapmaker (Multi-Mode)**
- All Prusa features plus:
- Current mode: 3D Print, CNC, or Laser
- Mode switching capability

### Example Printers

**Prusa MK4:**
```
Name: My Prusa MK4
Type: Prusa
Model: Prusa MK4
Build Volume: 250 × 210 × 220 mm
Status: Idle
```

**Snapmaker 2.0 A350:**
```
Name: My Snapmaker
Type: Snapmaker
Model: Snapmaker 2.0 A350
Build Volume: 320 × 350 × 330 mm
Status: Idle
Current Mode: 3D Printing
```

## Troubleshooting

### MongoDB Connection Error

If you see connection errors:

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

### No Collections Visible

Collections are created automatically when you first insert data:
1. Generate a 3D model → creates `models_3d` and `generation_jobs`
2. Add a printer → creates `printers`
3. Create a print job → creates `print_jobs`

### Import Errors

If you see `ImportError: cannot import name 'db'`:

1. **Check MongoDB is accessible** from your machine
2. **Verify `.env` file** has correct `MONGO_URI`
3. **Restart Django server**

### Django Auth Not Working

Django auth uses SQLite, not MongoDB:

```bash
# Run migrations for Django auth
python manage.py migrate

# Create superuser
python manage.py createsuperuser
```

## Advantages Over djongo

✅ **No compatibility issues** - Works with any Django version  
✅ **Full MongoDB features** - Aggregation, indexing, transactions  
✅ **Better performance** - Direct PyMongo is faster  
✅ **Easier debugging** - Standard PyMongo queries  
✅ **More flexible** - Mix SQL and NoSQL as needed  

## Data Structure

### Model3D Document
```json
{
  "_id": ObjectId("..."),
  "user_id": 1,
  "prompt": "a modern coffee mug",
  "refined_prompt": "...",
  "quality": "standard",
  "polygon_count": 30000,
  "status": "completed",
  "glb_url": "https://...",
  "thumbnail_url": "https://...",
  "created_at": ISODate("..."),
  "completed_at": ISODate("...")
}
```

### Printer Document
```json
{
  "_id": ObjectId("..."),
  "user_id": 1,
  "name": "My Prusa MK4",
  "printer_type": "prusa",
  "model": "Prusa MK4",
  "build_volume_x": 250,
  "build_volume_y": 210,
  "build_volume_z": 220,
  "status": "idle",
  "ip_address": "192.168.1.100",
  "created_at": ISODate("..."),
  "updated_at": ISODate("...")
}
```

## Next Steps

- Add your printers at `/printers/add`
- Generate 3D models at `/generate/`
- View model history at `/history/`
- Explore MongoDB collections with MongoDB Compass

## Support

For issues or questions:
- Check GitHub Issues: https://github.com/NexaFood/nexaai/issues
- Review PyMongo docs: https://pymongo.readthedocs.io/
