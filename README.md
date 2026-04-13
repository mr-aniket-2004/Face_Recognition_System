# FaceTrack — Smart Attendance System

A Django-based automatic attendance system using face recognition.
Employees are detected via webcam and attendance is marked automatically.

---

## 🚀 Setup Instructions

### 1. Prerequisites
- Python 3.10 is good and used for this project -- recommended
- pip (Python package manager)
- Webcam (for face recognition)

### 2. Create Virtual Environment
```bash
cd facetrack_project
python -m venv venv

# Windows:
venv\Scripts\activate

# Mac/Linux:
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

> **Note on dlib/face_recognition:**
> - **Windows**: You may need to install Visual Studio Build Tools and CMake first:
>   ```
>   pip install cmake
>   pip install dlib
>   pip install face-recognition
>   ```
> - **Mac**: `brew install cmake` then `pip install face-recognition`
> - **Linux**: `sudo apt-get install cmake libboost-all-dev` then `pip install face-recognition`

### 4. Run Migrations
```bash
python manage.py makemigrations attendance
python manage.py migrate
```

### 5. Create Admin User
```bash
python manage.py create_admin
```
This creates: **Username:** `admin` | **Password:** `admin123`

### 6. Run the Server
```bash
python manage.py runserver
```
Open: **http://127.0.0.1:8000**

---

## 📖 Usage

### Admin Workflow
1. Login as admin at `/login/`
2. Add employees with photos at `/add-employee/`
   - Upload a photo OR capture via webcam
   - Face encoding is auto-generated
3. Start face recognition:
   - **Option A**: Click "Start Camera" on dashboard → opens OpenCV window on server
   - **Option B**: Use "Live Monitor" page → browser-based webcam processing
4. View attendance records at `/attendance-records/`

### Employee Workflow
1. Login at `/login/` (select "Employee" role)
2. View attendance dashboard, profile, and history
3. Change password

### Face Recognition via Terminal
```bash
python manage.py start_attendance
```
This opens an OpenCV window. Press 'q' to quit.

---

## 📁 Project Structure
```
facetrack_project/
├── manage.py
├── requirements.txt
├── facetrack/
│   ├── settings.py
│   ├── urls.py
│   └── attendance/
│       ├── models.py          # Employee, Attendance, UserRole
│       ├── views.py           # All views
│       ├── urls.py            # URL routing
│       ├── forms.py           # Django forms
│       ├── face_utils.py      # Face recognition logic
│       ├── decorators.py      # Access control
│       ├── admin.py           # Django admin config
│       └── management/commands/
│           ├── create_admin.py
│           └── start_attendance.py
├── templates/attendance/       # All HTML templates
├── static/                     # CSS, JS, images
└── media/employee_photos/      # Employee photos
```

---

## 🔐 Default Credentials
| Role     | Username | Password  |
|----------|----------|-----------|
| Admin    | admin    | admin123  |

**⚠️ Change the admin password in production!**

---

## 🛡️ Security Notes
- Change `SECRET_KEY` in `settings.py` for production
- Set `DEBUG = False` in production
- Configure `ALLOWED_HOSTS` properly
- Use HTTPS in production
