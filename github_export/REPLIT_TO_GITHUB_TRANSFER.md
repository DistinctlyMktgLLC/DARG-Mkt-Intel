# Transferring from Replit to GitHub

This guide provides instructions for transferring this project from Replit to your private GitHub repository.

## Prerequisites

- GitHub account with access to your organization's repositories
- Git installed on your local machine
- Admin access to the target GitHub repository

## Step 1: Export Code from Replit

There are several methods to export the code from Replit:

### Option A: Download as ZIP (Simplest)

1. In Replit, click on the three dots menu in the Files panel
2. Select "Download as ZIP"
3. Save the ZIP file to your local machine
4. Extract the ZIP file to a local folder

### Option B: Using Git (More Advanced)

1. Open the Shell in Replit
2. Initialize a git repository (if not already done):
   ```bash
   git init
   ```
3. Add all files to git:
   ```bash
   git add .
   ```
4. Commit the files:
   ```bash
   git commit -m "Initial commit for GitHub transfer"
   ```
5. Add your GitHub repository as a remote:
   ```bash
   git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
   ```
6. Push to GitHub:
   ```bash
   git push -u origin main
   ```

## Step 2: Set Up GitHub Repository

1. Create a new private repository on GitHub (if not already created)
2. Clone the repository to your local machine (if using Option A from above):
   ```bash
   git clone https://github.com/YOUR_USERNAME/YOUR_REPO.git
   ```
3. Copy all files from the extracted Replit ZIP to this folder

## Step 3: Push Code to GitHub

If using Option A (ZIP download):

1. Navigate to the local repository folder
2. Stage all files:
   ```bash
   git add .
   ```
3. Commit the files:
   ```bash
   git commit -m "Initial commit for DARG project"
   ```
4. Push to GitHub:
   ```bash
   git push origin main
   ```

## Step 4: Set Up GitHub Secrets

For the GitHub Actions workflow:

1. Go to your repository on GitHub
2. Navigate to Settings > Secrets and variables > Actions
3. Add the following repository secrets:
   - `SUPABASE_URL`: Your Supabase URL
   - `SUPABASE_KEY`: Your Supabase key

## Step 5: Verify GitHub Actions

1. Go to the Actions tab in your GitHub repository
2. Verify that the workflow runs successfully

## Step 6: Share with Team Members

1. Add team members as collaborators in the repository settings
2. Share the setup_developer_environment.md file with them

## Troubleshooting

- If you encounter permission issues, ensure you have admin access to the repository
- If GitHub Actions fail, check the workflow logs for specific errors
- For any Supabase connection issues, verify your environment variables and secrets
