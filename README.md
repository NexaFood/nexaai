# NexaAI - AI CAD Designer

AI-powered parametric CAD generation from natural language descriptions using CadQuery.

## Overview

NexaAI is an AI-powered CAD design system that generates precise, parametric CAD models from natural language descriptions. It uses OpenAI GPT-4 to generate CadQuery Python code, which is then executed to create manufacturing-ready STEP and STL files.

## Features

- **Natural Language to CAD**: Describe your design in plain English
- **3-Stage Workflow**: Design Concept → Part Breakdown → CAD Generation
- **Fast Generation**: 5-10 seconds per part
- **Manufacturing-Ready**: Export STEP (for CAD software) and STL (for 3D printing) files
- **Editable Code**: View and modify the generated CadQuery Python code
- **Multi-Part Support**: Automatically splits complex designs into manufacturable parts
- **AI-Powered Analysis**: Intelligent part breakdown with manufacturing recommendations

## Technology Stack

- **Backend**: Django 5.0.1 + Python 3.11
- **Database**: MongoDB
- **CAD Generation**: CadQuery 2.4.0
- **AI**: OpenAI GPT-4
- **Frontend**: HTMX + Tailwind CSS
- **Authentication**: Session-based with MongoDB

## Quick Start

### Prerequisites

- Python 3.11
- MongoDB
- OpenAI API key

### Installation

1. Clone the repository:
```bash
git clone https://github.com/NexaFood/nexaai.git
cd nexaai
```

2. Create virtual environment with CadQuery:
```bash
python3.11 -m venv venv_cadquery
source venv_cadquery/bin/activate
pip install -r requirements.txt
pip install cadquery==2.4.0
```

3. Configure environment variables:
```bash
# Create .env file with:
OPENAI_API_KEY=your-openai-api-key
MONGO_URI=mongodb://localhost:27017/
MONGO_DB_NAME=nexaai
SECRET_KEY=your-secret-key
```

4. Start MongoDB and run server:
```bash
sudo systemctl start mongod
python manage.py runserver
```

5. Visit `http://localhost:8000`

## Usage

### 3-Stage Design Workflow

1. **Design Concept**: Describe your design → AI generates concept
2. **Part Breakdown**: AI splits into parts → Review and approve
3. **CAD Generation**: Generate STEP/STL files → Download and use

See `CADQUERY_DJANGO_INTEGRATION.md` for detailed usage guide.

## Documentation

- **README.md** (this file) - Quick start guide
- **CADQUERY_DJANGO_INTEGRATION.md** - Technical integration details
- **DEPLOYMENT_GUIDE.md** - Production deployment instructions
- **AI_CAD_SYSTEM_SUMMARY.md** - CadQuery AI system documentation

## Project Structure

```
nexaai/
├── models/                    # Django app
│   ├── cadquery_views.py     # CadQuery generation
│   ├── design_views.py       # Design workflow
│   └── design_schemas.py     # MongoDB schemas
├── services/                  # Business logic
│   ├── cadquery_agent.py     # AI code generation
│   └── cadquery_executor.py  # Code execution
├── templates/                 # HTML templates
└── media/cadquery_models/    # Generated files
```

## License

Proprietary - NexaFood

## Support

GitHub Issues: https://github.com/NexaFood/nexaai/issues

---

**NexaAI** - Transform ideas into CAD models with AI
