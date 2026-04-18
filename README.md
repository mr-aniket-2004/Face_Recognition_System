# 🚀 FaceTrack — Smart Attendance System

![Banner](https://capsule-render.vercel.app/api?type=waving\&color=0:0f2027,100:00c6ff\&height=220\&section=header\&text=FaceTrack%20Attendance%20System\&fontSize=32\&fontColor=ffffff\&animation=fadeIn)

![GitHub stars](https://img.shields.io/github/stars/mr-aniket-2004/Face_Recognition_System?style=for-the-badge)
![GitHub forks](https://img.shields.io/github/forks/mr-aniket-2004/Face_Recognition_System?style=for-the-badge)
![GitHub issues](https://img.shields.io/github/issues/mr-aniket-2004/Face_Recognition_System?style=for-the-badge)
![License](https://img.shields.io/github/license/mr-aniket-2004/Face_Recognition_System?style=for-the-badge)

![Python](https://img.shields.io/badge/Python-3.x-blue?style=for-the-badge\&logo=python)
![Django](https://img.shields.io/badge/Django-Framework-green?style=for-the-badge\&logo=django)
![OpenCV](https://img.shields.io/badge/OpenCV-Computer_Vision-red?style=for-the-badge\&logo=opencv)
![NumPy](https://img.shields.io/badge/NumPy-Numerical-blue?style=for-the-badge\&logo=numpy)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-DB-0a0a0a?style=for-the-badge&logo=postgresql&logoColor=white)
![TailwindCSS](https://img.shields.io/badge/TailwindCSS-UI-blue?style=for-the-badge\&logo=tailwindcss)

---

## 📌 Project Overview

**FaceTrack** is a smart, AI-powered attendance system built using **Django + OpenCV**.
It automates attendance tracking using **face recognition**, eliminating manual entry, proxy attendance, and human errors.

The system includes:

* 🔐 Secure OTP-based authentication
* 📷 Real-time face detection & recognition
* 📊 Admin analytics and reporting
* 👨‍💼 Employee self-service dashboard

---

## ✨ Core Features

### 👨‍💼 Admin Module

* Add & manage employees
* Capture face via webcam / upload image
* Automatic face encoding
* Live attendance monitoring
* Export reports (CSV / PDF)
* Filter attendance by date & department

### 👤 Employee Module

* Secure login with OTP
* Dashboard with attendance stats
* View attendance history
* Change / reset password
* Manual checkout (if needed)

### 🤖 Smart System Features

* Face Recognition using **LBPH**
* Face Detection using **Haar Cascade**
* Email-based OTP verification
* Real-time webcam processing
* Attendance auto-marking

---

## 🧰 Tech Stack

### 💻 Backend

* Python
* Django

### 🎨 Frontend

* HTML, CSS, JavaScript
* Tailwind CSS

### 🧠 AI / ML

* OpenCV
* NumPy
* Haar Cascade
* LBPH Algorithm

### 🗄️ Database

* Postgresql

### 🛠️ Tools

* VS Code
* Git & GitHub

---

## 🏗️ Project Architecture

```
User (Admin / Employee)
        ↓
Frontend (HTML, CSS, JS, Tailwind)
        ↓
Django Backend (Views + Logic)
        ↓
Database (SQLite)
        ↓
Face Recognition (OpenCV + LBPH)
        ↓
Email Service (SMTP)
```

---

## 🔄 System Flow

### 🔐 Authentication

```
Login → Validate → Generate OTP → Verify OTP → Dashboard
```

### 👨‍💼 Admin Flow

```
Login → Dashboard → Add Employee → Capture Face → Encode → Store → Monitor Attendance
```

### 👤 Employee Flow

```
Login → Dashboard → Face Scan → Attendance Marked → View Records → Checkout
```

---

## ⚙️ Setup Instructions

### 🔹 1. Clone Repository

```bash
git clone https://github.com/mr-aniket-2004/Face_Recognition_System.git
cd FRAS
```

### 🔹 2. Virtual Environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/macOS
source venv/bin/activate
```

### 🔹 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 🔹 4. Configure Environment

Create `.env` file:

```env
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
```

---

### 🔹 5. Migrate Database

```bash
python manage.py migrate
```

### 🔹 6. Create Admin

```bash
python manage.py create_admin
```

Default:

* Username: `admin`
* Password: `admin123`

---

### 🔹 7. Run Server

```bash
python manage.py runserver
```

Open:
👉 http://127.0.0.1:8000/

---

## 📁 Project Structure

```
FRAS/
├── attendance/
├── facetrack/
├── templates/
├── static/
├── media/
├── manage.py
├── requirements.txt
```

---

## 📬 Email Configuration

Update in `settings.py`:

```python
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
```

Use **App Password** for Gmail.

---

## 🎯 Useful Commands

```bash
python manage.py runserver
python manage.py migrate
python manage.py create_admin
python manage.py start_attendance
```

---

## ⚠️ Important Guidelines

### 🔒 Security

* Never commit `.env`
* Use strong passwords
* Set `DEBUG = False` in production
* Configure `ALLOWED_HOSTS`

### 📷 Face Recognition

* Use clear front-facing images
* Ensure good lighting
* Avoid multiple faces in capture

### ⚡ Performance

* LBPH works best for small datasets
* Avoid large-scale production use without optimization

---

## 🚀 Future Enhancements

* Deep Learning Models (FaceNet, CNN)
* PostgreSQL / Cloud DB
* Mobile App Integration
* Multi-camera support
* Real-time analytics dashboard

---

## 🤝 Contribution

Pull requests are welcome.
For major changes, open an issue first.

---

## 👨‍💻 Author

**Aniket Chandiwade**

---

## ⭐ Support

If you like this project, give it a ⭐ on GitHub!

---
