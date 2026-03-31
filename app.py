import cv2
import math
import datetime # NEW
from flask import Flask, render_template, Response, jsonify # NEW: jsonify
from ultralytics import YOLO

app = Flask(__name__)
model_path = r"runs\detect\train\weights\best.pt"
model = YOLO(model_path)
classNames = model.names 

alert_logs = []

def generate_frames():
    global alert_logs 
    cap = cv2.VideoCapture(0)
    
    while True:
        success, frame = cap.read()
        if not success:
            break
            
        results = model(frame, stream=True, verbose=False) 
        
        for r in results:
            boxes = r.boxes
            for box in boxes:
                confidence = math.ceil((box.conf[0] * 100)) / 100
                
                if confidence > 0.40: 
                    x1, y1, x2, y2 = box.xyxy[0]
                    x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
                    cls_id = int(box.cls[0])
                    current_class = classNames[cls_id]

                    # --- LOGGING LOGIC ---
                    if current_class in ['handgun', 'knife']:
                        box_color = (0, 0, 255)
                        
                        # Format the timestamp and message
                        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
                        log_msg = f"[{timestamp}] {current_class.capitalize()} Detected ({int(confidence*100)}%)"
                        
                        # Prevent the split-second log from spamming the list
                        if len(alert_logs) == 0 or alert_logs[0] != log_msg:
                            alert_logs.insert(0, log_msg) # Push to top of list
                            if len(alert_logs) > 5: # Keep only the 5 most recent logs
                                alert_logs.pop()
                    else:
                        box_color = (0, 255, 0)
                    # -------------------------
                    
                    cv2.rectangle(frame, (x1, y1), (x2, y2), box_color, 3)
                    cv2.putText(frame, f"{current_class} {confidence}", (x1, y1 - 10), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, box_color, 2)

        ret, buffer = cv2.imencode('.jpg', frame)
        frame_bytes = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/get_logs')
def get_logs():
    return jsonify(alert_logs)

@app.route('/system_status')
def system_status():
    return jsonify({
        "system_online": True,
        "yolo_active": True,
        "mediapipe_active": False 
    })
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)