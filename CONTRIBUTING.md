# Contributing to DARG

Thank you for being part of the DARG development team. This guide will help you contribute effectively to this private repository.

## Development Setup

1. **Clone the repository** (access will be granted to your GitHub account)
   ```bash
   git clone https://github.com/COMPANY_NAME/darg.git
   cd darg
   ```

2. **Set up environment variables**
   Copy `.env.example` to `.env` and fill in the required values (contact your team lead for access to credentials):
   ```bash
   cp .env.example .env
   # Fill in credentials provided by your team lead
   ```

3. **Install dependencies**
   ```bash
   pip install -r github_requirements.txt
   ```

4. **Run the application**
   ```bash
   streamlit run app.py
   ```

## Development Guidelines

### Code Style
- Follow PEP 8 style guidelines for Python code
- Use descriptive variable and function names
- Include docstrings for all functions and classes

### Branch Naming
- Use feature/short-description for feature branches
- Use fix/short-description for bug fix branches

### Commit Messages
- Use clear, descriptive commit messages
- Reference task IDs when applicable

### Pull Requests
- Create a pull request against the main branch
- Include a clear description of the changes
- Request review from at least one team member

## Component Structure

The application is organized into several key directories:

- `components/`: Reusable UI components
- `pages/`: Application pages (Streamlit multipage app)
- `utils/`: Utility functions and helpers

## Data Access Pattern

All data access should go through the data_access.py module, which provides a consistent interface to the Supabase backend with appropriate error handling and fallbacks.

## Questions?

If you have any questions or need help, please reach out to the team lead or through the designated communication channels.
