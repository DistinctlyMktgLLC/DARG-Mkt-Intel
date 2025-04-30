# Developer Environment Setup Guide

This document provides step-by-step instructions for setting up your development environment for the DARG project.

## Prerequisites

- Python 3.11+
- Git
- Access to company GitHub repository
- Access to company Supabase instance

## Initial Setup

1. **Clone the Repository**

   ```bash
   git clone https://github.com/COMPANY_NAME/darg.git
   cd darg
   ```

2. **Set Up Python Environment**

   It's recommended to use a virtual environment:

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies**

   ```bash
   pip install -r github_requirements.txt
   ```

4. **Set Up Environment Variables**

   Create a `.env` file in the project root (copy from `.env.example`):

   ```bash
   cp .env.example .env
   ```

   Then edit the `.env` file with the credentials provided by your team lead:

   ```
   SUPABASE_URL=your_provided_url
   SUPABASE_KEY=your_provided_key
   ENVIRONMENT=development
   ```

## Running the Application

1. **Start the Streamlit Server**

   ```bash
   streamlit run app.py
   ```

2. **Access the Application**

   Open your browser and navigate to: http://localhost:8501

## Development Workflow

1. **Create a Feature Branch**

   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make Changes and Test**

   During development, the application will use:
   - Real data from Supabase when connected
   - Sample data when connection issues occur (enabling local development)

3. **Commit Changes**

   ```bash
   git add .
   git commit -m "Description of your changes"
   ```

4. **Push Changes and Create Pull Request**

   ```bash
   git push origin feature/your-feature-name
   ```

   Then create a pull request through the GitHub interface.

## Troubleshooting

- **Supabase Connection Issues**
  - Ensure your VPN is connected (if required)
  - Verify your SUPABASE_URL and SUPABASE_KEY in the .env file
  - Check the connection_status page in the application

- **Missing Dependencies**
  - Try running `pip install -r github_requirements.txt` again
  - Contact the team lead if specific package versions are causing conflicts

- **Map Rendering Issues**
  - Ensure folium and streamlit-folium are properly installed
  - Check browser console for any JavaScript errors
