# NexaAI - AI-Powered 3D Model Generation

Django + HTMX application for text-to-3D model generation using Meshy.ai, LLM prompt refinement, and interactive 3D viewing.

## 🚀 Features

- **Text-to-3D Generation**: Convert text descriptions into high-quality 3D models
- **LLM Prompt Refinement**: Improve prompts with AI suggestions
- **Interactive 3D Viewer**: Three.js-powered 3D model viewer
- **Model History**: Browse and manage generated models
- **User Authentication**: Secure login system
- **HTMX Dynamic Updates**: No page reloads, smooth UX

## 🛠️ Tech Stack

**Backend:**
- Django 5.0
- Django REST Framework
- SQLite
- Python 3.10+

**Frontend:**
- Django Templates
- HTMX 1.9
- TailwindCSS (CDN)
- Three.js

**Services:**
- Meshy.ai (3D generation)
- OpenAI/LLM (prompt refinement)
- AWS S3 (file storage)

## 📋 Prerequisites

- Python 3.10 or higher
- pip (Python package manager)
- Virtual environment (recommended)

## 🔧 Installation

### 1. Clone Repository

```bash
git clone <repository-url>
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
# Django
DJANGO_SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Meshy.ai
MESHY_API_KEY=msy_your_api_key_here

# LLM (OpenAI or compatible)
LLM_API_KEY=your-llm-api-key
LLM_API_URL=https://api.openai.com/v1
LLM_MODEL=gpt-4

# AWS S3 (optional)
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

Or use the default admin account:
- Username: `admin`
- Password: `admin123`

### 7. Start Development Server

```bash
python manage.py runserver
```

### 8. Access Application

- **Homepage**: http://localhost:8000/
- **Generate**: http://localhost:8000/generate/
- **History**: http://localhost:8000/history/
- **Admin**: http://localhost:8000/admin/

## 📁 Project Structure

```
nexaai/
├── manage.py              # Django management
├── nexaai/               # Project settings
│   ├── settings.py       # Configuration
│   ├── urls.py           # URL routing
│   └── wsgi.py           # WSGI config
├── models/               # Main app
│   ├── models.py         # Database models
│   ├── views.py          # HTMX views
│   ├── urls.py           # App URLs
│   └── admin.py          # Admin config
├── services/             # Business logic
│   ├── meshy_client.py   # Meshy.ai integration
│   ├── prompt_refinement.py # LLM service
│   ├── storage.py        # S3 storage
│   └── notifications.py  # Notifications
├── templates/            # Django templates
│   ├── base.html
│   ├── home.html
│   ├── generate.html
│   ├── history.html
│   ├── viewer.html
│   ├── partials/
│   └── registration/
├── static/               # Static files
│   ├── css/
│   └── js/
└── requirements.txt      # Python dependencies
```

## 🎯 Usage

### Generate 3D Models

1. Navigate to `/generate/`
2. Enter a text description (e.g., "a modern coffee mug")
3. Optionally click "Refine with AI" to improve the prompt
4. Select art style and quality
5. Click "Generate 3D Model"
6. Wait 2-5 minutes for generation
7. View the model in the 3D viewer

### View Model History

1. Navigate to `/history/`
2. Browse all generated models
3. Filter by status (completed, processing, failed)
4. Click on a model to view in 3D viewer
5. Download files (GLB, OBJ, FBX, USDZ)

### Better Prompts

- Be specific about shape, size, and proportions
- Mention materials (wood, metal, plastic, etc.)
- Include style references (modern, vintage, minimalist)
- Use the "Refine with AI" button
- Start with Preview quality, then refine if needed

**Example Prompts:**
- "A modern coffee mug with geometric patterns, ceramic material, minimalist design"
- "A vintage wooden chair with carved details, Victorian style"
- "A futuristic robot toy, low-poly style, bright colors"

## 🚀 Production Deployment

### AWS EC2 Deployment

1. **Provision Ubuntu 20.04+ EC2 instance**

2. **Install dependencies**:
```bash
sudo apt update
sudo apt install python3-pip python3-venv nginx -y
```

3. **Clone and setup**:
```bash
git clone <repository-url>
cd nexaai
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

4. **Configure environment**:
```bash
nano .env  # Add production values
```

5. **Run migrations**:
```bash
python manage.py migrate
python manage.py collectstatic
python manage.py createsuperuser
```

6. **Set up Gunicorn**:
```bash
pip install gunicorn
gunicorn nexaai.wsgi:application --bind 0.0.0.0:8000
```

7. **Configure Nginx** (create `/etc/nginx/sites-available/nexaai`):
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /static/ {
        alias /path/to/nexaai/staticfiles/;
    }
}
```

8. **Enable site**:
```bash
sudo ln -s /etc/nginx/sites-available/nexaai /etc/nginx/sites-enabled/
sudo systemctl restart nginx
```

9. **Set up systemd service** (create `/etc/systemd/system/nexaai.service`):
```ini
[Unit]
Description=NexaAI Django Application
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/nexaai
Environment="PATH=/home/ubuntu/nexaai/venv/bin"
ExecStart=/home/ubuntu/nexaai/venv/bin/gunicorn nexaai.wsgi:application --bind 0.0.0.0:8000 --workers 3

[Install]
WantedBy=multi-user.target
```

10. **Start service**:
```bash
sudo systemctl daemon-reload
sudo systemctl start nexaai
sudo systemctl enable nexaai
```

## 🔑 API Keys Setup

### Meshy.ai

1. Sign up at https://www.meshy.ai
2. Navigate to Settings → API
3. Create API key
4. Add to `.env`: `MESHY_API_KEY=msy_...`

### OpenAI (for LLM)

1. Sign up at https://platform.openai.com
2. Create API key
3. Add to `.env`: `LLM_API_KEY=sk-...`

### AWS S3 (Optional)

1. Create S3 bucket in AWS Console
2. Create IAM user with S3 access
3. Add credentials to `.env`

## 🧪 Development

### Running Tests

```bash
python manage.py test
```

### Creating Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### Collecting Static Files

```bash
python manage.py collectstatic
```

## 📝 License

MIT License

## 🤝 Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Open Pull Request

## 📧 Support

For issues and questions:
- GitHub Issues: <repository-url>/issues
- Email: support@nexaai.com

## 🗺️ Roadmap

- [ ] Batch generation (multiple models at once)
- [ ] Model editing and refinement
- [ ] Public model gallery
- [ ] Model sharing and collaboration
- [ ] 3D printer integration
- [ ] Cost estimation
- [ ] Material selection

## 📜 Credits

- Meshy.ai for 3D generation API
- Three.js for 3D rendering
- HTMX for dynamic interactions
- TailwindCSS for styling
- Django community
