import cv2
import math
import datetime
import time 
import sqlite3
import os
import winsound
import threading
from flask import Flask, render_template, Response, jsonify
from ultralytics import YOLO

app = Flask(__name__)

# ==========================================
# SYSTEM SETUP & DATABASE
# ==========================================
os.makedirs('static/evidence', exist_ok=True)

def init_db():
    conn = sqlite3.connect('sentinel.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS alerts
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  timestamp TEXT,
                  threat_type TEXT,
                  confidence TEXT,
                  image_path TEXT)''')
    conn.commit()
    conn.close()

init_db()

def save_evidence(threat_type, confidence, frame):
    file_time = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    display_time = datetime.datetime.now().strftime("%H:%M:%S")
    filename = f"ev_{threat_type.replace(' ', '_')}_{file_time}.jpg"
    filepath = os.path.join('static', 'evidence', filename)
    
    # Save image
    cv2.imwrite(filepath, frame)
    
    # Save DB record
    conn = sqlite3.connect('sentinel.db')
    c = conn.cursor()
    c.execute("INSERT INTO alerts (timestamp, threat_type, confidence, image_path) VALUES (?, ?, ?, ?)",
              (display_time, threat_type, str(confidence), filename))
    
    # Delete old images to protect hard drive
    c.execute("SELECT image_path FROM alerts WHERE id NOT IN (SELECT id FROM alerts ORDER BY id DESC LIMIT 50)")
    old_records = c.fetchall()
    for record in old_records:
        old_file = os.path.join('static', 'evidence', record[0])
        if os.path.exists(old_file):
            os.remove(old_file) 
            
    c.execute("DELETE FROM alerts WHERE id NOT IN (SELECT id FROM alerts ORDER BY id DESC LIMIT 50)")
    conn.commit()
    conn.close()

# ==========================================
# HARDWARE ALARM SYSTEM
# ==========================================
def trigger_alarm():
    # Plays a high-pitched 2500Hz beep for 1000ms (1 second) directly from the laptop
    winsound.Beep(2500, 1000)

# ==========================================
# LOAD AI ENGINES
# ==========================================
print("Loading Stream A: Weapon Detection...")
weapon_model = YOLO(r"runs\detect\train\weights\best.pt")
classNames = weapon_model.names 

print("Loading Stream B: Pose Kinematics...")
pose_model = YOLO("yolov8n-pose.pt") 

alert_logs = []

def generate_frames():
    global alert_logs 
    cap = cv2.VideoCapture(0)
    
    pTime = time.time()
    prev_people = []
    last_violence_save = 0
    last_weapon_save = 0

    while True:
        success, frame = cap.read()
        if not success: break
            
        cTime = time.time()
        time_elapsed = cTime - pTime
        pTime = cTime

        # ==========================================
        # STREAM B: BODY-CENTRIC KINEMATICS
        # ==========================================
        pose_results = pose_model(frame, stream=True, verbose=False)
        current_people = []
        safe_time = max(time_elapsed, 0.033) 
        
        for r in pose_results:
            frame = r.plot(boxes=False) 
            if r.keypoints is not None and r.keypoints.xy.shape[1] > 0:
                for person_pts in r.keypoints.xy:
                    if len(person_pts) > 10: 
                        nx, ny = int(person_pts[0][0]), int(person_pts[0][1]) 
                        lx, ly = int(person_pts[9][0]), int(person_pts[9][1]) 
                        rx, ry = int(person_pts[10][0]), int(person_pts[10][1]) 
                        lsx, lsy = int(person_pts[5][0]), int(person_pts[5][1]) 
                        rsx, rsy = int(person_pts[6][0]), int(person_pts[6][1])
                        
                        if nx == 0 or lsx == 0 or rsx == 0: continue
                        
                        shoulder_width = math.hypot(lsx - rsx, lsy - rsy)
                        if shoulder_width < 60: shoulder_width = 150 
                        
                        current_people.append({
                            'nose': (nx, ny), 'lw': (lx, ly), 'rw': (rx, ry), 'sw': shoulder_width
                        })

        if len(prev_people) > 0:
            for curr in current_people:
                closest_person = None
                min_nose_dist = float('inf')
                
                for prev in prev_people:
                    n_dist = math.hypot(curr['nose'][0] - prev['nose'][0], curr['nose'][1] - prev['nose'][1])
                    if n_dist < min_nose_dist:
                        min_nose_dist = n_dist
                        closest_person = prev
                
                if closest_person and min_nose_dist < curr['sw']:
                    lw_c, lw_p = curr['lw'], closest_person['lw']
                    rw_c, rw_p = curr['rw'], closest_person['rw']
                    nose_c, nose_p = curr['nose'], closest_person['nose']

                    # FILTER 1: OUT OF FRAME (0,0)
                    lw_visible = (lw_c[0] > 0 and lw_c[1] > 0) and (lw_p[0] > 0 and lw_p[1] > 0)
                    rw_visible = (rw_c[0] > 0 and rw_c[1] > 0) and (rw_p[0] > 0 and rw_p[1] > 0)

                    lw_raw_dist = math.hypot(lw_c[0] - lw_p[0], lw_c[1] - lw_p[1]) if lw_visible else 0
                    rw_raw_dist = math.hypot(rw_c[0] - rw_p[0], rw_c[1] - rw_p[1]) if rw_visible else 0

                    # FILTER 2: THE TELEPORTATION GLITCH
                    if lw_raw_dist > (curr['sw'] * 1.5): lw_visible = False
                    if rw_raw_dist > (curr['sw'] * 1.5): rw_visible = False

                    # BODY-CENTRIC THRUST MATH
                    lw_ext_c = math.hypot(lw_c[0] - nose_c[0], lw_c[1] - nose_c[1]) if lw_visible else 0
                    rw_ext_c = math.hypot(rw_c[0] - nose_c[0], rw_c[1] - nose_c[1]) if rw_visible else 0
                    
                    lw_ext_p = math.hypot(lw_p[0] - nose_p[0], lw_p[1] - nose_p[1]) if lw_visible else 0
                    rw_ext_p = math.hypot(rw_p[0] - nose_p[0], rw_p[1] - nose_p[1]) if rw_visible else 0
                    
                    lw_thrust = lw_ext_c - lw_ext_p
                    rw_thrust = rw_ext_c - rw_ext_p
                    
                    # FILTER 4: Y-AXIS (No Waving)
                    lw_below_face = lw_c[1] > nose_c[1]
                    rw_below_face = rw_c[1] > nose_c[1]
                    
                    # THE ULTIMATE STRIKE RULE
                    valid_lw_strike = lw_visible and (lw_thrust > 30) and (lw_ext_c > (curr['sw'] * 0.8)) and lw_below_face
                    valid_rw_strike = rw_visible and (rw_thrust > 30) and (rw_ext_c > (curr['sw'] * 0.8)) and rw_below_face

                    if not valid_lw_strike and not valid_rw_strike:
                        continue 

                    lw_speed = (lw_thrust / curr['sw']) / safe_time if valid_lw_strike else 0
                    rw_speed = (rw_thrust / curr['sw']) / safe_time if valid_rw_strike else 0
                    max_speed = max(lw_speed, rw_speed)
                    
                    # STRICT THRESHOLD
                    if max_speed > 8.5: 
                        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
                        log_msg = {"type": "violence", "text": f"[{timestamp}] Aggressive Motion"}
                        
                        if len(alert_logs) == 0 or alert_logs[0].get("text") != log_msg["text"]:
                            alert_logs.insert(0, log_msg)
                            if len(alert_logs) > 5: alert_logs.pop()
                        
                        cv2.putText(frame, "THREAT: AGGRESSIVE MOTION", (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 3)
                        
                        # TRIGGER EVIDENCE AND ALARM
                        if cTime - last_violence_save > 3:
                            save_evidence("Violence", "High", frame)
                            last_violence_save = cTime
                            threading.Thread(target=trigger_alarm).start()
                        break

        prev_people = current_people

        # ==========================================
        # STREAM A: WEAPON DETECTION
        # ==========================================
        weapon_results = weapon_model(frame, stream=True, verbose=False)
        
        for r in weapon_results:
            for box in r.boxes:
                confidence = math.ceil((box.conf[0] * 100)) / 100
                
                if confidence > 0.70: 
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    cls_id = int(box.cls[0])
                    current_class = classNames[cls_id]

                    if current_class in ['handgun', 'knife']:
                        box_color = (0, 0, 255)
                        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
                        log_msg = {"type": "weapon", "text": f"[{timestamp}] {current_class.capitalize()} ({int(confidence*100)}%)"}
                        
                        if len(alert_logs) == 0 or alert_logs[0].get("text") != log_msg["text"]:
                            alert_logs.insert(0, log_msg) 
                            if len(alert_logs) > 5: alert_logs.pop()
                        
                        # TRIGGER EVIDENCE AND ALARM
                        if cTime - last_weapon_save > 3:
                            save_evidence(current_class.capitalize(), f"{int(confidence*100)}%", frame)
                            last_weapon_save = cTime
                            threading.Thread(target=trigger_alarm).start()
                    else:
                        box_color = (0, 255, 0)
                    
                    cv2.rectangle(frame, (x1, y1), (x2, y2), box_color, 3)
                    cv2.putText(frame, f"{current_class} {confidence}", (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, box_color, 2)

        ret, buffer = cv2.imencode('.jpg', frame)
        yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')


# ==========================================
# WEB ROUTES
# ==========================================
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/history')
def history():
    return render_template('history.html')

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/get_logs')
def get_logs():
    return jsonify(alert_logs)

@app.route('/api/history')
def api_history():
    conn = sqlite3.connect('sentinel.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM alerts ORDER BY id DESC")
    rows = c.fetchall()
    conn.close()
    return jsonify([dict(ix) for ix in rows])

@app.route('/system_status')
def system_status():
    return jsonify({"system_online": True, "yolo_active": True, "mediapipe_active": True})

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)