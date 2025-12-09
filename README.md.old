# NexaAI - AI-Powered 3D Model Generation

Manufacturing orchestration platform with AI-powered 3D model generation using Meshy.ai, printer management, and MongoDB storage.

## Features

- **Text-to-3D Generation** - Convert text prompts to 3D models using Meshy.ai
- **LLM Prompt Refinement** - Improve prompts with AI before generation
- **Four Quality Levels** - Preview (10k), Standard (30k), High (60k), Ultra (100k polygons)
- **Interactive 3D Viewer** - Three.js-powered GLB viewer with CORS proxy
- **Printer Management** - Manage Prusa and Snapmaker printers
- **Snapmaker Mode Switching** - Switch between 3D Print, CNC, and Laser modes
- **Print Job Tracking** - Track print history and status
- **MongoDB Storage** - All data stored in MongoDB (users, models, printers, jobs)
- **HTMX Dynamic Updates** - No page reloads, automatic status polling
- **Django + PyMongo** - Clean hybrid architecture

## Tech Stack

- **Backend**: Django 5.0, PyMongo 4.10
- **Frontend**: HTMX, TailwindCSS CDN, Three.js
- **Database**: MongoDB (all data)
- **3D Generation**: Meshy.ai API
- **LLM**: OpenAI-compatible API

## Quick Start

### Prerequisites

- Python 3.10+
- MongoDB (local or Atlas)
- Meshy.ai API key
- OpenAI API key (or compatible)

### 1. Clone Repository

\`\`\`bash
git clone https://github.com/NexaFood/nexaai.git
cd nexaai
\`\`\`

### 2. Create Virtual Environment

\`\`\`bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
\`\`\`

### 3. Install Dependencies

\`\`\`bash
pip install -r requirements.txt
\`\`\`

### 4. Configure Environment

Create \`.env\` file:

\`\`\`env
# Django
DJANGO_SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# MongoDB
MONGO_URI=mongodb://localhost:27017/
MONGO_DB_NAME=nexaai

# Meshy.ai API
MESHY_API_KEY=msy_your_key_here

# LLM Configuration
LLM_API_KEY=your_openai_key_here
LLM_API_URL=https://api.openai.com/v1
LLM_MODEL=gpt-4
\`\`\`

### 5. Run Django Migrations (for sessions only)

\`\`\`bash
python manage.py migrate
\`\`\`

### 6. Create Superuser in MongoDB

\`\`\`bash
python manage.py createsuperuser_mongo
\`\`\`

### 7. Start Server

\`\`\`bash
python manage.py runserver
\`\`\`

Visit: **http://localhost:8000/**

## User Management Commands

### Create Superuser
\`\`\`bash
python manage.py createsuperuser_mongo
\`\`\`

### List All Users
\`\`\`bash
python manage.py listusers_mongo
\`\`\`

### Delete User
\`\`\`bash
python manage.py deleteuser_mongo <username>
\`\`\`

## MongoDB Collections

Collections are created automatically:

- **users** - User accounts
- **models_3d** - 3D model metadata
- **printers** - 3D printers and CNC machines
- **print_jobs** - Print history
- **generation_jobs** - Meshy.ai tasks

## Documentation

- **MONGODB_SETUP.md** - Detailed MongoDB setup guide
- **DEPLOYMENT.md** - Production deployment instructions

## License

MIT License

## Support

- GitHub: https://github.com/NexaFood/nexaai
- Issues: https://github.com/NexaFood/nexaai/issues
