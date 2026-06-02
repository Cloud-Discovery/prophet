<p align="center"><a href="https://oneprocloud.com"><img src="./images/prophet-logo.png" alt="Prophet" width="300" /></a></p>
<h3 align="center">Automated Resource Collection and Analysis Toolset for Cloud Migration and Disaster Recovery</h3>

<p align="center">
  <a href="https://shields.io/github/downloads/Cloud-Discovery/prophet/total"><img src="https://shields.io/github/downloads/Cloud-Discovery/prophet/total" alt=" release"></a>
  <a href="https://github.com/Cloud-Discovery/prophet"><img src="https://img.shields.io/github/stars/Cloud-Discovery/prophet?color=%231890FF&style=flat-square" alt="Stars"></a>
</p>

---

- [中文](../README.md)

## Table of Contents

- [Project Overview](#project-overview)
- [Key Features](#key-features)
- [Installation](#installation)
  - [Docker Compose Deployment (Recommended)](#docker-compose-deployment-recommended)
  - [Source Code Installation](#source-code-installation)
- [Usage Guide](#usage-guide)
  - [Web Interface](#web-interface)
  - [Command Line Tools](#command-line-tools)
- [Project Structure](#project-structure)
- [Contributing](#contributing)
- [Security Policy](#security-policy)
- [Contributors](#contributors)
- [License](#license)

## Project Overview

Prophet is an automated resource collection, analysis, and management toolset designed for cloud migration and disaster recovery technical research. The project provides a modern web interface and powerful command-line tools, supporting comprehensive collection and analysis of physical machines and VMware environments, helping users quickly understand source infrastructure conditions and ensure the feasibility of migration and disaster recovery plans.

### Core Value

- **Automated Collection**: Automatically collect detailed host information through multiple protocols (nmap, Ansible, WMI, VMware API)
- **Visual Analysis**: Provide an intuitive web interface with application topology visualization and management
- **Data Desensitization**: Automatically remove sensitive information to ensure data security
- **Containerized Deployment**: One-click deployment, ready to use, reducing environment dependencies

### Use Cases

- Pre-migration research: Comprehensive understanding of source infrastructure to develop migration plans
- Disaster recovery planning: Assess disaster recovery feasibility and predict data transfer time
- Infrastructure management: Unified management of hosts, applications, and dependencies
- Technical documentation generation: Automatically generate technical research reports

## Key Features

### Web Interface Features

- **Host Management**: View, search, and manage collected host information
- **Application Management**: Create applications and organize business topology and host dependencies through visual canvas
- **Scan Tasks**: Create and manage network scan tasks to discover hosts in batches
- **Virtualization Platforms**: Manage VMware platforms and virtual machine information
- **Tag Management**: Add tags to hosts for easy classification
- **Data Import/Export**: Support batch import of host data and export of collection results

### Command Line Features

- **Network Scanning**: Scan active hosts in network segments using nmap
- **Detailed Information Collection**:
  - Collect virtual machine and ESXi host information via VMware API
  - Collect detailed Linux host information via Ansible
  - Collect Windows host information via Windows WMI interface
- **Data Analysis**: Analyze collection results and generate technical research reports
- **Data Packaging**: Package and compress collection results with automatic desensitization

## Installation

### Docker Compose Deployment (Recommended)

We recommend using Docker Compose for deployment, which is simple, fast, and requires no complex environment configuration.

#### Prerequisites

- Docker >= 20.10
- Docker Compose >= 2.0

#### Quick Start

1. **Clone the repository**

```bash
git clone https://github.com/Cloud-Discovery/prophet
cd prophet
```

2. **Configure environment variables (optional)**

Copy the environment variable example file and modify it:

```bash
cp env.example .env
```

Edit the `.env` file and set necessary keys:

```bash
# Required security keys (must be changed)
SECRET_KEY=your-secret-key-here
JWT_SECRET_KEY=your-jwt-secret-key-here
ENCRYPTION_KEY=your-encryption-key-here
```

3. **Start services**

```bash
# Build and start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Check service status
docker-compose ps
```

4. **Access the application**

- **Web Interface**: http://localhost
- **API Health Check**: http://localhost:5000/api/v1/health

#### Service Description

- **backend**: Backend service container (port 5000)
  - Flask REST API
  - Celery Worker (async task processing)
  - Redis (message queue and cache)
- **frontend**: Frontend service container (port 80)
  - Nginx static file service
  - Automatic API request proxying

#### Data Persistence

The following directories are mounted as volumes for data persistence:

- `./data`: Database files
- `./logs`: Log files
- `./uploads`: Uploaded files

#### Common Commands

```bash
# Stop services
docker-compose down

# Restart services
docker-compose restart

# View backend logs
docker-compose logs -f backend

# Enter backend container
docker-compose exec backend bash

# Enter frontend container
docker-compose exec frontend sh
```

For more details, please refer to the [Docker Deployment Documentation](../docker/README.md).

### Source Code Installation

#### Prerequisites

- **Python Environment**: Python 3.8 or higher
- **System Dependencies** (RHEL & CentOS):
  ```bash
    yum install -y epel-release
  yum install -y nmap sshpass python3 python3-pip python3-devel
      ```

#### Installation Steps

```bash
# Clone the repository
git clone https://github.com/Cloud-Discovery/prophet
cd prophet

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows

# Install dependencies
pip install -U pip
pip install -r requirements.txt
pip install .

# Install Windows WMI module (RHEL/CentOS only)
yum install -y ./tools/wmi-1.3.14-4.el7.art.x86_64.rpm

# Initialize database
python -c "from app import create_app; from db import init_db; app = create_app(); init_db(app)"

# Start web service
python app.py

# Start Celery Worker (in another terminal)
celery -A celery_worker.celery worker --loglevel=info
```

## Usage Guide

### Web Interface

#### 1. Login

First-time users need to register an account, then log in with username and password.

#### 2. Host Management

- **View host list**: View all collected hosts on the "Hosts" page
- **Search and filter**: Support searching by IP, hostname, OS type, etc.
- **View details**: Click on a host to view detailed information (CPU, memory, disk, network, etc.)
- **Add tags**: Add tags to hosts for easy classification

#### 3. Application Management

Application management provides a visual canvas for organizing dependencies between hosts in business scenarios.

**Create Application**:

1. Click the "Create Application" button
2. Enter application name and description
3. Enter the application detail page

**Visual Canvas Operations**:

1. **Resource Panel** (left side)
   - Search and add hosts not yet in the application
   - Use template nodes (network, storage, service, etc.) to supplement business architecture
2. **Canvas Operations** (center)
   - Drag nodes to move positions
   - Connect two nodes to create relationships
   - Use toolbar to adjust layout (grid, horizontal, vertical)
   - Zoom and view reset
3. **Property Panel** (right side)
   - Select nodes or connections to view/edit properties
   - Modify relationship types and descriptions
   - Rebind hosts

**Line Style Settings**:

- Click on a connection in the canvas, then click "Line Style" in the top toolbar
- Set line type (polyline, straight line, bezier curve)
- Set line style (solid, dashed, dotted)
- Set line width and color

#### 4. Scan Tasks

- **Create scan task**: Create network scan tasks on the "Scans" page
- **View task status**: View scan progress and results in real-time
- **Download scan results**: Download CSV format result files after scanning

#### 5. Data Import

- Batch import host data on the "Collections" page
- Support CSV and YAML formats

## Project Structure

For detailed project structure, please refer to [PROJECT_STRUCTURE.md](../PROJECT_STRUCTURE.md).

Main directories:

- `api/` - Flask API endpoints
- `frontend/` - Vue.js frontend application
- `models/` - Database models
- `prophet/` - Core library (collection, parsing, scanning, etc.)
- `services/` - Business logic services
- `tasks/` - Celery async tasks
- `docker/` - Docker deployment configuration

## Contributing

We welcome all forms of contributions! Please check [CONTRIBUTING.md](../CONTRIBUTING.md) for detailed contribution guidelines.

## Security Policy

If you discover a security vulnerability, please see [SECURITY.md](../SECURITY.md) for how to report it.

## License

This project is licensed under the [Mulan PubL v2](http://license.coscl.org.cn/MulanPubL-2.0)

## Contributors

Thanks to all contributors who have contributed to this project

<a href="https://github.com/Cloud-Discovery/prophet/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=Cloud-Discovery/prophet" />
</a>
