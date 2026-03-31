import cv2
import math
import winsound 
from ultralytics import YOLO

print("Model Loading.......")
# Load your newly trained custom brain
model_path = r"runs\detect\train\weights\best.pt"
model = YOLO(model_path)

print("Model loaded succefully..")
# Extract the dynamic dictionary of classes directly from the model
classNames = model.names 

# Opening camera
cap = cv2.VideoCapture(0)

print("Sentinel AI Active. Beep enabled for Handgun and Knife detection.")

while True:
    ret, frame = cap.read()
    if not ret:
        break
        
    results = model(frame, stream=True)

    # Track if a threat is found in THIS specific frame
    threat_detected = False
    for r in results:
        boxes = r.boxes
        for box in boxes:
            confidence = math.ceil((box.conf[0] * 100)) / 100
            
            # Use a slightly lower threshold to catch the weapon faster
            if confidence > 0.40:
                x1, y1, x2, y2 = box.xyxy[0]
                x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
                
                cls_id = int(box.cls[0])
                current_class = classNames[cls_id]

                # Logical Filter for Threats
                if current_class in ['handgun', 'knife', 'hammer']:
                    box_color = (0, 0, 255) # Red
                    threat_detected = True
                else:
                    box_color = (0, 255, 0) # Green
                
                # Drawing boxes
                cv2.rectangle(frame, (x1, y1), (x2, y2), box_color, 3)
                label_text = f"{current_class} {confidence}"
                cv2.putText(frame, label_text, (x1, y1 - 10), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, box_color, 2)

    # Beep sound when threat detect
    if threat_detected:
        winsound.Beep(1000, 200)

    # Render
    cv2.imshow("Sentinel AI - Real Time Alert System", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
