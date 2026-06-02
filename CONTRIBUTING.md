# Contributing to Prophet

Thank you for your interest in contributing to Prophet! This document provides guidelines and instructions for contributing to the project.

## Code of Conduct

By participating in this project, you agree to abide by our Code of Conduct. Please be respectful and constructive in all interactions.

## How to Contribute

### Reporting Bugs

If you find a bug, please create an issue with the following information:

- **Description**: Clear description of the bug
- **Steps to Reproduce**: Detailed steps to reproduce the issue
- **Expected Behavior**: What you expected to happen
- **Actual Behavior**: What actually happened
- **Environment**: OS, Python version, Docker version (if applicable)
- **Screenshots**: If applicable, add screenshots

### Suggesting Features

We welcome feature suggestions! Please create an issue with:

- **Feature Description**: Clear description of the proposed feature
- **Use Case**: Why this feature would be useful
- **Possible Implementation**: If you have ideas on how to implement it

### Pull Requests

1. **Fork the repository** and create your branch from `main`:

   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes**:

   - Follow the existing code style
   - Add tests if applicable
   - Update documentation as needed

3. **Commit your changes**:

   ```bash
   git commit -m "Add: description of your changes"
   ```

   Use clear commit messages following conventional commits format:

   - `Add:` for new features
   - `Fix:` for bug fixes
   - `Update:` for updates to existing features
   - `Refactor:` for code refactoring
   - `Docs:` for documentation changes

4. **Push to your fork**:

   ```bash
   git push origin feature/your-feature-name
   ```

5. **Create a Pull Request**:
   - Provide a clear description of your changes
   - Reference any related issues
   - Ensure all CI checks pass

## Development Setup

### Prerequisites

- Python 3.8+
- Node.js 18+ (for frontend development)
- Docker and Docker Compose (for containerized development)
- Git

### Backend Development

1. Clone the repository:

   ```bash
   git clone https://github.com/Cloud-Discovery/prophet.git
   cd prophet
   ```

2. Create a virtual environment:

   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   pip install -e .
   ```

4. Set up environment variables:

   ```bash
   cp env.example .env
   # Edit .env with your configuration
   ```

5. Initialize the database:

   ```bash
   python -c "from app import create_app; from db import init_db; app = create_app(); init_db(app)"
   ```

6. Run the development server:
   ```bash
   python app.py
   ```

### Frontend Development

1. Navigate to the frontend directory:

   ```bash
   cd frontend
   ```

2. Install dependencies:

   ```bash
   npm install
   ```

3. Start the development server:
   ```bash
   npm run dev
   ```

### Docker Development

1. Build and start services:

   ```bash
   docker-compose up -d
   ```

2. View logs:
   ```bash
   docker-compose logs -f
   ```

## Code Style

### Python

- Follow PEP 8 style guide
- Use type hints where appropriate
- Write docstrings for functions and classes
- Maximum line length: 100 characters

### TypeScript/JavaScript

- Follow ESLint configuration
- Use TypeScript for type safety
- Follow Vue.js style guide

## Testing

- Write tests for new features
- Ensure all existing tests pass
- Add integration tests for API endpoints

## Documentation

- Update README.md if needed
- Add docstrings to new functions/classes
- Update CHANGELOG.md with your changes
- Keep documentation in both Chinese and English

## Questions?

If you have questions, please:

- Open an issue for discussion
- Check existing issues and pull requests
- Review the documentation

Thank you for contributing to Prophet!
