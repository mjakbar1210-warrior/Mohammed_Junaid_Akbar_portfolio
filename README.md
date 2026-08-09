# Mohammed Junaid Akbar — Robotics Portfolio V3

This version is a full-stack Flask portfolio with an owner-only project dashboard.

## Features
- Public robotics portfolio
- Private admin login
- Add projects from the website
- Edit projects from the website
- Delete projects from the website
- Upload project images
- SQLite database
- GitHub and LinkedIn links
- Responsive robotics-style UI

## Run locally

### 1. Create a virtual environment
Windows:
```bash
python -m venv venv
venv\Scripts\activate
```

Linux/macOS:
```bash
python3 -m venv venv
source venv/bin/activate
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Start
```bash
python app.py
```

Open:
http://127.0.0.1:5000

Admin:
http://127.0.0.1:5000/login

## Important security notes
- Never commit your real password or SECRET_KEY.
- Use environment variables in production.
- Use HTTPS when deployed.
- Do not share your admin credentials.
- The public site has no project-edit controls.
- The server checks the session before every admin operation.

## Deployment
This is a dynamic Flask application, so GitHub Pages alone is NOT suitable for the V3 backend. Deploy the Flask app on a platform that supports Python web apps and persistent storage. For production, use a managed database/object storage if the host's local filesystem is ephemeral.


## V2-style enhancements
Added About, Skills, Services, Engineering Journey, Contact, richer visual cards, responsive layout and robotics-style UI while retaining the private admin project management system.
