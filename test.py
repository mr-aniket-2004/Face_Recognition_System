from PIL import Image
import numpy as np
import face_recognition

image_path = r"C:\Users\anike\Downloads\profile2.jpeg"

# Load PIL image and force RGB
image = Image.open(image_path).convert("RGB")

# Convert to NumPy array with dtype uint8 and contiguous memory
image_np = np.array(image, dtype=np.uint8)
image_np = np.ascontiguousarray(image_np)

print("Image mode:", image.mode)
print("Array dtype:", image_np.dtype)
print("Array shape:", image_np.shape)

# Now encode
encodings = face_recognition.face_encodings(image_np)
print(encodings)