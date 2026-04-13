# FaceTrack — Smart Attendance System

FaceTrack is a Django-based attendance management application with face recognition support.
It allows admins to add employees, mark attendance via webcam or live monitoring, and export reports in CSV/PDF.

---

## 🚀 Setup Instructions

### 1. Prerequisites
- Python 3.10+ (recommended)
- pip
- Webcam (for face recognition capture and live monitoring)

### 2. Clone the Project
```bash
git clone <your-repo-url>
cd FRAS
```

### 3. Create and Activate Virtual Environment
```bash
python -m venv venv

# Windows:
venv\Scripts\activate

# Linux / macOS:
source venv/bin/activate
```

### 4. Install Dependencies
```bash
pip install -r requirements.txt
```

### 5. Configure Environment Variables
Create a `.env` file in the project root with the following values:
```env
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-email-app-password
```

> Note: Do not commit `.env` to version control.

### 6. Run Migrations
```bash
python manage.py migrate
```

### 7. Create Admin User
```bash
python manage.py create_admin
```
This creates a default admin account:
- **Username:** `admin`
- **Password:** `admin123`

### 8. Run the Server
```bash
python manage.py runserver
```
Open your browser at: `http://127.0.0.1:8000`

---

## 📁 Project Structure
```
FRAS/
├── manage.py
├── requirements.txt
├── README.md
├── .gitignore
├── .env                  # local environment variables (not committed)
├── db.sqlite3            # local database (ignored in git)
├── attendance/
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── decorators.py
│   ├── face_utils.py
│   ├── forms.py
│   ├── management/
│   │   ├── __init__.py
│   │   └── commands/
│   │       ├── create_admin.py
│   │       └── start_attendance.py
│   ├── migrations/
│   ├── models.py
│   ├── templates/
│   ├── templatetags/
│   ├── urls.py
│   └── views.py
├── facetrack/
│   ├── __init__.py
│   ├── asgi.py
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── templates/
│   └── attendance/
├── static/
│   ├── css/
│   ├── images/
│   └── js/
└── media/
    └── employee_photos/
```

---

## 🔧 Features

### Admin
- Login at `/login/` using admin role
- Add employees with:
  - profile info
  - employee ID
  - department
  - phone number
  - photo upload or webcam capture
- Automatic face encoding from employee photo
- View employees list
- Export employee details in CSV and PDF
- View attendance records with date/department filters
- Export attendance reports in CSV and PDF
- Start face recognition using server webcam
- Live monitor page for browser-based attendance

### Employee
- Login at `/login/` using employee role
- View employee dashboard
- View profile and attendance history
- Change password
- Forgot password via email with temporary password reset

---

## 🔑 Default Credentials
| Role  | Username | Password  |
|-------|----------|-----------|
| Admin | admin    | admin123  |

> Make sure to update the admin password before deployment.

---

## 📬 Email Setup
The project uses Gmail SMTP settings in `facetrack/settings.py`:
- `EMAIL_HOST = 'smtp.gmail.com'`
- `EMAIL_PORT = 587`
- `EMAIL_USE_TLS = True`
- `EMAIL_HOST_USER` and `EMAIL_HOST_PASSWORD` from `.env`

If using Gmail, create an app password and enable SMTP access.

---

## 🎯 Useful Commands
```bash
python manage.py runserver
python manage.py migrate
python manage.py create_admin
python manage.py start_attendance
```

---

## ⚠️ Important Notes
- Do not commit secrets or local files:
  - `.env`
  - `db.sqlite3`
  - `media/`
  - `venv/`
  - `__pycache__/`
- Set `DEBUG = False` in production
- Configure `ALLOWED_HOSTS` before deploying
- Use HTTPS in production

---

## ✅ Recommended Git Ignore
The repo already includes a `.gitignore` to ignore:
- Python caches and compiled files
- virtual environment folders
- database files and logs
- local environment variables
- media uploads
- IDE/editor settings
- OS temporary files
