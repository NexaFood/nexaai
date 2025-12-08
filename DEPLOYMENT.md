# NexaAI Deployment Guide

## Quick Start

### 1. Clone Repository

```bash
git clone https://github.com/NexaFood/nexaai.git
cd nexaai
```

### 2. Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Create a `.env` file in the project root:

```bash
DJANGO_SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Meshy.ai API
MESHY_API_KEY=msy_your_api_key_here

# LLM Configuration (OpenAI or compatible)
LLM_API_KEY=your-llm-api-key
LLM_API_URL=https://api.openai.com/v1
LLM_MODEL=gpt-4

# AWS S3 Configuration (optional)
AWS_ACCESS_KEY_ID=your-aws-access-key
AWS_SECRET_ACCESS_KEY=your-aws-secret-key
AWS_STORAGE_BUCKET_NAME=your-bucket-name
AWS_S3_REGION_NAME=us-east-1

# Owner
OWNER_EMAIL=admin@example.com
OWNER_NAME=Admin
```

### 5. Run Migrations

```bash
python manage.py migrate
```

### 6. Create Superuser

```bash
python manage.py createsuperuser
```

### 7. Start Services

**Terminal 1 - Django Server:**
```bash
python manage.py runserver
```

**Terminal 2 - Background Worker:**
```bash
python manage.py check_generation_status --loop --interval 10
```

### 8. Access Application

- **Homepage**: http://localhost:8000/
- **Generate**: http://localhost:8000/generate/
- **History**: http://localhost:8000/history/
- **Admin**: http://localhost:8000/admin/

## Background Worker

The background worker checks Meshy.ai API for generation status updates.

### Run as Background Service

**Option 1: Using nohup**
```bash
nohup python manage.py check_generation_status --loop --interval 10 > worker.log 2>&1 &
```

**Option 2: Using systemd (Production)**

Create `/etc/systemd/system/nexaai-worker.service`:

```ini
[Unit]
Description=NexaAI Background Worker
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/path/to/nexaai
Environment="PATH=/path/to/nexaai/venv/bin"
ExecStart=/path/to/nexaai/venv/bin/python manage.py check_generation_status --loop --interval 10

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl start nexaai-worker
sudo systemctl enable nexaai-worker
```

## Production Deployment (AWS EC2)

### 1. Install System Dependencies

```bash
sudo apt update
sudo apt install python3-pip python3-venv nginx supervisor -y
```

### 2. Clone and Setup

```bash
cd /home/ubuntu
git clone https://github.com/NexaFood/nexaai.git
cd nexaai
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install gunicorn
```

### 3. Configure Environment

```bash
nano .env  # Add production values
```

### 4. Run Migrations

```bash
python manage.py migrate
python manage.py collectstatic
python manage.py createsuperuser
```

### 5. Configure Gunicorn

Create `/etc/supervisor/conf.d/nexaai.conf`:

```ini
[program:nexaai]
command=/home/ubuntu/nexaai/venv/bin/gunicorn nexaai.wsgi:application --bind 0.0.0.0:8000 --workers 3
directory=/home/ubuntu/nexaai
user=ubuntu
autostart=true
autorestart=true
stderr_logfile=/var/log/nexaai/gunicorn.err.log
stdout_logfile=/var/log/nexaai/gunicorn.out.log

[program:nexaai-worker]
command=/home/ubuntu/nexaai/venv/bin/python manage.py check_generation_status --loop --interval 10
directory=/home/ubuntu/nexaai
user=ubuntu
autostart=true
autorestart=true
stderr_logfile=/var/log/nexaai/worker.err.log
stdout_logfile=/var/log/nexaai/worker.out.log
```

Create log directory:
```bash
sudo mkdir -p /var/log/nexaai
sudo chown ubuntu:ubuntu /var/log/nexaai
```

Start services:
```bash
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start nexaai
sudo supervisorctl start nexaai-worker
```

### 6. Configure Nginx

Create `/etc/nginx/sites-available/nexaai`:

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static/ {
        alias /home/ubuntu/nexaai/staticfiles/;
    }

    location /media/ {
        alias /home/ubuntu/nexaai/media/;
    }
}
```

Enable site:
```bash
sudo ln -s /etc/nginx/sites-available/nexaai /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 7. SSL with Let's Encrypt

```bash
sudo apt install certbot python3-certbot-nginx -y
sudo certbot --nginx -d your-domain.com
```

## Monitoring

### Check Worker Status

```bash
# If using supervisor
sudo supervisorctl status nexaai-worker

# If using systemd
sudo systemctl status nexaai-worker

# View logs
tail -f /var/log/nexaai/worker.out.log
```

### Check Django Server Status

```bash
sudo supervisorctl status nexaai
tail -f /var/log/nexaai/gunicorn.out.log
```

## Troubleshooting

### Worker Not Updating Status

1. Check worker is running:
   ```bash
   ps aux | grep check_generation_status
   ```

2. Check logs for errors:
   ```bash
   tail -f /var/log/nexaai/worker.err.log
   ```

3. Verify Meshy.ai API key is correct:
   ```bash
   python manage.py shell
   >>> from django.conf import settings
   >>> print(settings.MESHY_API_KEY)
   ```

### Models Stuck in "Processing"

1. Manually check status:
   ```bash
   python manage.py check_generation_status
   ```

2. Check Meshy.ai API directly:
   ```bash
   curl -H "Authorization: Bearer YOUR_API_KEY" \
        https://api.meshy.ai/v1/text-to-3d/TASK_ID
   ```

### Database Issues

```bash
# Reset database
rm db.sqlite3
python manage.py migrate
python manage.py createsuperuser
```

## Updating

```bash
cd /home/ubuntu/nexaai
git pull origin master
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
sudo supervisorctl restart nexaai
sudo supervisorctl restart nexaai-worker
```
