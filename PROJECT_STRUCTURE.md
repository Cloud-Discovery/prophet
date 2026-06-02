# Project Structure

This document describes the structure of the Prophet project.

## Directory Overview

```
prophet/
├── .github/              # GitHub configuration and templates
│   ├── ISSUE_TEMPLATE/   # Issue templates
│   ├── PULL_REQUEST_TEMPLATE.md
│   └── workflows/        # GitHub Actions workflows
├── api/                  # Flask API endpoints
├── docker/               # Docker deployment files
│   ├── backend/         # Backend container configuration
│   └── frontend/        # Frontend container configuration
├── docs/                 # Documentation
│   ├── images/          # Documentation images
│   └── README_EN.md     # English README
├── frontend/             # Vue.js frontend application
│   ├── src/             # Source code
│   │   ├── api/         # API client
│   │   ├── components/  # Vue components
│   │   ├── views/       # Page views
│   │   ├── stores/      # Pinia stores
│   │   └── router/      # Vue Router
│   └── public/          # Static assets
├── models/               # SQLAlchemy database models
├── prophet/              # Core Prophet library
│   ├── collector/       # Host collection modules
│   ├── parser/          # Data parsing modules
│   ├── scanner/         # Network scanning
│   ├── report/          # Report generation
│   └── cloud/           # Cloud platform integrations
├── services/             # Business logic services
├── tasks/                # Celery tasks
├── utils/                # Utility functions
├── tools/                # Development and deployment tools
├── migrations/           # Database migrations
└── examples/             # Example files and samples
```

## Key Files

### Root Level

- `README.md` - Main project documentation (Chinese)
- `CHANGELOG.md` - Version history and changes
- `CONTRIBUTING.md` - Contribution guidelines
- `CODE_OF_CONDUCT.md` - Code of conduct
- `SECURITY.md` - Security policy
- `LICENSE` - License file (Mulan PubL v2)
- `AUTHORS` - List of contributors
- `requirements.txt` - Python dependencies
- `env.example` - Environment variables template
- `docker-compose.yml` - Docker Compose configuration
- `Dockerfile.backend` - Backend container image
- `Dockerfile.frontend` - Frontend container image

### Backend Structure

- `app.py` - Flask application entry point
- `config.py` - Configuration management
- `db.py` - Database initialization
- `celery_app.py` - Celery application configuration
- `celery_worker.py` - Celery worker entry point

### Frontend Structure

- `frontend/package.json` - Node.js dependencies
- `frontend/vite.config.ts` - Vite build configuration
- `frontend/src/main.ts` - Application entry point
- `frontend/src/App.vue` - Root component

## Module Descriptions

### API (`api/`)

RESTful API endpoints organized by resource:

- `auth.py` - Authentication endpoints
- `hosts.py` - Host management endpoints
- `applications.py` - Application management endpoints
- `scanner.py` - Scanning task endpoints
- `tags.py` - Tag management endpoints
- `virtualization.py` - Virtualization platform endpoints

### Models (`models/`)

SQLAlchemy ORM models:

- `user.py` - User model
- `host.py` - Host model
- `application.py` - Application model
- `platform.py` - Virtualization platform model
- `task.py` - Task model

### Services (`services/`)

Business logic layer:

- `collector_service.py` - Host collection service
- `scanner_service.py` - Network scanning service
- `platform_collector_service.py` - Platform collection service
- `vmware_sync_service.py` - VMware synchronization service

### Tasks (`tasks/`)

Celery asynchronous tasks:

- `scanner.py` - Network scanning tasks
- `collector.py` - Host collection tasks

### Prophet Core (`prophet/`)

Core library modules:

- `collector/` - Host collection implementations (Linux, Windows, VMware)
- `parser/` - Data parsing and transformation
- `scanner/` - Network scanning functionality
- `report/` - Report generation
- `cloud/` - Cloud platform integrations (OpenStack, etc.)

## Data Directories

- `data/` - Database files (created at runtime)
- `logs/` - Log files (created at runtime)
- `uploads/` - Uploaded files (created at runtime)

## Configuration Files

- `.env` - Environment variables (not in repo, use `env.example`)
- `.gitignore` - Git ignore rules
- `.dockerignore` - Docker build ignore rules
- `setup.py` - Python package setup
- `setup.cfg` - Package configuration
- `tox.ini` - Testing configuration

## Documentation

- `README.md` - Main documentation (Chinese)
- `docs/README_EN.md` - English documentation
- `docker/README.md` - Docker deployment guide
- `PROJECT_STRUCTURE.md` - This file

## Development Files

- `.github/` - GitHub templates and workflows
- `CONTRIBUTING.md` - Contribution guidelines
- `CODE_OF_CONDUCT.md` - Community guidelines
- `SECURITY.md` - Security reporting
