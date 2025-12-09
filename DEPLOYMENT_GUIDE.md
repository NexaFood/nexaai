# CadQuery Integration Deployment Guide

## Quick Start

This guide will help you deploy the CadQuery-integrated NexaAI application.

## Prerequisites

- Ubuntu 22.04 or similar Linux distribution
- Python 3.11
- MongoDB installed and running
- OpenAI API key
- Git access to the repository

## Step-by-Step Deployment

### 1. Clone the Repository

```bash
cd /home/ubuntu
git clone https://github.com/NexaFood/nexaai.git
cd nexaai
```

### 2. Create Virtual Environment with CadQuery

```bash
# Create virtual environment
python3.11 -m venv venv_cadquery

# Activate virtual environment
source venv_cadquery/bin/activate

# Install Django and dependencies
pip install -r requirements.txt

# Install CadQuery
pip install cadquery==2.4.0
```

### 3. Configure Environment Variables

Create a `.env` file:

```bash
cat > .env << 'EOF'
# Django Settings
SECRET_KEY=your-secret-key-here
DEBUG=False
ALLOWED_HOSTS=your-domain.com,localhost,127.0.0.1

# MongoDB
MONGO_URI=mongodb://localhost:27017/
MONGO_DB_NAME=nexaai

# OpenAI API
OPENAI_API_KEY=your-openai-api-key-here

# AWS S3 (optional, for Meshy file storage)
AWS_ACCESS_KEY_ID=your-aws-key
AWS_SECRET_ACCESS_KEY=your-aws-secret
AWS_STORAGE_BUCKET_NAME=your-bucket-name
AWS_S3_REGION_NAME=us-east-1

# Meshy API (optional, for artistic 3D generation)
MESHY_API_KEY=your-meshy-api-key
EOF
```

### 4. Start MongoDB

```bash
# If using systemd
sudo systemctl start mongod
sudo systemctl enable mongod

# Or manually
mkdir -p /home/ubuntu/mongodb_data
mongod --dbpath /home/ubuntu/mongodb_data --fork --logpath /home/ubuntu/mongodb.log
```

### 5. Create Media Directory

```bash
mkdir -p /home/ubuntu/nexaai/media/cadquery_models
chmod 755 /home/ubuntu/nexaai/media/cadquery_models
```

### 6. Run Django Migrations (if any)

```bash
source venv_cadquery/bin/activate
python manage.py migrate
```

### 7. Create Superuser (Optional)

```bash
# Note: This uses MongoDB, not Django's default User model
# You may need to create users through the signup page
```

### 8. Test the Server

```bash
# Development mode
source venv_cadquery/bin/activate
python manage.py runserver 0.0.0.0:8000
```

Visit: `http://your-server-ip:8000`

### 9. Production Deployment with Gunicorn

```bash
# Install Gunicorn (already in requirements.txt)
source venv_cadquery/bin/activate

# Test Gunicorn
gunicorn nexaai.wsgi:application --bind 0.0.0.0:8000

# Create systemd service
sudo nano /etc/systemd/system/nexaai.service
```

Add this content:

```ini
[Unit]
Description=NexaAI Django Application
After=network.target

[Service]
Type=notify
User=ubuntu
Group=ubuntu
WorkingDirectory=/home/ubuntu/nexaai
Environment="PATH=/home/ubuntu/nexaai/venv_cadquery/bin"
ExecStart=/home/ubuntu/nexaai/venv_cadquery/bin/gunicorn \
    --workers 4 \
    --bind 0.0.0.0:8000 \
    --timeout 300 \
    --access-logfile /var/log/nexaai/access.log \
    --error-logfile /var/log/nexaai/error.log \
    nexaai.wsgi:application

[Install]
WantedBy=multi-user.target
```

Create log directory:

```bash
sudo mkdir -p /var/log/nexaai
sudo chown ubuntu:ubuntu /var/log/nexaai
```

Start the service:

```bash
sudo systemctl daemon-reload
sudo systemctl start nexaai
sudo systemctl enable nexaai
sudo systemctl status nexaai
```

### 10. Configure NGINX (Recommended)

```bash
sudo apt install nginx

sudo nano /etc/nginx/sites-available/nexaai
```

Add this content:

```nginx
server {
    listen 80;
    server_name your-domain.com;

    client_max_body_size 100M;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 300s;
        proxy_connect_timeout 300s;
    }

    location /media/ {
        alias /home/ubuntu/nexaai/media/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    location /static/ {
        alias /home/ubuntu/nexaai/static/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
}
```

Enable the site:

```bash
sudo ln -s /etc/nginx/sites-available/nexaai /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 11. Set Up SSL with Let's Encrypt (Optional)

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

## Verification

### Test CadQuery Generation

1. Visit `http://your-domain.com/design/projects/`
2. Create a new design project (e.g., "a simple mounting bracket")
3. Approve the design concept
4. Approve the part breakdown
5. Select "CadQuery (Recommended)"
6. Click "Generate CAD Model" for a part
7. Wait 5-10 seconds
8. Download STEP and STL files
9. View the generated Python code

### Check Logs

```bash
# Django logs (if using systemd)
sudo journalctl -u nexaai -f

# Or custom log files
tail -f /var/log/nexaai/error.log
tail -f /var/log/nexaai/access.log

# NGINX logs
sudo tail -f /var/nginx/error.log
sudo tail -f /var/nginx/access.log
```

## Troubleshooting

### Issue: CadQuery Import Error

```bash
# Verify CadQuery is installed
source venv_cadquery/bin/activate
python -c "import cadquery; print(cadquery.__version__)"
```

### Issue: MongoDB Connection Failed

```bash
# Check if MongoDB is running
sudo systemctl status mongod

# Or check process
ps aux | grep mongod

# Test connection
mongo --eval "db.adminCommand('ping')"
```

### Issue: Permission Denied on Media Files

```bash
# Fix permissions
sudo chown -R ubuntu:ubuntu /home/ubuntu/nexaai/media
chmod -R 755 /home/ubuntu/nexaai/media
```

### Issue: Gunicorn Timeout

```bash
# Increase timeout in systemd service
# Edit /etc/systemd/system/nexaai.service
# Add: --timeout 600

sudo systemctl daemon-reload
sudo systemctl restart nexaai
```

## Monitoring

### Check Service Status

```bash
sudo systemctl status nexaai
sudo systemctl status nginx
sudo systemctl status mongod
```

### Monitor Resource Usage

```bash
# CPU and memory
htop

# Disk space
df -h

# MongoDB stats
mongo nexaai --eval "db.stats()"
```

## Backup

### Backup MongoDB

```bash
# Create backup directory
mkdir -p /home/ubuntu/backups

# Backup database
mongodump --db nexaai --out /home/ubuntu/backups/mongo-$(date +%Y%m%d)

# Restore database
mongorestore --db nexaai /home/ubuntu/backups/mongo-20241209/nexaai
```

### Backup Media Files

```bash
# Backup CAD files
tar -czf /home/ubuntu/backups/media-$(date +%Y%m%d).tar.gz /home/ubuntu/nexaai/media
```

## Updates

### Pull Latest Changes

```bash
cd /home/ubuntu/nexaai
git pull origin master

# Activate virtual environment
source venv_cadquery/bin/activate

# Install any new dependencies
pip install -r requirements.txt

# Restart service
sudo systemctl restart nexaai
```

## Performance Optimization

### Recommended Settings

- **Workers**: 2-4 per CPU core
- **Timeout**: 300-600 seconds (for CAD generation)
- **MongoDB**: Enable indexes for faster queries
- **NGINX**: Enable gzip compression
- **Static Files**: Use CDN for production

### MongoDB Indexes

```javascript
// Connect to MongoDB
mongo nexaai

// Create indexes
db.design_projects.createIndex({ "user_id": 1, "created_at": -1 })
db.part_breakdowns.createIndex({ "project_id": 1 })
db.models.createIndex({ "user_id": 1, "created_at": -1 })
```

## Security Checklist

- [ ] Set DEBUG=False in production
- [ ] Use strong SECRET_KEY
- [ ] Configure ALLOWED_HOSTS properly
- [ ] Set up SSL/TLS with Let's Encrypt
- [ ] Enable firewall (ufw)
- [ ] Restrict MongoDB access
- [ ] Use environment variables for secrets
- [ ] Regular security updates
- [ ] Monitor logs for suspicious activity

## Support

For issues or questions:
- GitHub Issues: https://github.com/NexaFood/nexaai/issues
- Documentation: See CADQUERY_DJANGO_INTEGRATION.md
- CadQuery Docs: https://cadquery.readthedocs.io/

## License

Same as parent project (NexaAI).
