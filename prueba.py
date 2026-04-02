import cv2

for i in range(0, 6):
    cap = cv2.VideoCapture(i)
    if cap.isOpened():
        print(f"✅ Cámara encontrada en índice {i}")
        cap.release()
    else:
        print(f"❌ No cámara en índice {i}")
