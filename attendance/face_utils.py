"""
Face recognition utility functions for FaceTrack.
Uses face_recognition and OpenCV libraries.
"""
import cv2
import numpy as np
import face_recognition
from PIL import Image
import io
import os
from django.conf import settings

def encode_face_from_image(image_input):
    """
    Safe encoding for face_recognition:
    Handles file path, FileField, bytes (from webcam), ensures contiguous RGB uint8 array
    """
    # print("this is image input ",image_input)
    try:
        # FileField or local path
        if hasattr(image_input, 'path'):
            image = Image.open(image_input).convert("RGB")
        # raw bytes (webcam)
        elif isinstance(image_input, bytes):
            image = Image.open(io.BytesIO(image_input)).convert("RGB")
        else:
            # fallback for path string or file-like
            image = Image.open(image_input).convert("RGB")

        # Convert to NumPy array and make contiguous

        # print(image)
        image = np.array(image, dtype=np.uint8)
        image = np.ascontiguousarray(image)

        encodings = face_recognition.face_encodings(image)
        if encodings is not None and len(encodings) > 0:
            # print(encodings[0])
            return encodings[0]
        return None

    except Exception as e:
        print("Encoding error:", e)
        return None
    

    


def encode_face_from_array(image_array):
    try:
        import face_recognition
        import numpy as np
        import cv2

        # Convert BGR → RGB
        rgb = cv2.cvtColor(image_array, cv2.COLOR_BGR2RGB)

        #  HARD FIX
        rgb = np.ascontiguousarray(rgb, dtype=np.uint8)

        encodings = face_recognition.face_encodings(rgb)

        return encodings[0] if encodings else None

    except Exception as e:
        print(f"Error encoding face from array: {e}")
        return None
    



def recognize_faces_in_frame(frame, known_encodings, tolerance=0.6):
    """
    Detect and recognize faces in a video frame.
    Returns list of (name, employee_id, location) tuples.
    """
    small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
    rgb_small = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
    
    face_locations = face_recognition.face_locations(rgb_small)
    face_encs = face_recognition.face_encodings(rgb_small, face_locations)
    
    results = []
    
    for face_enc, face_loc in zip(face_encs, face_locations):
        best_match_id = None
        best_match_name = "Unknown"
        best_distance = tolerance
        best_employee = None
        
        for emp_id, (stored_enc, name, emp_obj) in known_encodings.items():
            distance = face_recognition.face_distance([stored_enc], face_enc)[0]
            if distance < best_distance:
                best_distance = distance
                best_match_id = emp_id
                best_match_name = name
                best_employee = emp_obj
        
        # Scale face location back to original size
        top, right, bottom, left = [v * 4 for v in face_loc]
        
        results.append({
            'name': best_match_name,
            'employee_id': best_match_id,
            'employee': best_employee,
            'location': (top, right, bottom, left),
            'distance': best_distance,
            'is_known': best_match_id is not None,
        })
    
    return results


def get_all_employee_encodings():
    from .models import Employee
    import numpy as np
    import json

    employees = Employee.objects.all()
    known_encodings = {}

    for emp in employees:
        if emp.face_encoding:
            try:
                encoding = np.array(json.loads(emp.face_encoding))
                known_encodings[emp.employee_id] = (
                    encoding,
                    emp.user.first_name,
                    emp
                )
            except Exception as e:
                print(f"Error loading encoding for {emp.user.first_name}: {e}")

    return known_encodings



def run_face_recognition_camera():
    """
    Run the OpenCV webcam face recognition loop.
    This is called when admin clicks "Start Attendance".
    Opens a window with live face detection.
    Press 'q' to quit.
    """
    from .models import Attendance
    from django.utils import timezone
    
    known = get_all_employee_encodings()
    if not known:
        print("No employee encodings found! Please add employees with photos first.")
        return
    
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error: Cannot open webcam")
        return
    
    marked_today = set()
    today = timezone.localdate()
    
    # Load already marked attendance for today
    existing = Attendance.objects.filter(date=today).values_list('employee__employee_id', flat=True)
    marked_today.update(existing)
    
    print(f"FaceTrack started. {len(known)} employees loaded. Press 'q' to quit.")
    
    process_frame = True
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        if process_frame:
            results = recognize_faces_in_frame(frame, known)
            
            for r in results:
                top, right, bottom, left = r['location']
                
                if r['is_known']:
                    color = (0, 255, 0)  # Green for known
                    label = f"{r['name']} ({r['employee_id']})"
                    
                    # Mark attendance if not already marked today
                    if r['employee_id'] not in marked_today:
                        now = timezone.localtime()
                        Attendance.objects.create(
                            employee=r['employee'],
                            date=today,
                            check_in_time=now.time(),
                            status='present' if now.hour < 10 else 'late',
                            marked_by='face_recognition'
                        )
                        marked_today.add(r['employee_id'])
                        label += " ✓ MARKED"
                        print(f"✓ Attendance marked for {r['name']} at {now.strftime('%H:%M:%S')}")
                else:
                    color = (0, 0, 255)  # Red for unknown
                    label = "Unknown"
                
                # Draw rectangle and label
                cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
                cv2.rectangle(frame, (left, bottom - 30), (right, bottom), color, cv2.FILLED)
                cv2.putText(frame, label, (left + 6, bottom - 8),
                           cv2.FONT_HERSHEY_DUPLEX, 0.5, (255, 255, 255), 1)
        
        process_frame = not process_frame  # Process every other frame for performance
        
        # Show status bar
        cv2.putText(frame, f"FaceTrack | Employees: {len(known)} | Marked today: {len(marked_today)}",
                   (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 212, 255), 1)
        cv2.putText(frame, "Press 'q' to quit", (10, frame.shape[0] - 15),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (128, 128, 128), 1)
        
        cv2.imshow('FaceTrack - Smart Attendance System', frame)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    cap.release()
    cv2.destroyAllWindows()
    print("FaceTrack stopped.")
