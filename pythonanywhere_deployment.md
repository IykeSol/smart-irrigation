# PythonAnywhere Deployment Guide

Deploying this Smart Irrigation backend on PythonAnywhere is straightforward because it is built with Flask, which PythonAnywhere supports natively.

## Prerequisites
1. Ensure your code is hosted on GitHub (or you can zip and upload it directly).
2. Create a free account on [PythonAnywhere](https://www.pythonanywhere.com/).

## Steps to Deploy

### 1. Upload Your Code
- Go to the **Consoles** tab and open a **Bash** console.
- Clone your repository:
  ```bash
  git clone https://github.com/yourusername/a-smart-irrigation.git
  ```
  *(Or use the **Files** tab to upload the project folder directly).*

### 2. Set Up Virtual Environment & Install Dependencies
In the Bash console, run:
```bash
cd a-smart-irrigation
mkvirtualenv --python=/usr/bin/python3.10 irrigation-venv
pip install -r requirements.txt
```
*Note: Make sure `scikit-learn` and `joblib` install properly. The ML model requires them.*

### 3. Configure the Web App
1. Go to the **Web** tab.
2. Click **Add a new web app**.
3. Choose **Manual configuration** (do NOT choose Flask auto-setup, manual is better for existing projects).
4. Select Python 3.10 (or whatever matches your venv).

### 4. Setup Virtual Environment Path
- Scroll down to the **Virtualenv** section on the Web tab.
- Enter the path to your venv: `/home/yourusername/.virtualenvs/irrigation-venv`

### 5. Configure the WSGI File
- Scroll down to the **Code** section.
- Click on the WSGI configuration file link (e.g., `/var/www/yourusername_pythonanywhere_com_wsgi.py`).
- Replace the entire contents of that file with the following:

```python
import sys
import os

# Add your project directory to the sys.path
path = '/home/yourusername/a-smart-irrigation'
if path not in sys.path:
    sys.path.append(path)

# Add the backend directory if necessary
backend_path = '/home/yourusername/a-smart-irrigation/backend'
if backend_path not in sys.path:
    sys.path.append(backend_path)

# Set the working directory to the backend folder so relative paths work
os.chdir(backend_path)

# Import the Flask app
from app import app as application
```
*(Make sure to replace `yourusername` with your actual PythonAnywhere username).*

### 6. Reload and Test
- Go back to the **Web** tab and click the big green **Reload yourusername.pythonanywhere.com** button.
- Visit your site URL. The backend API (`/api/predict`) and the frontend should now be live!
